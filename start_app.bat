@echo off
ECHO Starting Deadline Agent UI...

REM Set the directory of this script as the working directory
cd /d "%~dp0"

REM Activate the virtual environment
call .\venv\Scripts\activate.bat

REM Run the Streamlit app
streamlit run app.py