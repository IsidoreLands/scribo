import os
import time
import subprocess
import sys
import logging
import queue
import threading
import logging.handlers
import shutil
import typer # <-- NEW
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from .perfector import perfice_resarcio
from .probator_tool import run_tests

app = typer.Typer(name="speculator", help="The autonomous daemon. Watches the inbox and processes patches.")
SCRIBO_INBOX = os.path.expanduser("~/scribo_inbox")
QUARANTINE_DIR = os.path.join(SCRIBO_INBOX, "quarantine")
LOG_FILE = os.path.join(SCRIBO_INBOX, "Acta_Scriptoris.log")

# --- Logger Setup (unchanged, but moved for clarity) ---
def setup_logging():
    logger = logging.getLogger()
    if logger.hasHandlers(): # Prevent adding handlers multiple times
        return
    logger.setLevel(logging.INFO)
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=10485760, backupCount=5
    )
    file_handler.setFormatter(log_formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# --- Operarius and PatchHandler Classes (unchanged) ---
class Operarius(threading.Thread):
    # ... (This entire class is unchanged) ...
    def __init__(self, work_queue):
        super().__init__()
        self.work_queue = work_queue
        self.daemon = True
    def run(self):
        logging.info("Operarius: Worker thread started. Awaiting tasks.")
        while True:
            patch_path = self.work_queue.get()
            if patch_path is None: break
            self.process_patch(patch_path)
            self.work_queue.task_done()
    def process_patch(self, patch_path):
        logging.info(f"Operarius: Processing '{os.path.basename(patch_path)}'.")
        time.sleep(0.1)
        if not os.path.exists(patch_path):
            logging.warning(f"Operarius: Patch file disappeared: {patch_path}")
            return
        with open(patch_path, 'r') as f:
            header = f.readline()
        if not header.startswith('--- target: '):
            logging.error(f"Operarius: Invalid patch header. Quarantining.")
            self.quarantine(patch_path)
            return
        target_file = header.split('--- target: ')[1].strip()
        temp_backup_path = target_file + ".scribo_bak"
        shutil.copy(target_file, temp_backup_path)
        logging.info("Probator: Created temporary backup.")
        if not perfice_resarcio(patch_path):
            logging.error(f"Operarius: Patch failed. Reverting.")
            self.revert_and_quarantine(target_file, temp_backup_path, patch_path)
            return
        self.run_ornator(target_file)
        if not run_tests(target_file):
            logging.error(f"Operarius: Tests failed. Reverting.")
            self.revert_and_quarantine(target_file, temp_backup_path, patch_path)
            return
        os.remove(temp_backup_path)
        os.remove(patch_path)
        logging.info("Operarius: Mutatis mutandis. Scriptor has perfected and verified the file.")
    def revert_and_quarantine(self, target, backup, patch):
        try:
            shutil.move(backup, target)
            self.quarantine(patch)
            logging.info("Probator: Reversion successful.")
        except Exception as e:
            logging.critical(f"PROBATOR: CRITICAL FAILURE. Could not restore backup. Error: {e}")
    def quarantine(self, patch_path):
        if os.path.exists(patch_path):
            shutil.move(patch_path, os.path.join(QUARANTINE_DIR, os.path.basename(patch_path)))
    def run_ornator(self, target_file):
        if not target_file.endswith('.py'):
            logging.info(f"Ornator: Skipping non-Python file.")
            return
        logging.info(f"Ornator: Formatting '{os.path.basename(target_file)}'...")
        try:
            venv_bin_dir = os.path.dirname(sys.executable)
            black_path = os.path.join(venv_bin_dir, "black")
            ruff_path = os.path.join(venv_bin_dir, "ruff")
            subprocess.run([black_path, target_file], check=True, capture_output=True, text=True)
            subprocess.run([ruff_path, "check", "--fix", target_file], check=True, capture_output=True, text=True)
            logging.info("Ornator: Formatting complete.")
        except Exception as e:
            logging.warning(f"Ornator: Formatting failed. Details: {e}")

class PatchHandler(FileSystemEventHandler):
    def __init__(self, work_queue):
        super().__init__()
        self.work_queue = work_queue
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".patch"):
            logging.info(f"Speculator: Detected new patch -> {os.path.basename(event.src_path)}")
            self.work_queue.put(event.src_path)

# The @app.callback() makes this function run automatically
# when the user types 'scriptor speculator'. No 'start' needed.
@app.callback(invoke_without_command=True)
def run_daemon():
    """
    Starts the Speculator daemon.
    """
    setup_logging()
    logging.info("--- Speculator v3.1 ---")
    os.makedirs(SCRIBO_INBOX, exist_ok=True); os.makedirs(QUARANTINE_DIR, exist_ok=True)
    work_queue = queue.Queue(); worker = Operarius(work_queue); worker.start()
    event_handler = PatchHandler(work_queue); observer = Observer()
    observer.schedule(event_handler, SCRIBO_INBOX, recursive=False); observer.start()
    logging.info(f"System online. Observing for patch files in: {SCRIBO_INBOX}")
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Shutdown signal received. Cleaning up."); observer.stop(); work_queue.put(None)
    observer.join(); worker.join(); logging.info("Speculator stopped.")
