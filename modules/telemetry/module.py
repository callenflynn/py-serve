import json
import os
from datetime import datetime


def run(ip_address):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.join(base_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    log_file = os.path.join(logs_dir, f"{date_str}.json")

    entry = {"timestamp": time_str, "ip": ip_address}

    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")