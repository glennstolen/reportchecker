@echo off
cd /d "%~dp0"

echo Starter ReportChecker...
docker compose -f docker-compose.prod.yml up -d

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Feil: Kunne ikke starte ReportChecker.
    echo Kontroller at Docker Desktop er installert og kjorer.
    pause
    exit /b 1
)

echo.
echo Venter pa at tjenestene starter...
timeout /t 15 /nobreak >nul

echo Apner nettleser...
start http://localhost:3000
