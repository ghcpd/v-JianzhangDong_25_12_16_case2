import os
import platform
import subprocess
import datetime

LOGFILE = os.path.join('logs', 'test_run.log')
os.makedirs('logs', exist_ok=True)


def log(msg):
    ts = datetime.datetime.utcnow().isoformat()
    with open(LOGFILE, 'a') as f:
        f.write(f"{ts} {msg}\n")
    print(msg)


def detect_env():
    if os.path.exists('/.dockerenv'):
        return 'docker'
    sys = platform.system().lower()
    if 'windows' in sys:
        return 'windows'
    return 'linux'


def run_script(script):
    log(f"Running script: {script}")
    try:
        proc = subprocess.run(script, shell=True, capture_output=True, text=True)
        out = proc.stdout + '\n' + proc.stderr
        log(f"Output for {script}:\n{out}")
        if proc.returncode == 0:
            log(f"{script}: TEST PASSED")
            return True
        else:
            log(f"{script}: TEST FAILED (code {proc.returncode})")
            return False
    except Exception as e:
        log(f"{script}: EXCEPTION {e}")
        return False


def main():
    env = detect_env()
    log(f"Detected environment: {env}")
    if env == 'windows':
        script = 'run_test.bat'
    else:
        script = './run_test.sh'

    success = run_script(script)
    if success:
        log('TEST PASSED')
        return 0
    else:
        log('TEST FAILED')
        return 2


if __name__ == '__main__':
    exit(main())
