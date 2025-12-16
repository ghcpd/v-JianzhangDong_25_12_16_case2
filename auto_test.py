import os
import shutil
import subprocess
import platform
from datetime import datetime

def log_message(log_file, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, 'a') as f:
        f.write(f"[{timestamp}] {message}\n")
        f.flush()

def run_test(file_to_test, log_file):
    try:
        # Backup current input.py
        if os.path.exists('input.py'):
            shutil.copy('input.py', 'input_temp.py')
        
        # Copy the file to test as input.py
        shutil.copy(file_to_test, 'input.py')
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if platform.system() == 'Windows':
            bat_path = os.path.join(script_dir, 'run_test.bat')
            result = subprocess.run(['cmd', '/c', bat_path], capture_output=True, text=True, timeout=60)
        else:
            sh_path = os.path.join(script_dir, 'run_test.sh')
            result = subprocess.run(['bash', sh_path], capture_output=True, text=True, timeout=30)
        
        output = result.stdout + result.stderr
        status = "TEST PASSED" if result.returncode == 0 else "TEST FAILED"
        
        log_message(log_file, f"Testing {file_to_test}")
        log_message(log_file, f"Output: {output}")
        log_message(log_file, f"Status: {status}")
        
    except Exception as e:
        log_message(log_file, f"Error testing {file_to_test}: {str(e)}")
        log_message(log_file, "Status: TEST FAILED")
    
    # Restore original input.py
    try:
        if os.path.exists('input_temp.py'):
            shutil.copy('input_temp.py', 'input.py')
            os.remove('input_temp.py')
    except Exception as e:
        log_message(log_file, f"Error restoring: {str(e)}")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(script_dir, 'auto_test.log')
    
    # Clear log file
    with open(log_file, 'w') as f:
        f.write("")
        f.flush()
    
    log_message(log_file, "Starting tests")
    
    run_test('input_backup.py', log_file)
    run_test('input.py', log_file)