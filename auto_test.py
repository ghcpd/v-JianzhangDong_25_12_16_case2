import os
import sys
import subprocess
import platform
from datetime import datetime
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "test_run.log"

SCRIPTS = {
    "Windows": "run_test.bat",
    "Linux": "run_test.sh",
    "Darwin": "run_test.sh",
}

TARGETS = ["input_backup", "input"]


def detect_env():
    sys_plat = platform.system()
    in_docker = Path("/.dockerenv").exists()
    return sys_plat, in_docker


def run_tests_for(target, script):
    env = os.environ.copy()
    env["TARGET_MODULE"] = target
    cmd = [script] if platform.system() == "Windows" else ["/bin/bash", script]
    start = datetime.utcnow().isoformat() + "Z"
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, timeout=300)
        output = proc.stdout.decode(errors="replace")
        rc = proc.returncode
    except Exception as e:
        output = str(e)
        rc = 2

    timestamp = datetime.utcnow().isoformat() + "Z"
    status = "TEST PASSED" if rc == 0 else "TEST FAILED"

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] TARGET={target} START={start}\n")
        f.write(output + "\n")
        f.write(f"[{timestamp}] TARGET={target} EXIT={rc} {status}\n\n")

    return rc == 0


if __name__ == "__main__":
    sys_plat, in_docker = detect_env()
    script = SCRIPTS.get(sys_plat, "run_test.sh")

    overall_ok = True
    for t in TARGETS:
        ok = run_tests_for(t, script)
        if not ok:
            overall_ok = False

    final_line = f"[{datetime.utcnow().isoformat()}Z] OVERALL {'PASSED' if overall_ok else 'FAILED'}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(final_line)

    if not overall_ok:
        sys.exit(1)
    print("All tests passed")
