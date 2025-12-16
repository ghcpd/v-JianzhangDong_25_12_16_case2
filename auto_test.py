#!/usr/bin/env python3
"""
Automatic test execution script for security testing.
Detects current environment and runs appropriate tests for both backup and fixed versions.
"""

import os
import sys
import subprocess
import platform
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

log_file = log_dir / "test_run.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ],
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)


def detect_environment():
    """Detect current operating system and environment."""
    system = platform.system()
    logger.info(f"Detected OS: {system}")
    
    if system == "Windows":
        return "windows"
    elif system in ("Linux", "Darwin"):
        return "unix"
    else:
        logger.warning(f"Unknown OS: {system}")
        return "unix"


def run_test_unix(test_file):
    """Run test on Unix-like systems (Linux/macOS)."""
    script = "run_test.sh"
    
    if not Path(script).exists():
        logger.error(f"Test script not found: {script}")
        return False, "Test script not found"
    
    try:
        logger.info(f"Running {script} for {test_file}...")
        result = subprocess.run(
            ["bash", script, test_file],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        output = result.stdout + result.stderr
        logger.info(f"Test output:\n{output}")
        
        if result.returncode == 0:
            logger.info(f"✓ {test_file} tests PASSED")
            return True, output
        else:
            logger.error(f"✗ {test_file} tests FAILED")
            return False, output
            
    except subprocess.TimeoutExpired:
        error_msg = f"Test timeout for {test_file}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Error running test: {e}"
        logger.error(error_msg)
        return False, error_msg


def run_test_windows(test_file):
    """Run test on Windows systems."""
    script = "run_test.bat"
    
    if not Path(script).exists():
        logger.error(f"Test script not found: {script}")
        return False, "Test script not found"
    
    try:
        logger.info(f"Running {script} for {test_file}...")
        result = subprocess.run(
            [script, test_file],
            capture_output=True,
            text=True,
            timeout=60,
            shell=True
        )
        
        output = result.stdout + result.stderr
        logger.info(f"Test output:\n{output}")
        
        if result.returncode == 0:
            logger.info(f"✓ {test_file} tests PASSED")
            return True, output
        else:
            logger.error(f"✗ {test_file} tests FAILED")
            return False, output
            
    except subprocess.TimeoutExpired:
        error_msg = f"Test timeout for {test_file}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Error running test: {e}"
        logger.error(error_msg)
        return False, error_msg


def run_tests(env_type):
    """Run all tests (backup and fixed version)."""
    logger.info("=" * 70)
    logger.info("AUTOMATIC TEST EXECUTION STARTED")
    logger.info("=" * 70)
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Environment: {env_type}")
    logger.info(f"Python Version: {sys.version}")
    logger.info("")
    
    test_files = ["input_backup.py", "input.py"]
    results = {}
    
    # Run tests for each file
    for test_file in test_files:
        if not Path(test_file).exists():
            logger.warning(f"File not found: {test_file}")
            results[test_file] = (False, f"File not found: {test_file}")
            continue
        
        logger.info("")
        logger.info("-" * 70)
        logger.info(f"Testing: {test_file}")
        logger.info("-" * 70)
        
        if env_type == "windows":
            success, output = run_test_windows(test_file)
        else:
            success, output = run_test_unix(test_file)
        
        results[test_file] = (success, output)
    
    # Log final summary
    logger.info("")
    logger.info("=" * 70)
    logger.info("TEST SUMMARY")
    logger.info("=" * 70)
    
    all_passed = True
    for test_file, (success, output) in results.items():
        status = "PASSED" if success else "FAILED"
        logger.info(f"{test_file}: {status}")
        if not success:
            all_passed = False
    
    logger.info("")
    logger.info("=" * 70)
    
    if all_passed:
        final_status = "TEST PASSED"
        logger.info(final_status)
        logger.info("All security tests completed successfully!")
        return 0
    else:
        final_status = "TEST FAILED"
        logger.info(final_status)
        logger.info("Some tests failed. Please review the logs above.")
        return 1


def main():
    """Main entry point."""
    try:
        # Detect environment
        env_type = detect_environment()
        
        # Load environment variables from .env if available
        env_file = Path(".env")
        if env_file.exists():
            logger.info(f"Loading environment from .env file")
            try:
                from dotenv import load_dotenv
                load_dotenv(env_file)
            except ImportError:
                logger.info("python-dotenv not installed, reading .env manually...")
                with open(env_file) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            if "=" in line:
                                key, value = line.split("=", 1)
                                os.environ[key.strip()] = value.strip()
        
        # Set default environment variables if not already set
        os.environ.setdefault("PAYMENT_TOKEN", "test_token_123")
        os.environ.setdefault("MAIL_SERVER_KEY", "test_key_456")
        os.environ.setdefault("INTERNAL_AUTH", "test_auth_789")
        os.environ.setdefault("FLASK_ENV", "development")
        
        # Run tests
        exit_code = run_tests(env_type)
        
        logger.info("")
        logger.info(f"Test execution completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Log file: {log_file}")
        logger.info("")
        
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        logger.warning("Test execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
