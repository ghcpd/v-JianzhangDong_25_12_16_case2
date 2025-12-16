#!/bin/bash

# Start the app in background
python3 input.py &
APP_PID=$!

# Wait for app to start
sleep 3

FAILED=0

# Test SQL injection
echo "Testing SQL injection..."
RESPONSE=$(curl -s -X GET "http://localhost:5000/profile?id=1' OR '1'='1")
if echo "$RESPONSE" | grep -q "error"; then
    echo "SQL injection blocked: PASS"
else
    echo "SQL injection succeeded: FAIL"
    FAILED=1
fi

# Test command injection
echo "Testing command injection..."
RESPONSE=$(curl -s -X GET "http://localhost:5000/export?name=test; echo hacked")
if echo "$RESPONSE" | grep -q "error"; then
    echo "Command injection blocked: PASS"
else
    echo "Command injection succeeded: FAIL"
    FAILED=1
fi

# Test invalid auth
echo "Testing invalid auth..."
RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" -d '{}' http://localhost:5000/auth)
if echo "$RESPONSE" | grep -q "error"; then
    echo "Invalid auth blocked: PASS"
else
    echo "Invalid auth succeeded: FAIL"
    FAILED=1
fi

# Kill the app
kill $APP_PID
wait $APP_PID 2>/dev/null

if [ $FAILED -eq 0 ]; then
    echo "TEST PASSED"
    exit 0
else
    echo "TEST FAILED"
    exit 1
fi