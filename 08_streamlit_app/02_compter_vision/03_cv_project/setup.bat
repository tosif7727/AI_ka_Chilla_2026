@echo off
echo ========================================
echo Security Vision System - Setup Script
echo ========================================
echo.

echo [1/4] Activating virtual environment...
call venv\Scripts\activate
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    echo Please run: python -m venv venv
    pause
    exit /b 1
)
echo ✓ Virtual environment activated
echo.

echo [2/4] Installing core packages...
pip install streamlit opencv-python pillow python-dotenv pandas matplotlib
if errorlevel 1 (
    echo ERROR: Failed to install core packages
    pause
    exit /b 1
)
echo ✓ Core packages installed
echo.

echo [3/4] Installing numpy...
pip install numpy
if errorlevel 1 (
    echo WARNING: Numpy installation failed
    echo The app will still work with basic features
)
echo.

echo [4/4] Installing AI packages (optional)...
pip install ultralytics
if errorlevel 1 (
    echo WARNING: Ultralytics installation failed
    echo The app will use fallback detection method
)
echo.

echo ========================================
echo Setup complete!
echo.
echo Ready to run! Execute:
echo   streamlit run app.py
echo ========================================
echo.
pause
