@echo off
setlocal EnableDelayedExpansion

echo ===================================================
echo   DocumentConverter Context Menu Installer
echo ===================================================
echo.

:: Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] This script requires Administrator privileges.
    echo Please right-click and select "Run as Administrator".
    echo.
    pause
    exit /b 1
)

:: Set paths
set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%..\.."
set "EXE_PATH=%ROOT_DIR%\dist\document-converter.exe"

:: Resolve absolute path
pushd "%ROOT_DIR%\dist"
set "ABS_EXE_PATH=%CD%\document-converter.exe"
popd

:: Validate executable exists
if not exist "%ABS_EXE_PATH%" (
    echo [ERROR] Executable not found at:
    echo %ABS_EXE_PATH%
    echo.
    echo Please make sure you have built the executable first:
    echo python -m PyInstaller --clean document-converter.spec
    echo.
    pause
    exit /b 1
)

echo Found executable: %ABS_EXE_PATH%
echo.
echo This will add "Convert with DocumentConverter" to your right-click menu.
echo.
set /p "CONFIRM=Are you sure you want to continue? (Y/N): "
if /i "%CONFIRM%" neq "Y" (
    echo Installation cancelled.
    pause
    exit /b 0
)

:: Prepare reg file content with escaped slashes
set "ESC_EXE_PATH=%ABS_EXE_PATH:\=\\%"

:: Create temporary reg file
set "TEMP_REG=%TEMP%\doc_conv_install.reg"
type "%SCRIPT_DIR%add_context_menu.reg" > "%TEMP_REG%"

echo Using executable path: %ABS_EXE_PATH%
echo Escaped path for registry: %ESC_EXE_PATH%

:: Replace placeholder using PowerShell (safer than batch replacement)
powershell -Command "(Get-Content '%TEMP_REG%') -replace 'INSTALL_PATH', '%ESC_EXE_PATH%' | Set-Content '%TEMP_REG%'"

:: Import to registry
echo.
echo Installing registry keys...

:: Cleanup old global key if exists
reg delete "HKCR\*\shell\DocumentConverter" /f >nul 2>&1
if %errorLevel% equ 0 (
    echo [INFO] Removed old global context menu entry.
)

reg import "%TEMP_REG%"

if %errorLevel% equ 0 (
    echo.
    echo [SUCCESS] Context menu installed successfully!
    echo You can now right-click any file and select "Convert with DocumentConverter".
) else (
    echo.
    echo [ERROR] Failed to install registry keys.
)

:: Cleanup
if exist "%TEMP_REG%" del "%TEMP_REG%"

echo.
pause
