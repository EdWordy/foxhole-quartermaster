@echo off
echo ===== Foxhole Quartermaster Build Script =====
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

REM Check if pip is installed
pip --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: pip is not installed or not in PATH
    exit /b 1
)

echo Installing required packages...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to install required packages
    exit /b 1
)

echo.
echo Creating build directories...
if not exist "build" mkdir build
if not exist "dist" mkdir dist

echo.
echo Building executable with PyInstaller...
pyinstaller --clean --noconfirm foxhole_quartermaster.spec
if %ERRORLEVEL% NEQ 0 (
    echo Error: PyInstaller failed to build the executable
    exit /b 1
)

echo.
echo Copying additional files...
if not exist "dist\FoxholeQuartermaster\CheckImages" mkdir "dist\FoxholeQuartermaster\CheckImages"
xcopy /E /I /Y "CheckImages" "dist\FoxholeQuartermaster\CheckImages"
copy /Y "item_mappings.csv" "dist\FoxholeQuartermaster\"
copy /Y "item_thresholds.json" "dist\FoxholeQuartermaster\"
if exist "config.yaml" copy /Y "config.yaml" "dist\FoxholeQuartermaster\"

echo.
echo Build completed successfully!
echo Executable is located in dist\FoxholeQuartermaster\FoxholeQuartermaster.exe
echo.

pause
