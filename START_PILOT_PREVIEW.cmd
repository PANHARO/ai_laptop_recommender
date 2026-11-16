@echo off
setlocal
set "pilotPreview=%~dp0reports\pilot_2026-10-29\preview\START_PILOT_PREVIEW.html"
if not exist "%pilotPreview%" (
  echo Preview file not found. Rebuild with the command in docs\PILOT.md.
  pause
  exit /b 1
)
start "" "%pilotPreview%"
