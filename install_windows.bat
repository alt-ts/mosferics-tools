@echo off
setlocal EnableDelayedExpansion
title Mosferics Tools Installer

echo.
echo =========================================
echo   Mosferics Price List Generator
echo   Windows Installer
echo =========================================
echo.

:: Check if Python is already installed
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Python is already installed.
    goto :run_installer
)

python3 --version >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Python is already installed.
    set PYTHON_CMD=python3
    goto :run_installer
)

:: Python not found - download and install silently
echo [..] Python not found. Downloading Python installer...
echo     This may take a minute depending on your connection.
echo.

:: Download Python 3.12 installer (stable, widely compatible)
set PYTHON_URL=https://www.python.org/ftp/python/3.12.4/python-3.12.4-amd64.exe
set PYTHON_INSTALLER=%TEMP%\python_installer.exe

:: Use PowerShell to download (available on all modern Windows)
powershell -Command "Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_INSTALLER%' -UseBasicParsing"

if not exist "%PYTHON_INSTALLER%" (
    echo.
    echo [ERROR] Could not download Python.
    echo         Please check your internet connection and try again.
    echo         Or install Python manually from: https://python.org/downloads
    pause
    exit /b 1
)

echo [..] Installing Python silently...
:: Install Python silently, add to PATH, for all users
"%PYTHON_INSTALLER%" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

:: Refresh PATH so python is available in this session
set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%"
set "PATH=C:\Program Files\Python312;C:\Program Files\Python312\Scripts;%PATH%"

:: Clean up installer
del "%PYTHON_INSTALLER%" >nul 2>&1

:: Verify
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Python installation failed or PATH not updated.
    echo         Please restart your computer and try again.
    echo         Or install Python manually from: https://python.org/downloads
    echo         Make sure to tick "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo [OK] Python installed successfully.

:run_installer
echo.
echo [..] Running Mosferics installer...
echo.

:: Find python command
set PYTHON_CMD=python
python --version >nul 2>&1
if %errorlevel% neq 0 set PYTHON_CMD=python3

:: Run the Python installer script from the same folder as this .bat
set SCRIPT_DIR=%~dp0
set INSTALLER_PY=%SCRIPT_DIR%install.py

if not exist "%INSTALLER_PY%" (
    echo [ERROR] install.py not found in the same folder as this file.
    echo         Please make sure install.py is in the same folder as install_windows.bat
    pause
    exit /b 1
)

%PYTHON_CMD% "%INSTALLER_PY%"

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Installation failed. See messages above.
    pause
    exit /b 1
)

exit /b 0
