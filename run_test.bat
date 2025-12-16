@echo off
REM Run tests for the fixed code by default unless TEST_TARGET is set by caller
if "%TEST_TARGET%"=="" set TEST_TARGET=fixed
pytest -q
