@echo off
REM Run pytest (Windows)
if "%TARGET_MODULE%"=="" (
  echo Running full test suite (both modules)
) else (
  echo Running tests for %TARGET_MODULE%
)
pytest -q
exit /B %ERRORLEVEL%
