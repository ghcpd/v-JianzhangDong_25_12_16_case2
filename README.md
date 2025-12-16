# Project: Secure Flask App

This repository contains a (fixed) secure version of the vulnerable `input.py` file and a backup copy named `input_backup.py` showing the original issues.

## Files in this repo

- `input.py` — the fixed, secure implementation.
- `input_backup.py` — the original vulnerable code (kept for audit comparison and tests).
- `report.json` — structured vulnerability report (IDs, locations, original/fixed code, and explanation).
- `requirements.txt` — pip packages required to run the app and tests.
- `setup.sh` — convenience script (Linux/macOS) to create a venv and install requirements.
- `run_test.sh` — run tests in Linux/macOS (tests are `pytest` based).
- `run_test.bat` — run tests on Windows.
- `auto_test.py` — script that runs tests for both the backup and fixed targets and logs the results into `logs/test_run.log`.
- `Dockerfile` — container that runs the auto tests on start.
- `tests/test_security.py` — pytest suite validating the vulnerabilities are present in `input_backup.py` and fixed in `input.py`.

## How to run locally (Linux/macOS)

```bash
# Install
./setup.sh
# Run tests for the fixed code only
./run_test.sh
# Or run both backup and fixed tests and log results
python auto_test.py
```

## How to run locally (Windows)

```powershell
# Install dependencies (in a virtualenv if you prefer)
pip install -r requirements.txt
# Run tests for fixed code only
run_test.bat
# Or run both backup and fixed tests and log results
python auto_test.py
```

## Important notes

- Hard-coded secrets were removed and are expected to be provided via environment variables (`PAYMENT_TOKEN`, `MAIL_SERVER_KEY`, `INTERNAL_AUTH`, etc.).
- SQL queries are parameterized to prevent SQL injection.
- `transfer_funds` validates `notify_url` to mitigate SSRF.
- `export_data` now uses Python's `zipfile` module and validates filenames to avoid shell-injection.
- `update_records` prevents path traversal by restricting config load sites to a configured directory (`CONFIG_DIR`).

## Check logs

After running `auto_test.py` you will find a detailed log at `logs/test_run.log` including timestamps, the platform used, stdout/stderr of the test runs, and a final `TEST PASSED` or `TEST FAILED` status for each target.

---

## Disclaimer

These fixes are demonstration-oriented and may need further hardening or integration-specific adjustments before production use (e.g., robust validation, better error handling, secure configuration management, rate limiting, etc.).
