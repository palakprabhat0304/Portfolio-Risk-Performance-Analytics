@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Creating local virtual environment...
    py -m venv .venv
)

call ".venv\Scripts\activate.bat"
python -m pip install -r requirements.txt
python run_project.py
if errorlevel 1 (
    echo.
    echo [ERROR] Project execution failed.
    exit /b 1
)

echo.
echo [OK] Portfolio Risk & Performance Analytics completed.
pause
