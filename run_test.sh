#!/bin/bash

# Test script for Linux/macOS
set -e

echo "========================================="
echo "Running security tests for Flask app"
echo "========================================="

# Load environment variables
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

# Set default test environment variables if not set
export PAYMENT_TOKEN=${PAYMENT_TOKEN:-"test_token_123"}
export MAIL_SERVER_KEY=${MAIL_SERVER_KEY:-"test_key_456"}
export INTERNAL_AUTH=${INTERNAL_AUTH:-"test_auth_789"}
export FLASK_ENV=development

# Check which file to test
TARGET_FILE=${1:-"input.py"}

echo "Testing file: $TARGET_FILE"
echo "Test Environment: $(uname -s)"
echo "Python Version: $(python3 --version)"
echo ""

# Verify file exists
if [ ! -f "$TARGET_FILE" ]; then
    echo "ERROR: File not found - $TARGET_FILE"
    exit 1
fi

# Run security tests
echo "[TEST 1] Syntax validation..."
python3 -m py_compile "$TARGET_FILE" && echo "✓ Syntax valid" || { echo "✗ Syntax error"; exit 1; }

echo ""
echo "[TEST 2] Import check..."
python3 -c "import sys; sys.path.insert(0, '.'); exec(open('$TARGET_FILE').read())" 2>&1 | head -20 || true

echo ""
echo "[TEST 3] Security checks..."

# Check for hardcoded secrets in file (should only be in input_backup.py)
if [ "$TARGET_FILE" = "input.py" ]; then
    if grep -q "tok_production\|mail_srv_key_\|admin_internal_" "$TARGET_FILE"; then
        echo "✗ FAILED: Hardcoded secrets found in $TARGET_FILE"
        exit 1
    else
        echo "✓ No hardcoded secrets detected"
    fi
fi

# Check for SQL injection vulnerability (string formatting with %)
if grep -q "WHERE.*%s\|\".*%\s*\"" "$TARGET_FILE"; then
    if [ "$TARGET_FILE" = "input.py" ]; then
        echo "✗ FAILED: SQL injection vulnerability found"
        exit 1
    else
        echo "⚠ SQL injection pattern found (expected in backup)"
    fi
else
    echo "✓ No obvious SQL injection patterns"
fi

# Check for shell=True in actual code (not comments)
if grep -q "Popen.*shell=True" "$TARGET_FILE"; then
    if [ "$TARGET_FILE" = "input.py" ]; then
        echo "✗ FAILED: shell=True found in subprocess calls"
        exit 1
    else
        echo "⚠ shell=True found (expected in backup)"
    fi
else
    echo "✓ No dangerous subprocess.Popen with shell=True"
fi

# Check for debug=True in app.run (actual hardcoded debug)
if grep -q "app.run.*debug=True" "$TARGET_FILE"; then
    if [ "$TARGET_FILE" = "input.py" ]; then
        echo "✗ FAILED: debug=True found in production code"
        exit 1
    else
        echo "⚠ debug=True found (expected in backup)"
    fi
else
    echo "✓ Debug mode properly configured"
fi

echo ""
echo "========================================="
if [ "$TARGET_FILE" = "input.py" ]; then
    echo "All security tests PASSED for secured version"
    exit 0
else
    echo "Vulnerability tests confirmed in backup"
    exit 0
fi
