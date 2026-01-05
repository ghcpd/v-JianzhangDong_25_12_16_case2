@echo off
REM Test script for Windows

setlocal enabledelayedexpansion

echo.
echo =========================================
echo Running security tests for Flask app
echo =========================================
echo.

REM Load environment variables from .env file if it exists
if exist ".env" (
    for /f "usebackq delims==" %%A in (".env") do (
        if not "%%A"=="" (
            if not "%%A:~0,1%%" == "#" (
                set %%A
            )
        )
    )
)

REM Set default test environment variables if not set
if not defined PAYMENT_TOKEN set PAYMENT_TOKEN=test_token_123
if not defined MAIL_SERVER_KEY set MAIL_SERVER_KEY=test_key_456
if not defined INTERNAL_AUTH set INTERNAL_AUTH=test_auth_789
set FLASK_ENV=development

REM Check which file to test
set TARGET_FILE=%1
if "!TARGET_FILE!"=="" set TARGET_FILE=input.py

echo Testing file: !TARGET_FILE!
echo Test Environment: Windows
python --version
echo.

REM Verify file exists
if not exist "!TARGET_FILE!" (
    echo ERROR: File not found - !TARGET_FILE!
    exit /b 1
)

REM Test 1: Syntax validation
echo [TEST 1] Syntax validation...
python -m py_compile "!TARGET_FILE!" >nul 2>&1
if !errorlevel! equ 0 (
    echo ✓ Syntax valid
) else (
    echo ✗ Syntax error
    exit /b 1
)

echo.

REM Test 2: Security checks
echo [TEST 2] Security checks...

REM Check for hardcoded secrets (should only be in backup)
if "!TARGET_FILE!"=="input.py" (
    findstr /R "tok_production mail_srv_key_ admin_internal_" "!TARGET_FILE!" >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✗ FAILED: Hardcoded secrets found in !TARGET_FILE!
        exit /b 1
    ) else (
        echo ✓ No hardcoded secrets detected
    )
)

REM Check for SQL injection vulnerability (string formatting in WHERE clause)
findstr "WHERE.*%s" "!TARGET_FILE!" >nul 2>&1
if !errorlevel! equ 0 (
    if "!TARGET_FILE!"=="input.py" (
        echo ✗ FAILED: SQL injection vulnerability found
        exit /b 1
    ) else (
        echo ⚠ SQL injection pattern found (expected in backup)
    )
) else (
    echo ✓ No obvious SQL injection patterns
)

REM Check for shell=True in actual code (not comments)
findstr "Popen.*shell=True" "!TARGET_FILE!" >nul 2>&1
if !errorlevel! equ 0 (
    if "!TARGET_FILE!"=="input.py" (
        echo ✗ FAILED: shell=True found in subprocess calls
        exit /b 1
    ) else (
        echo ⚠ shell=True found (expected in backup)
    )
) else (
    echo ✓ No dangerous subprocess calls with shell=True
)

REM Check for debug=True in app.run (actual hardcoded debug)
findstr "app.run.*debug=True" "!TARGET_FILE!" >nul 2>&1
if !errorlevel! equ 0 (
    if "!TARGET_FILE!"=="input.py" (
        echo ✗ FAILED: debug=True found in production code
        exit /b 1
    ) else (
        echo ⚠ debug=True found (expected in backup)
    )
) else (
    echo ✓ Debug mode properly configured
)

echo.
echo =========================================
if "!TARGET_FILE!"=="input.py" (
    echo All security tests PASSED for secured version
    exit /b 0
) else (
    echo Vulnerability tests confirmed in backup
    exit /b 0
)
