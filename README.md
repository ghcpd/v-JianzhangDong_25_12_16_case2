# Security audit and fixes for input.py

Overview
- input_backup.py: original file (unchanged) kept as a backup for comparison and testing.
- input.py: patched, secured version (secrets moved to env, SQL injection fixed, SSRF/SS checks, no shell usage, path traversal protected, HMAC-SHA256 used for auth tokens, admin protection on sensitive endpoints).
- report.json: structured report listing vulnerabilities, severities, affected lines and explanations.
- test_runner.py: simple tests that validate the vulnerability fixes (runs checks against both backup and fixed modules).
- run_test.sh / run_test.bat: platform test wrappers (Linux/macOS and Windows respectively).
- auto_test.py: automatic detector/runner that runs tests for backup and fixed modules and records logs at logs/test_run.log.
- setup.sh: helper to create a sample DB and config directory for local testing.
- requirements.txt / Dockerfile: environment replication files.

Setup (Linux/macOS)
1. Create a Python virtual environment and install deps:
   ./setup.sh
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

2. Set required environment variables BEFORE running the service or tests:
   export PAYMENT_TOKEN=your_payment_token
   export MAIL_SERVER_KEY=your_mail_key
   export INTERNAL_AUTH=your_internal_secret
   export ADMIN_API_KEY=your_admin_token

Running tests
- Linux/macOS: ./run_test.sh
- Windows: run_test.bat
- Both scripts accept an optional argument: "backup" or "fixed" to run tests for input_backup.py or input.py individually. By default they run both checks.

Automatic testing and logs
- Use auto_test.py to run platform-specific test scripts automatically. It will write results to logs/test_run.log and print FINAL STATUS (TEST PASSED or TEST FAILED).
  python3 auto_test.py

Interpreting results
- TEST PASSED: fixed version behaved securely and backup demonstrated expected vulnerable behavior (this means the patch is effective).
- TEST FAILED: either the fixed tests did not pass, or the backup behavior was not as expected; inspect logs/test_run.log for details and failure output.

Notes
- Secrets are intentionally loaded from environment variables. Do NOT commit real secrets to the repository.
- The changes aim to be incremental and minimal to make the code safer and easier to review.
