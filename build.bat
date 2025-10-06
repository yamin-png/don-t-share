@echo off
echo ========================================
echo SR FAST OTP Bot - Build Script
echo ========================================

echo.
echo [1/3] Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)

echo.
echo [2/3] Cleaning previous builds...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "*.spec" del "*.spec"

echo.
echo [3/3] Building executable...
pyinstaller --noconfirm --onefile --windowed --name "TelegramBot" --add-data "chromedriver.exe;." app.py
if %errorlevel% neq 0 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo Executable location: dist\TelegramBot.exe
echo ========================================
pause
