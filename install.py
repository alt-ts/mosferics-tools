#!/usr/bin/env python3
"""
Mosferics Tools — Installer
============================
Run this once to install the Mosferics Price List Generator.
After installation, a desktop shortcut will be created.
The app will keep itself up to date automatically.

Usage:
  Windows: Double-click install.py (or right-click → Open with Python)
  Mac:     Double-click install.py, or: python3 install.py
"""

import sys
import os
import subprocess
import platform
import urllib.request
import urllib.error
import tempfile
import shutil
from pathlib import Path

# ── Configuration — update these to match your GitHub details ─────────────
GITHUB_RAW_URL = "https://raw.githubusercontent.com/alt-ts/mosferics-tools/main/generate_price_list.py"
APP_NAME       = "Mosferics Price List Generator"
SCRIPT_NAME    = "generate_price_list.py"

# Install location — a folder in the user's home directory
INSTALL_DIR    = Path.home() / "MosfericsTools"
 
REQUIRED_PACKAGES = ["reportlab", "openpyxl", "Pillow", "pypdf", "numpy"]
 
_venv_python = None  # set if we fall back to a venv
IS_WINDOWS = platform.system() == "Windows"
IS_MAC     = platform.system() == "Darwin"
 
# ── Helpers ────────────────────────────────────────────────────────────────
def log(msg):
    print(f"  {msg}")
 
def run(cmd, check=True, capture=False):
    kwargs = dict(check=check)
    if capture:
        kwargs['capture_output'] = True
        kwargs['text'] = True
    return subprocess.run(cmd, **kwargs)
 
def python_ok():
    """Check Python version is 3.8+"""
    return sys.version_info >= (3, 8)
 
def pip_install(packages):
    log(f"Installing: {', '.join(packages)}")
    # Try standard install first, then --user as fallback
    try:
        run([sys.executable, "-m", "pip", "install", "--upgrade", "--quiet"] + packages)
        return
    except subprocess.CalledProcessError:
        pass
    try:
        log("Retrying with --user flag...")
        run([sys.executable, "-m", "pip", "install", "--upgrade", "--quiet", "--user"] + packages)
        return
    except subprocess.CalledProcessError:
        pass
    # Final fallback: use a virtual environment inside the install dir
    log("Setting up virtual environment...")
    venv_dir = INSTALL_DIR / ".venv"
    run([sys.executable, "-m", "venv", str(venv_dir)])
    if IS_WINDOWS:
        venv_python = venv_dir / "Scripts" / "python.exe"
    else:
        venv_python = venv_dir / "bin" / "python3"
    run([str(venv_python), "-m", "pip", "install", "--upgrade", "--quiet"] + packages)
    # Update sys.executable so the shortcut uses the venv python
    global _venv_python
    _venv_python = str(venv_python)
 
