@echo off
REM ====================================================================
REM  Windows Task Scheduler Runner for X Tech Digest
REM ====================================================================

cd /d "D:\Project_WorkSpace\x-tech-digest"

REM Ensure logs directory exists
if not exist "logs" mkdir "logs"

REM Define log filename with current date
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
set LOGFILE=logs\run_%mydate%.log

echo ============================================================ >> "%LOGFILE%"
echo Starting X Tech Digest at %TIME% on %DATE% >> "%LOGFILE%"
echo ============================================================ >> "%LOGFILE%"

REM If you created a virtual environment (.venv), activate it:
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM Run the digest script
python main.py >> "%LOGFILE%" 2>&1

echo Finished at %TIME% with Exit Code %ERRORLEVEL% >> "%LOGFILE%"
echo. >> "%LOGFILE%"
