@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  py -3 -m venv .venv
  if errorlevel 1 goto :error
)
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto :error
.venv\Scripts\python.exe -m streamlit run app.py
pause
exit /b
:error
echo Installation failed. Install Python 3.12 from python.org with PATH enabled.
pause
exit /b 1
