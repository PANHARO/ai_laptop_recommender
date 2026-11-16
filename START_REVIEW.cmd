@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Python environment missing. Follow the README setup instructions first.
  pause
  exit /b 1
)
echo Open http://127.0.0.1:8501 in your browser when the review desk starts.
".venv\Scripts\python.exe" -m laptop_collection review
