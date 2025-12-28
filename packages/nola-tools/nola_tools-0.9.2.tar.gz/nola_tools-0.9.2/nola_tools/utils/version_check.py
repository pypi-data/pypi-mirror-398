import urllib.request
import json
import os
import time
from datetime import datetime, timedelta

def get_latest_version(package_name):
    url = f"https://pypi.org/pypi/{package_name}/json"
    try:
        with urllib.request.urlopen(url, timeout=1) as response:
            data = json.loads(response.read().decode())
            return data['info']['version']
    except Exception:
        return None

def check_version(current_version, home_dir):
    if "dev" in current_version:
        return

    # Check only once per day
    last_check_file = os.path.join(home_dir, '.last_version_check')
    
    now = time.time()
    if os.path.exists(last_check_file):
        with open(last_check_file, 'r') as f:
            try:
                last_check = float(f.read().strip())
                if now - last_check < 86400: # 24 hours
                    return
            except ValueError:
                pass

    latest_version = get_latest_version('nola-tools')
    if latest_version:
        # Update last check time
        with open(last_check_file, 'w') as f:
            f.write(str(now))
        
        if latest_version != current_version:
            print(f"\033[33m* A new version of nola-tools is available: {latest_version} (current: {current_version})\033[0m")
            print(f"\033[33m* To upgrade, run: pip install --upgrade nola-tools\033[0m\n")
