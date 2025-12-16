#!/usr/bin/env bash
# run_test.sh [backup|fixed]
set -euo pipefail
TARGET=${1:-both}
export PAYMENT_TOKEN=${PAYMENT_TOKEN:-test_payment_token}
export INTERNAL_AUTH=${INTERNAL_AUTH:-test_internal_auth}
export ADMIN_API_KEY=${ADMIN_API_KEY:-test_admin_key}
export CONFIG_DIR=${CONFIG_DIR:-configs}
python3 test_runner.py --target "$TARGET"
