#!/usr/bin/env python3
import psutil
import pynvml
import subprocess
import logging
import json
import os
import re
import time
import sys
import socket
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(filename='/tmp/sm_score_error.log', level=logging.WARNING, format='%(asctime)s: %(message)s')
CONFIG_FILE = '/tmp/sm_gpu_config.json'
FAILURE_CACHE = '/tmp/sm_gpu_failure_cache.txt'
DMESG_OOM_PATTERN = re.compile(r'Out of memory|oom-kill')
LAST_ALERT_FILE = '/home/isidore/system_maneuverability/sm_alert_cooldown.txt'
ALERT_COOLDOWN = 3600

training_mode = len(sys.argv) > 1 and sys.argv[1] == '--training'

gpu_tool = 'none'
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        gpu_tool = config.get('gpu_tool', 'none')
        logging.info(f"Using GPU tool: {gpu_tool}")
    except Exception as e:
        logging.warning(f"Failed to read GPU config: {e}")

def should_log_failure(tool):
    if not os.path.exists(FAILURE_CACHE):
        return True
    try:
        with open(FAILURE_CACHE, 'r') as f:
            last_failure = f.read().strip()
        last_time, last_tool = last_failure.split(',')
        last_time = int(last_time)
    except (ValueError, IndexError):
        last_time, last_tool = 0, ''
    current_time = int(time.time())
    return last_tool != tool or (current_time - last_time) > 86400

def log_failure(tool, message):
    if should_log_failure(tool):
        logging.warning(message)
        with open(FAILURE_CACHE, 'w') as f:
            f.write(f"{int(time.time())},{tool}")

def get_gpu_utilization():
    if gpu_tool == 'none':
        return 0
    if gpu_tool == 'radeontop':
        try:
            result = subprocess.run(['sudo', 'radeontop', '-d', '-', '-l', '1'], capture_output=True, text=True, check=True, timeout=5)
            for line in result.stdout.splitlines():
                match = re.search(r'gpu\s+(\d+\.\d+)%', line)
                if match:
                    return int(float(match.group(1)))
            log_failure('radeontop', "No valid gpu percentage found")
        except Exception as e:
            log_failure('radeontop', f"Error: {e}")
        return 0
    elif gpu_tool == 'intel_gpu_top':
        try:
            result = subprocess.run(['sudo', 'intel_gpu_top', '-s', '1', '-o', 'csv'], capture_output=True, text=True, check=True, timeout=5)
            for line in result.stdout.splitlines()[1:]:
                fields = line.split(',')
                if len(fields) > 2:
                    return int(float(fields[2]))
            log_failure('intel_gpu_top', "No valid CSV data")
        except Exception as e:
            log_failure('intel_gpu_top', f"Error: {e}")
        return 0
    elif gpu_tool == 'nvidia-smi':
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader'], capture_output=True, text=True, check=True)
            util = int(result.stdout.strip().replace('%', ''))
            return util
        except Exception as e:
            log_failure('nvidia-smi', f"Error: {e}")
        return 0
    return 0

def get_inference_rate():
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    session.mount('http://', HTTPAdapter(max_retries=retries))
    try:
        response = session.head('http://localhost:11434', timeout=5)
        if response.status_code == 200:
            return 1  # Server active
        return 0
    except Exception as e:
        logging.warning(f"Failed to get inference rate: {e}")
        return 0

def get_thermal_penalty():
    crit_temp = 95.0
    warn_temp = 70.0
    max_penalty = 40.0
    temps = psutil.sensors_temperatures()
    high_temp = 0.0
    for key, sensors in temps.items():
        for sensor in sensors:
            if sensor.current > high_temp:
                high_temp = sensor.current
                logging.info(f"Temperature ({key}-{sensor.label}): {high_temp}°C")
    if high_temp > crit_temp:
        return max_penalty
    elif high_temp > warn_temp:
        return ((high_temp - warn_temp) / (crit_temp - warn_temp)) * max_penalty
    return 0

def detect_crash_penalty():
    try:
        dmesg = subprocess.run(['sudo', 'dmesg', '-T'], capture_output=True, text=True).stdout
        if DMESG_OOM_PATTERN.search(dmesg[-2000:]):
            logging.warning("Detected potential OOM/crash")
            return 50
    except Exception:
        pass
    return 0

def calculate_sm_score():
    score = 100
    penalties = {}
    cpu_util = psutil.cpu_percent(interval=2)
    penalties['cpu'] = (cpu_util / 100) * 30
    penalties['gpu'] = (get_gpu_utilization() / 100) * 30
    swap = psutil.swap_memory()
    penalties['memory_swap'] = (swap.percent / 100) * 5 if swap.percent > 80 else 0
    penalties['thermal'] = get_thermal_penalty()
    iowait = psutil.cpu_times_percent(interval=2).iowait
    penalties['iowait'] = (iowait / 100) * 20
    mem_util = psutil.virtual_memory().percent
    penalties['memory_util'] = ((mem_util - 80.0) / 20.0) * 10 if mem_util > 80.0 else 0
    penalties['crash'] = detect_crash_penalty()
    net_io = psutil.net_io_counters()
    net_bytes = net_io.bytes_sent + net_io.bytes_recv
    inference_rate = get_inference_rate()
    
    if training_mode:
        for key in penalties:
            penalties[key] /= 2
    
    total_penalty = sum(penalties.values())
    final_score = int(max(0, score - total_penalty))
    
    logging.warning(f"SM Score: {final_score}, CPU Util: {cpu_util}%, Mem Util: {mem_util}%, IOWait: {iowait}%, Swap: {swap.percent}%, Net Bytes: {net_bytes}, Inference Rate: {inference_rate}, Penalties: {penalties}")
    
    if final_score < 20:
        try:
            if os.path.exists(LAST_ALERT_FILE):
                with open(LAST_ALERT_FILE, 'r') as f:
                    last_alert = int(f.read().strip())
                if time.time() - last_alert < ALERT_COOLDOWN:
                    logging.info(f"Skipping ntfy alert due to cooldown (last sent: {last_alert})")
                    return final_score
            result = subprocess.run(['curl', '-s', '-H', f'Title: 🚨 System Alert on {socket.gethostname()}',
                                    '-d', f'SM Score: {final_score}, CPU: {cpu_util}%, Penalties: {penalties}',
                                    'https://ntfy.sh/roma'], capture_output=True, text=True, check=True)
            logging.info(f"ntfy alert sent: {result.stdout}")
            with open(LAST_ALERT_FILE, 'w') as f:
                f.write(str(int(time.time())))
        except Exception as e:
            logging.warning(f"ntfy alert failed: {e}")
    
    logging.info(f"SM Score: {final_score}, Penalties: {penalties}, Training Mode: {training_mode}")
    return final_score

if __name__ == "__main__":
    print(calculate_sm_score())
