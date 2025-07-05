import os
import platform
import threading
import time
import socket
import random
import json
import logging
from collections import defaultdict
from datetime import datetime
from scapy.all import sniff, IP, ICMP

import sys


THRESHOLD = 10
BLOCK_DURATION = 60
LOG_FILE = "ddos_log.txt"
UDP_ALERT_IP = "192.168.7.3"
UDP_ALERT_PORT = 5555


logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(message)s')


ping_requests = defaultdict(int)
blocked_ips = {}
running = True
DEMO_MODE = "--demo" in sys.argv


def alert_system():
    if platform.system() == "Windows":
        import winsound
        winsound.Beep(1000, 500)
    else:
        os.system('echo -e "\a"')


def log_attack(ip):
    with open(LOG_FILE, "a") as log:
        log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Blocked IP: {ip}\n")


def send_udp_alert(message):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(message.encode(), (UDP_ALERT_IP, UDP_ALERT_PORT))
        sock.close()
        print(f"📡 Sent alert to {UDP_ALERT_IP}:{UDP_ALERT_PORT}")
    except Exception as e:
        print(f"⚠️ Failed to send UDP alert: {e}")


def block_ip(ip):
    print(f"🚨 Blocking IP: {ip}")
    if platform.system() == "Windows":
        rule_name = f"Block {ip}"
        os.system(f'netsh advfirewall firewall add rule name="{rule_name}" dir=in action=block remoteip={ip}')
    else:
        os.system(f"sudo iptables -A INPUT -s {ip} -j DROP")
    blocked_ips[ip] = time.time()
    log_attack(ip)
    send_udp_alert(f"🚨 DDoS Attack Detected from {ip} 🚨")


def unblock_ips():
    while running:
        current_time = time.time()
        for ip in list(blocked_ips.keys()):
            if current_time > blocked_ips[ip] + random.randint(30, BLOCK_DURATION):
                print(f"✅ Unblocking IP: {ip}")
                if platform.system() == "Windows":
                    rule_name = f"Block {ip}"
                    os.system(f'netsh advfirewall firewall delete rule name="{rule_name}"')
                else:
                    os.system(f"sudo iptables -D INPUT -s {ip} -j DROP")
                blocked_ips.pop(ip, None)
        time.sleep(5)


def create_sandbox(ip, pkt):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sandbox_dir = f"sandbox_logs/{ip}_{timestamp}"
    os.makedirs(sandbox_dir, exist_ok=True)
    with open(f"{sandbox_dir}/packet_info.txt", "w") as f:
        f.write(f"Suspicious activity from IP: {ip}\n\n")
        f.write("Packet Summary:\n")
        f.write(str(pkt.summary()) + "\n")
        f.write("Raw Bytes:\n")
        f.write(str(bytes(pkt)))
    print(f"🧪 [Sandbox] Created at: {sandbox_dir}")


def save_forensic_snapshot(ip, prediction, pkt):
    snapshot = {
        "ip": ip,
        "timestamp": datetime.now().isoformat(),
        "prediction": prediction,
        "packet_summary": pkt.summary(),
        "raw_bytes": str(bytes(pkt))
    }
    os.makedirs("forensic_snapshots", exist_ok=True)
    snap_file = f"forensic_snapshots/{ip}_{datetime.now().strftime('%H%M%S')}.qvoidlog"
    with open(snap_file, "w") as f:
        json.dump(snapshot, f, indent=4)
    print(f"📸 [Snapshot] Saved: {snap_file}")


def detect_ddos(pkt):
    try:
        if pkt.haslayer(ICMP):
            ip_src = pkt[IP].src
            if ip_src in blocked_ips:
                return
            ping_requests[ip_src] += 1

            if ping_requests[ip_src] > THRESHOLD:
                alert_system()
                block_ip(ip_src)
                logging.info(f"DDoS Detected from {ip_src}")
                create_sandbox(ip_src, pkt)
                save_forensic_snapshot(ip_src, "malicious", pkt)
            else:
                print(f"✅ Normal ping from {ip_src}")
                logging.info(f"Normal ping from {ip_src}")
    except Exception as e:
        print(f"Error in detection logic: {e}")
        logging.error(f"Error in detection logic: {e}")


def simulate_attack():
    from scapy.all import IP, ICMP, send
    for _ in range(15):
        pkt = IP(src="1.2.3.4", dst="127.0.0.1") / ICMP()
        detect_ddos(pkt)
        time.sleep(0.2)


def start_sniffing():
    print("📡 Starting packet detection on interface: Wi-Fi")
    sniff(filter="icmp", prn=detect_ddos, store=0, stop_filter=lambda x: not running)


def listen_for_exit():
    global running
    while running:
        cmd = input()
        if cmd.strip() == "exit()":
            running = False
            print("🛑 Exit command received. Stopping...")


if __name__ == "__main__":
    print("🔍 QVoid Defense System is live. Type exit() to stop.")

    threading.Thread(target=unblock_ips, daemon=True).start()

    if DEMO_MODE:
        print("🎥 Demo mode ON — Simulating fake attack...")
        simulate_attack()
        running = False
    else:
        threading.Thread(target=start_sniffing).start()
        listen_for_exit()
