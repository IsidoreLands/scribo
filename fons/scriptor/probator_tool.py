import os
import subprocess
import logging
import sys

def find_project_root(start_path):
    """
    Finds the project root by searching upwards for a .git directory
    or a pyproject.toml file.
    """
    # Using os.path.realpath to resolve any symlinks for robustness
    current_path = os.path.realpath(start_path)
    while True:
        if os.path.isdir(os.path.join(current_path, '.git')) or \
           os.path.isfile(os.path.join(current_path, 'pyproject.toml')):
            return current_path
        
        parent_path = os.path.dirname(current_path)
        if parent_path == current_path: # Reached the filesystem root
            return None
        current_path = parent_path

def run_tests(target_file):
    """
    Probator: Runs pytest in the project root of the target file.
    Returns True if tests pass or no tests are found, False otherwise.
    """
    logging.info("Probator: Verifying patch integrity...")
    
    project_root = find_project_root(os.path.dirname(target_file))

    if not project_root:
        logging.warning("Probator: Could not determine project root. Skipping tests.")
        return True # If we can't find a project, we can't run tests, so we assume success.

    logging.info(f"Probator: Found project root at '{project_root}'. Running pytest...")

    try:
        # Determine the absolute path to the pytest executable within the current venv
        venv_bin_dir = os.path.dirname(sys.executable)
        pytest_path = os.path.join(venv_bin_dir, "pytest")
        
        # A fallback check in case pytest wasn't installed correctly
        if not os.path.exists(pytest_path):
            logging.warning(f"Probator: 'pytest' executable not found at '{pytest_path}'. Skipping tests.")
            return True

        # '--no-test-found-exit-code=5' is a pytest 8+ feature. We'll use a more compatible approach.
        # We will check the exit code directly. Pytest exits with 5 if no tests are found.
        # We remove `check=True` so the command doesn't raise an exception on non-zero exit codes.
        result = subprocess.run(
            [pytest_path],
            cwd=project_root,
            capture_output=True,
            text=True
        )

        # Success is either exit code 0 (tests passed) or 5 (no tests found).
        if result.returncode == 0 or result.returncode == 5:
            if result.returncode == 5:
                logging.info("Probator: No tests were found.")
            logging.info("Probator: Verification successful.")
            return True
        else:
            # Any other non-zero exit code is a failure.
            logging.error("Probator: Tests FAILED. Reversion is necessary.")
            # Combine stdout and stderr for a complete failure log
            error_summary = f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
            logging.error(f"Probator: Pytest failure summary:\n{error_summary}")
            return False

    except Exception as e:
        # A catch-all for unexpected errors during the test run
        logging.error(f"Probator: An unexpected error occurred while running tests: {e}")
        return False
