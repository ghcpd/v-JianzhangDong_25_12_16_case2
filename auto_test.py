#!/usr/bin/env python3
"""auto_test.py: detect environment, run the platform test script for backup and fixed modules,
capture output to logs/test_run.log with timestamps and a final TEST PASSED / TEST FAILED line.
"""
import subprocess
import platform
import os
import shlex
from datetime import datetime

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG = os.path.join(LOG_DIR, "test_run.log")

def now():
    return datetime.utcnow().isoformat() + "Z"

def run_script(cmd, env=None):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, env=dict(os.environ, **(env or {})))
    out, _ = proc.communicate()
    return proc.returncode, out.decode(errors='replace')

def main():
    system = platform.system()
    if system == "Windows":
        script = "run_test.bat"
    else:
        script = "./run_test.sh"

    entries = []
    # Run for backup and fixed separately so we can log per-target results
    for target in ("backup", "fixed"):
        cmd = f"{script} {target}"
        rc, out = run_script(cmd)
        status = "TEST PASSED" if rc == 0 and target == "fixed" else ("VULNERABLE" if rc == 0 and target == "backup" else "TEST FAILED")
        entries.append({"time": now(), "target": target, "rc": rc, "status": status, "output": out})
        # append to log file after each run
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"[{now()}] RUN: {cmd}\n")
            f.write(out + "\n")
            f.write(f"[{now()}] RESULT: {status} (rc={rc})\n\n")

    # Final overall status: passed only if fixed passed (rc==0) and backup run indicated vulnerability (rc==0)
    fixed_ok = any(e for e in entries if e['target']=='fixed' and e['rc']==0)
    backup_ok = any(e for e in entries if e['target']=='backup' and e['rc']==0)
    final = "TEST PASSED" if fixed_ok and backup_ok else "TEST FAILED"
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{now()}] FINAL STATUS: {final}\n")
    print(final)
    return 0 if final=="TEST PASSED" else 2

if __name__ == '__main__':
    raise SystemExit(main())
