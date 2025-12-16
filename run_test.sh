#!/usr/bin/env bash
set -e
# If TARGET_MODULE not set, run tests for both
if [ -z "${TARGET_MODULE:-}" ]; then
  echo "Running full test suite (both modules)"
  pytest -q
else
  echo "Running tests for $TARGET_MODULE"
  pytest -q
fi
