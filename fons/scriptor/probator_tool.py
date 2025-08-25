import os
import subprocess
import logging
import sys

def find_project_root(start_path):
    """
    Finds the project root by searching upwards for a .git directory
    or a pyproject.toml file.
    """
    current_path = os.path.abspath(start_path)
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
        return True

    logging.info(f"Probator: Found project root at '{project_root}'. Running pytest...")

    try:
        # --- THIS IS THE NEW, ROBUST LOGIC ---
        venv_bin_dir = os.path.dirname(sys.executable)
        pytest_path = os.path.join(venv_bin_dir, "pytest")
        
        # Check if pytest actually exists where we expect it
        if not os.path.exists(pytest_path):
            logging.warning(f"Probator: 'pytest' not found at '{pytest_path}'. Skipping tests.")
            return True

        result = subprocess.run(
            [pytest_path], # Use the absolute path
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True
        )
        # ------------------------------------

        logging.info("Probator: All tests passed.")
        return True
    except subprocess.CalledProcessError as e:
        logging.error("Probator: Tests FAILED. Reversion is necessary.")
        error_summary = "\n".join(e.stdout.splitlines()[-15:]) # More context on failure
        logging.error(f"Probator: Pytest failure summary:\n{error_summary}")
        return False
