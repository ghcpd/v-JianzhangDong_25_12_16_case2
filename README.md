# Secureed Project Audit and Test Harness ✅

## Overview
This workspace contains the original vulnerable script `input_backup.py` and a secured version `input.py`, along with automated tests and environment scripts.

Files generated:
- `input_backup.py` — Original file (backup). ⚠️ Vulnerable
- `input.py` — Hardened/secure implementation ✅
- `report.json` — Structured vulnerability report (details and fixes)
- `tests/test_security.py` — Test cases demonstrating vulnerabilities in the backup and mitigation in the fixed version
- `requirements.txt` — Python dependencies
- `Dockerfile` — Simple container to run the app
- `setup.sh` — Create virtualenv and install dependencies (Linux/macOS)
- `run_test.sh` — Runs `pytest` (Linux/macOS)
- `run_test.bat` — Runs `pytest` (Windows)
- `auto_test.py` — Detects environment and runs tests for `input_backup` and `input` sequentially, writes logs to `logs/test_run.log`
- `logs/` — Directory where test logs are written

---

## Setup (Linux/macOS)
1. Ensure Python 3.8+ is installed.
2. Run:
   ```bash
   ./setup.sh
   source .venv/bin/activate
   ```
3. Set required environment variables (recommended to export before running):
   - `SECRET_KEY` - application secret for token signing
   - `ADMIN_PASSWORD` - admin password used to request tokens in `/auth`
   - `PAYMENT_TOKEN` - (optional) token used to notify payment service
   - `ALLOWED_NOTIFY_HOSTS` - comma-separated list of allowed notify hosts (optional)

Example:
```bash
export SECRET_KEY=change-me
export ADMIN_PASSWORD=strongpass
export ALLOWED_NOTIFY_HOSTS=example.com,my.notify.host
```

## Running Tests
### Linux/macOS
1. To run tests manually:
   ```bash
   TARGET_MODULE=input pytest -q
   ```
   Replace `TARGET_MODULE` with `input_backup` or `input`.
2. Or run the helper script:
   ```bash
   ./run_test.sh
   ```

### Windows
1. To run tests manually in an activated environment:
   ```cmd
   set TARGET_MODULE=input
   pytest -q
   ```
2. Or run the helper batch:
   ```cmd
   run_test.bat
   ```

## Automatic Test Runner
`auto_test.py` will detect the environment (Windows/Linux/Docker) and execute the test script for both `input_backup` and `input` sequentially. It writes a timestamped log to `logs/test_run.log` and appends a final status line saying `TEST PASSED` or `TEST FAILED` for each run.

Usage:
```bash
python auto_test.py
# Check logs with: less logs/test_run.log
```

## Interpreting `logs/test_run.log`
Each test run appends:
- Timestamp and target module
- Full pytest output
- Exit code and `TEST PASSED` or `TEST FAILED`

A final summary line indicates overall PASS/FAIL.

---

## Notes & Security Recommendations
- Ensure secrets are provided via secure environment variables or a secrets manager, never checked into source control.
- In production, run the Flask app behind a WSGI server (gunicorn/uWSGI) and behind TLS termination.
- Continuously run the provided tests as part of CI to catch regressions.

If you want, I can run the tests here and provide the log output. ✅
