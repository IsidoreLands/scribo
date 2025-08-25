import os
import time
import subprocess
import sys
import logging
import queue
import threading
import logging.handlers
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from scriptor.perfector import perfice_resarcio
from scriptor.probator_tool import run_tests

# --- Global Configuration ---
SCRIBO_INBOX = os.path.expanduser("~/scribo_inbox")
QUARANTINE_DIR = os.path.join(SCRIBO_INBOX, "quarantine")
LOG_FILE = os.path.join(SCRIBO_INBOX, "Acta_Scriptoris.log")

# --- Logger Setup ---
def setup_logging():
    """Configures a rotating logger to write to both a file and the console."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Rotating file handler: 10MB per file, keeping 5 old log files.
    # Acta_Scriptoris.log -> .log.1 -> .log.2 -> etc.
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=10485760, backupCount=5
    )

    file_handler.setFormatter(log_formatter)
    
    # Console handler for real-time feedback (remains the same)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# --- The Producer ---
class PatchHandler(FileSystemEventHandler):
    """The Watcher: Detects new patches and places them on the queue."""
    def __init__(self, work_queue):
        super().__init__()
        self.work_queue = work_queue

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".patch"):
            logging.info(f"Speculator: Detected new patch -> {os.path.basename(event.src_path)}")
            self.work_queue.put(event.src_path)

# --- The Consumer ---
class Operarius(threading.Thread):
    """The Workman: Processes patches from the queue one by one."""
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
            logging.warning(f"Operarius: Patch file disappeared before processing: {patch_path}")
            return

        # --- Read target file from header BEFOREHAND ---
        with open(patch_path, 'r') as f:
            header = f.readline()
        if not header.startswith('--- target: '):
            logging.error(f"Operarius: Invalid patch header in {patch_path}. Quarantining.")
            self.quarantine(patch_path)
            return
        target_file = header.split('--- target: ')[1].strip()
        # ----------------------------------------------

        # --- The Atomic Operation Block ---
        temp_backup_path = target_file + ".scribo_bak"
        shutil.copy(target_file, temp_backup_path)
        logging.info("Probator: Created temporary backup of original file.")

        if not perfice_resarcio(patch_path):
            logging.error(f"Operarius: Failed to apply patch. Reverting and quarantining.")
            self.revert_and_quarantine(target_file, temp_backup_path, patch_path)
            return

        self.run_ornator(target_file)

        if not run_tests(target_file):
            logging.error(f"Operarius: Tests failed. Reverting and quarantining.")
            self.revert_and_quarantine(target_file, temp_backup_path, patch_path)
            return

        # --- Success Condition ---
        os.remove(temp_backup_path) # Commit the change by removing the backup
        os.remove(patch_path)
        logging.info("Operarius: Mutatis mutandis. Scriptor has perfected and verified the file.")
    
    def revert_and_quarantine(self, target, backup, patch):
        """Restores the original file and quarantines the patch."""
        try:
            shutil.move(backup, target)
            self.quarantine(patch)
            logging.info("Probator: Reversion successful.")
        except Exception as e:
            logging.critical(f"PROBATOR: CRITICAL FAILURE. Could not restore backup {backup} to {target}. Manual intervention required. Error: {e}")

    def quarantine(self, patch_path):
        """Moves a patch file to the quarantine directory."""
        if os.path.exists(patch_path):
            shutil.move(patch_path, os.path.join(QUARANTINE_DIR, os.path.basename(patch_path)))

    def run_ornator(self, target_file):
        """Ornator: The Arranger. Runs formatters on the target file."""
        logging.info(f"Ornator: Formatting '{os.path.basename(target_file)}'...")
        try:
            venv_bin_dir = os.path.dirname(sys.executable)
            black_path = os.path.join(venv_bin_dir, "black")
            ruff_path = os.path.join(venv_bin_dir, "ruff")
            subprocess.run([black_path, target_file], check=True, capture_output=True, text=True)
            subprocess.run([ruff_path, "check", "--fix", target_file], check=True, capture_output=True, text=True)
            logging.info("Ornator: Formatting complete.")
        except Exception as e:
            logging.warning(f"Ornator: Formatting failed for '{target_file}'. Details: {e}")

# --- Main Execution Block ---
def main():
    setup_logging()
    logging.info("--- Speculator v3.0 ---")

    os.makedirs(SCRIBO_INBOX, exist_ok=True)
    os.makedirs(QUARANTINE_DIR, exist_ok=True)
    
    work_queue = queue.Queue()
    
    # Start the consumer thread (Operarius)
    worker = Operarius(work_queue)
    worker.start()

    # Start the producer (Observer/PatchHandler)
    event_handler = PatchHandler(work_queue)
    observer = Observer()
    observer.schedule(event_handler, SCRIBO_INBOX, recursive=False)
    observer.start()
    
    logging.info(f"System online. Observing for patch files in: {SCRIBO_INBOX}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Shutdown signal received. Cleaning up.")
        observer.stop()
        work_queue.put(None) # Signal the worker to exit
    
    observer.join()
    worker.join() # Wait for the worker to finish its current task
    logging.info("Speculator stopped.")

if __name__ == "__main__":
    main()
