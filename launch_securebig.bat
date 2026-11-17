@echo off
REM Launches the SecureBig 3D dashboard: starts a local web server (if not already
REM running) and opens it in the default browser.
setlocal
set "UI_DIR=C:\Users\Adarsh singh\.zcode\workspace\default\securebig-3d-ui"
set PORT=8080

REM Check if something is already listening on the port
netstat -ano | findstr ":%PORT% " | findstr "LISTENING" >nul
if errorlevel 1 (
    echo Starting SecureBig dashboard server on port %PORT%...
    start "SecureBig 3D Dashboard Server" /min cmd /c "cd /d ""%UI_DIR%"" && python -m http.server %PORT%"
    timeout /t 2 /nobreak >nul
) else (
    echo Server already running on port %PORT%.
)

start "" "http://localhost:%PORT%"
endlocal
