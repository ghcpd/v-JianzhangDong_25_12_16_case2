@echo off
REM run_test.bat [backup|fixed]
setlocal enabledelayedexpansion
set TARGET=%1
if "%TARGET%"=="" set TARGET=both
if "%PAYMENT_TOKEN%"=="" set PAYMENT_TOKEN=test_payment_token
if "%INTERNAL_AUTH%"=="" set INTERNAL_AUTH=test_internal_auth
if "%ADMIN_API_KEY%"=="" set ADMIN_API_KEY=test_admin_key
if "%CONFIG_DIR%"=="" set CONFIG_DIR=configs
python test_runner.py --target "%TARGET%"
exit /b %errorlevel%
