@echo off
setlocal enabledelayedexpansion
set LOGFILE=logs\test_run.log
if not exist logs mkdir logs

echo %DATE% %TIME% Running tests for input_backup >> %LOGFILE%
set MODULE_NAME=input_backup
pytest -q
if %ERRORLEVEL% EQU 0 (
  echo %DATE% %TIME% input_backup: TEST PASSED >> %LOGFILE%
) else (
  echo %DATE% %TIME% input_backup: TEST FAILED (%ERRORLEVEL%) >> %LOGFILE%
)

echo %DATE% %TIME% Running tests for input >> %LOGFILE%
set MODULE_NAME=input
pytest -q
if %ERRORLEVEL% EQU 0 (
  echo %DATE% %TIME% input: TEST PASSED >> %LOGFILE%
  echo %DATE% %TIME% TEST PASSED >> %LOGFILE%
  exit /b 0
) else (
  echo %DATE% %TIME% input: TEST FAILED (%ERRORLEVEL%) >> %LOGFILE%
  echo %DATE% %TIME% TEST FAILED >> %LOGFILE%
  exit /b %ERRORLEVEL%
)
