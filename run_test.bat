@echo off
set PAYMENT_TOKEN=tok_production_998877
set MAIL_SERVER_KEY=mail_srv_key_ABCDEFG
set INTERNAL_AUTH=admin_internal_5566
REM Start the app in background
start /B python input.py
timeout /t 3 /nobreak > nul

set FAILED=0

REM Test SQL injection
echo Testing SQL injection...
curl -s -X GET "http://localhost:5000/profile?id=1%27%20OR%20%271%27%3D%271" > response.txt
echo Response: & type response.txt
findstr /C:"error" response.txt > nul
if %errorlevel% equ 0 (
    echo SQL injection blocked: PASS
) else (
    echo SQL injection succeeded: FAIL
    set FAILED=1
)

REM Test command injection
echo Testing command injection...
curl -s -X GET "http://localhost:5000/export?name=test%3B%20echo%20hacked" > response.txt
echo Response: & type response.txt
findstr /C:"error" response.txt > nul
if %errorlevel% equ 0 (
    echo Command injection blocked: PASS
) else (
    echo Command injection succeeded: FAIL
    set FAILED=1
)

REM Test invalid auth
echo Testing invalid auth...
curl -s -X POST -H "Content-Type: application/json" -d "{}" http://localhost:5000/auth > response.txt
echo Response: & type response.txt
findstr /C:"error" response.txt > nul
if %errorlevel% equ 0 (
    echo Invalid auth blocked: PASS
) else (
    echo Invalid auth succeeded: FAIL
    set FAILED=1
)

REM Kill the app (assuming python.exe)
taskkill /IM python.exe /F > nul 2>&1

if %FAILED% equ 0 (
    echo TEST PASSED
    exit /b 0
) else (
    echo TEST FAILED
    exit /b 1
)