import os
import platform
import subprocess
import datetime
from pathlib import Path

LOG_FILE = Path("logs/test_run.log")
LOG_FILE.parent.mkdir(exist_ok=True)


def run_tests(target: str) -> None:
    # Determine which script to run based on platform
    system = platform.system().lower()
    if system == "windows":
        script = "run_test.bat"
        shell = True
    else:
        script = "./run_test.sh"
        shell = True

    env = os.environ.copy()
    env["TEST_TARGET"] = target

    proc = subprocess.run(script, shell=shell, capture_output=True, text=True, env=env)

    now = datetime.datetime.utcnow().isoformat()
    status = "TEST PASSED" if proc.returncode == 0 else "TEST FAILED"

    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"[{now}] Running tests for target={target} (platform={system})\n")
        f.write(f"Command: {script}\n")
        f.write("--- stdout ---\n")
        f.write(proc.stdout)
        f.write("--- stderr ---\n")
        f.write(proc.stderr)
        f.write(f"Exit code: {proc.returncode} -> {status}\n")
        f.write("\n")

    print(f"{target} tests completed: {status}")


if __name__ == "__main__":
    for tgt in ["backup", "fixed"]:
        run_tests(tgt)
