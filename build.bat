/home/claude/build.bat

@echo off
setlocal EnableDelayedExpansion

echo ===== Foxhole Quartermaster Build Script =====
echo.

REM ============================================
REM Check Prerequisites
REM ============================================

echo Checking prerequisites...

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH
    exit /b 1
)
echo [OK] Python found

REM Check if pip is installed
pip --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] pip is not installed or not in PATH
    exit /b 1
)
echo [OK] pip found
echo.

REM ============================================
REM Install Dependencies
REM ============================================

echo Installing required packages...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install required packages
    exit /b 1
)
echo [OK] Packages installed successfully
echo.

REM ============================================
REM Create Build Directories
REM ============================================

echo Creating build directories...
if not exist "build" mkdir build
if not exist "dist" mkdir dist
echo [OK] Directories created
echo.

REM ============================================
REM Build Executable
REM ============================================

echo Building executable with PyInstaller...

set EXCLUDE_MODULES=^
    --exclude-module scipy ^
    --exclude-module setuptools ^
    --exclude-module hook ^
    --exclude-module distutils ^
    --exclude-module site ^
    --exclude-module hooks ^
    --exclude-module tornado ^
    --exclude-module PyQt4 ^
    --exclude-module PyQt5 ^
    --exclude-module pydoc ^
    --exclude-module pythoncom ^
    --exclude-module pytz ^
    --exclude-module pywintypes ^
    --exclude-module sqlite3 ^
    --exclude-module pyz ^
    --exclude-module sklearn ^
    --exclude-module scapy ^
    --exclude-module scrapy ^
    --exclude-module sympy ^
    --exclude-module kivy ^
    --exclude-module pyramid ^
    --exclude-module tensorflow ^
    --exclude-module pipenv ^
    --exclude-module pattern ^
    --exclude-module mechanize ^
    --exclude-module beautifulsoup4 ^
    --exclude-module requests ^
    --exclude-module wxPython ^
    --exclude-module pygi ^
    --exclude-module pillow ^
    --exclude-module pygame ^
    --exclude-module pyglet ^
    --exclude-module flask ^
    --exclude-module django ^
    --exclude-module pylint ^
    --exclude-module pytube ^
    --exclude-module odfpy ^
    --exclude-module mccabe ^
    --exclude-module pilkit ^
    --exclude-module six ^
    --exclude-module wrapt ^
    --exclude-module astroid ^
    --exclude-module isort

pyinstaller --clean --noconfirm --onefile --strip %EXCLUDE_MODULES% foxhole_quartermaster.spec

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PyInstaller failed to build the executable
    exit /b 1
)
echo [OK] Executable built successfully
echo.

REM ============================================
REM Copy Additional Files
REM ============================================

echo Copying additional files...

REM Create data directories
if not exist "dist\FoxholeQuartermaster\data\processed_templates" (
    mkdir "dist\FoxholeQuartermaster\data\processed_templates"
)

REM Copy templates
xcopy /E /I /Y "data\processed_templates" "dist\FoxholeQuartermaster\data\processed_templates"
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Failed to copy processed templates
)

REM Copy JSON files
copy /Y "data\catalog.json" "dist\FoxholeQuartermaster\data" >nul
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Failed to copy catalog.json
)

copy /Y "data\item_thresholds.json" "dist\FoxholeQuartermaster\data" >nul
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Failed to copy item_thresholds.json
)

REM Copy config if exists
if exist "config.yaml" (
    copy /Y "config.yaml" "dist\FoxholeQuartermaster\" >nul
    echo [OK] config.yaml copied
) else (
    echo [INFO] config.yaml not found, skipping
)

echo [OK] Additional files copied
echo.

REM ============================================
REM Build Complete
REM ============================================

echo ==========================================
echo Build completed successfully!
echo ==========================================
echo.
echo Executable location:
echo   dist\FoxholeQuartermaster\FoxholeQuartermaster.exe
echo.
pause