def download_script(url, dest):
    log(f"Downloading latest script from GitHub...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'MosfericsInstaller/1.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode('utf-8')
        dest.write_text(content, encoding='utf-8')
        log(f"Downloaded to {dest}")
        return True
    except urllib.error.URLError as e:
        log(f"Warning: Could not download from GitHub ({e})")
        log("You can update manually later by re-running the installer.")
        return False
 
def create_windows_shortcut(script_path):
    """Create a .bat launcher + a desktop shortcut on Windows."""
    # Create a .bat launcher in the install dir
    launcher = INSTALL_DIR / f"{APP_NAME}.bat"
    python_exe = globals().get('_venv_python', sys.executable)
    launcher.write_text(
        f'@echo off\n'
        f'"{python_exe}" "{script_path}"\n',
        encoding='utf-8'
    )
 
    # Try to create a proper .lnk shortcut on the desktop using PowerShell
    desktop = Path.home() / "Desktop"
    shortcut_path = desktop / f"{APP_NAME}.lnk"
    ps_cmd = (
        f'$ws = New-Object -ComObject WScript.Shell; '
        f'$sc = $ws.CreateShortcut("{shortcut_path}"); '
        f'$sc.TargetPath = "{sys.executable}"; '
        f'$sc.Arguments = \'"{script_path}"\'; '
        f'$sc.WorkingDirectory = "{INSTALL_DIR}"; '
        f'$sc.Description = "{APP_NAME}"; '
        f'$sc.Save()'
    )
    try:
        run(["powershell", "-Command", ps_cmd])
        log(f"Desktop shortcut created: {shortcut_path}")
    except Exception:
        # Fallback: put the .bat on the desktop instead
        bat_desktop = desktop / f"{APP_NAME}.bat"
        shutil.copy(launcher, bat_desktop)
        log(f"Desktop launcher created: {bat_desktop}")
 
def create_mac_app(script_path):
    """Create a .app bundle on Mac that double-clicks like a native app."""
    desktop  = Path.home() / "Desktop"
    app_path = desktop / f"{APP_NAME}.app"
 
    # Remove existing app if present so we get a clean install
    if app_path.exists():
        shutil.rmtree(app_path)
 
    # App bundle structure
    contents  = app_path / "Contents"
    macos_dir = contents / "MacOS"
    macos_dir.mkdir(parents=True, exist_ok=True)
 
    # Info.plist
    (contents / "Info.plist").write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>{APP_NAME}</string>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundleIdentifier</key>
    <string>com.mosferics.pricelistgenerator</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
""", encoding='utf-8')
 
    # Launcher shell script inside the bundle
    launcher = macos_dir / "launcher"
    # Use the actual Python that ran the installer — guaranteed to work
    # since it just successfully ran this code
    python_exe = globals().get('_venv_python') or sys.executable
 
    # Verify it's a real path before writing it
    if not Path(python_exe).exists():
        # Search common Mac locations as fallback
        for candidate in [
            '/usr/local/bin/python3',
            '/opt/homebrew/bin/python3',
            '/usr/bin/python3',
        ]:
            if Path(candidate).exists():
                python_exe = candidate
                break
 
    launcher.write_text(
        f'''#!/bin/bash
exec "{python_exe}" "{script_path}"
''', encoding='utf-8'
    )
    launcher.chmod(0o755)
 
    # Remove quarantine flag so Gatekeeper doesn't block it
    try:
        subprocess.run(['xattr', '-rd', 'com.apple.quarantine', str(app_path)],
                      capture_output=True)
    except Exception:
        pass
    log(f"Mac app created: {app_path}")
 
def create_update_script():
    """Create a small update helper the user can run to force an update."""
    updater = INSTALL_DIR / "update.py"
    updater.write_text(
        f'#!/usr/bin/env python3\n'
        f'"""Run this to force-check for updates."""\n'
        f'import urllib.request, sys\n'
        f'from pathlib import Path\n'
        f'url = "{GITHUB_RAW_URL}"\n'
        f'dest = Path("{INSTALL_DIR / SCRIPT_NAME}")\n'
        f'print("Checking for updates...")\n'
        f'try:\n'
        f'    req = urllib.request.Request(url, headers={{"User-Agent": "MosfericsUpdater"}})\n'
        f'    with urllib.request.urlopen(req, timeout=15) as r:\n'
        f'        content = r.read().decode("utf-8")\n'
        f'    dest.write_text(content, encoding="utf-8")\n'
        f'    print("Updated successfully. Relaunch the app.")\n'
        f'except Exception as e:\n'
        f'    print(f"Update failed: {{e}}")\n',
        encoding='utf-8'
    )
    log(f"Update helper created: {updater}")
 
# ── Main installer ─────────────────────────────────────────────────────────
def main():
    print()
    print("=" * 55)
    print(f"  {APP_NAME}")
    print("  Installer")
    print("=" * 55)
    print()
 
    # Step 1: Check Python
    print("[ 1/5 ] Checking Python...")
    if not python_ok():
        print(f"\n  ERROR: Python 3.8 or higher is required.")
        print(f"  You have: Python {sys.version}")
        if IS_WINDOWS:
            print("\n  Please download Python from https://python.org/downloads")
            print("  Make sure to tick 'Add Python to PATH' during installation.")
        elif IS_MAC:
            print("\n  Please install Python from https://python.org/downloads")
        input("\n  Press Enter to exit...")
        sys.exit(1)
    log(f"Python {sys.version.split()[0]} — OK")
 
    # Step 2: Create install directory
    print("\n[ 2/5 ] Setting up install folder...")
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    log(f"Install folder: {INSTALL_DIR}")
 
    # Step 3: Install dependencies
    print("\n[ 3/5 ] Installing dependencies...")
    log("This may take a minute on first run...")
    try:
        pip_install(REQUIRED_PACKAGES)
        log("All dependencies installed.")
    except subprocess.CalledProcessError as e:
        print(f"\n  ERROR: Failed to install dependencies: {e}")
        input("\n  Press Enter to exit...")
        sys.exit(1)
 
    # Step 4: Download the app script
    print("\n[ 4/5 ] Downloading app...")
    script_path = INSTALL_DIR / SCRIPT_NAME
    downloaded  = download_script(GITHUB_RAW_URL, script_path)
 
    if not downloaded:
        # If download failed, check if we have a local copy to use
        local = Path(__file__).parent / SCRIPT_NAME
        if local.exists():
            shutil.copy(local, script_path)
            log(f"Copied local script to {script_path}")
        else:
            print(f"\n  ERROR: Could not download script and no local copy found.")
            print(f"  Please check your internet connection and try again.")
            input("\n  Press Enter to exit...")
            sys.exit(1)
 
    # Step 5: Create shortcut
    print("\n[ 5/5 ] Creating desktop shortcut...")
    try:
        if IS_WINDOWS:
            create_windows_shortcut(script_path)
        elif IS_MAC:
            create_mac_app(script_path)
        else:
            # Linux fallback — create a .desktop file
            desktop    = Path.home() / "Desktop"
            shortcut   = desktop / f"{APP_NAME}.desktop"
            shortcut.write_text(
                f'[Desktop Entry]\n'
                f'Type=Application\n'
                f'Name={APP_NAME}\n'
                f'Exec={sys.executable} "{script_path}"\n'
                f'Terminal=false\n'
            )
            shortcut.chmod(0o755)
            log(f"Desktop shortcut created: {shortcut}")
    except Exception as e:
        log(f"Warning: Could not create desktop shortcut: {e}")
        log(f"You can still run the app directly from: {script_path}")
 
    # Create update helper
    create_update_script()
 
    # Done
    print()
    print("=" * 55)
    print(f"  Installation complete!")
    print(f"")
    print(f"  A shortcut has been added to your Desktop.")
    print(f"  The app will check for updates automatically")
    print(f"  each time it is launched.")
    print(f"")
    print(f"  App installed to:")
    print(f"  {INSTALL_DIR}")
    print("=" * 55)
    print()
 
    if IS_WINDOWS:
        input("  Press Enter to close...")
 
if __name__ == '__main__':
    main()
