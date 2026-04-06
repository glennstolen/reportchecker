@echo off
cd /d "%~dp0"

echo Stopper ReportChecker...
docker compose -f docker-compose.prod.yml down

echo ReportChecker er stoppet.
timeout /t 3 /nobreak >nul
