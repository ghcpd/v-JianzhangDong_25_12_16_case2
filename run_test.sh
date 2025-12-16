#!/usr/bin/env bash
set -e

# Run tests for input_backup and input
RESULT=0
LOGFILE=logs/test_run.log
mkdir -p logs

echo "$(date -Iseconds) Running tests for input_backup" | tee -a "$LOGFILE"
MODULE_NAME=input_backup pytest -q || RESULT=$?
if [ "$RESULT" -eq 0 ]; then
  echo "$(date -Iseconds) input_backup: TEST PASSED" | tee -a "$LOGFILE"
else
  echo "$(date -Iseconds) input_backup: TEST FAILED (code $RESULT)" | tee -a "$LOGFILE"
fi

echo "$(date -Iseconds) Running tests for input" | tee -a "$LOGFILE"
MODULE_NAME=input pytest -q || RESULT=$?
if [ "$RESULT" -eq 0 ]; then
  echo "$(date -Iseconds) input: TEST PASSED" | tee -a "$LOGFILE"
else
  echo "$(date -Iseconds) input: TEST FAILED (code $RESULT)" | tee -a "$LOGFILE"
fi

if [ "$RESULT" -eq 0 ]; then
  echo "$(date -Iseconds) TEST PASSED" | tee -a "$LOGFILE"
  exit 0
else
  echo "$(date -Iseconds) TEST FAILED" | tee -a "$LOGFILE"
  exit $RESULT
fi
