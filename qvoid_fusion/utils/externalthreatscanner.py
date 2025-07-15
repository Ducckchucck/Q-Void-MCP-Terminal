import os
import re
import time
import random
from datetime import datetime

# Suspicious patterns
SUSPICIOUS_PATTERNS = [
    r'(?i)keylogger',
    r'(?i)rat',
    r'(?i)backdoor',
    r'(?i)autorun\.inf',
    r'(?i)hacktool',
    r'(?i)ransom',
    r'(?i)injector',
    r'(?i)exploit',
    r'(?i)\.vbs$',
    r'(?i)\.exe$',
    r'(?i)\.bat$',
    r'(?i)\.scr$',
    r'(?i)decrypt',
    r'(?i)malicious',
    r'(?i)payload',
    r'(?i)trojan',
    r'(?i)virus',
    r'(?i)worm',
    r'(?i)spyware',
    r'(?i)stealer',
    r'(?i)snoop',
]

WATCH_DIR = "test_usb"  # Default USB scan directory

def scan_path(path):
    suspicious = []
    for root, _, files in os.walk(path):
        for file in files:
            for pattern in SUSPICIOUS_PATTERNS:
                if re.search(pattern, file):
                    suspicious.append(os.path.join(root, file))
                    break
    return suspicious

def log_detection(files):
    with open("logs/usb_threats.log", "a", encoding="utf-8") as f:
        f.write(f"\n[{datetime.now().isoformat()}] 🚨 Detected {len(files)} suspicious file(s):\n")
        for file in files:
            f.write(f" - {file}\n")

def start_monitor(path=WATCH_DIR, duration=60):
    print("📡 External Threat Scanner started (auto-scan mode).")
    start_time = time.time()

    while (time.time() - start_time) < duration:
        wait_time = random.randint(2, 5)
        time.sleep(wait_time)

        if os.path.exists(path):
            suspicious = scan_path(path)
            if suspicious:
                print(f"\n🚨 [{datetime.now().strftime('%H:%M:%S')}] Threat Detected in USB!\n")
                for s in suspicious:
                    print(f" - {s}")
                log_detection(suspicious)
            else:
                print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] No threats found.")
        else:
            print(f"⚠️ [{datetime.now().strftime('%H:%M:%S')}] USB path not found.")

    print("🛑 External Threat Scanner session ended.")

if __name__ == "__main__":
    start_monitor()
