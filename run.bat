@echo off
chcp 65001
echo Creating/Activating virtual environment...
if not exist venv (
    python -m venv venv
    if %errorlevel% neq 0 exit /b
)

cd /d %~dp0

call venv\Scripts\activate
if %errorlevel% neq 0 exit /b

echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 exit /b

echo Running Gradio application...
python main.py

pause