@echo off
echo ========================================
echo Starting Security Vision System...
echo ========================================
echo.
echo Activating virtual environment...
call venv\Scripts\activate
echo.
echo Launching Streamlit app...
streamlit run app.py
pause
