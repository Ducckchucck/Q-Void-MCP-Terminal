

from scapy.all import sniff, IP, TCP, UDP, ICMP
from collections import defaultdict
import os
import platform
import threading
import time
import socket
import joblib
import random


THRESHOLD = 10
BLOCK_DURATION = 60
LOG_FILE = "ddos_log.txt"
#UDP_ALERT_IP = "192.168.7.3"
UDP_ALERT_PORT = 5555
MODEL_PATH = "cyrus_ai_model.pkl"
SCALER_PATH = "scaler.pkl"


ping_requests = defaultdict(int)
blocked_ips = {}
model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)


def alert_system():
    if platform.system() == "Windows":
        import winsound
        winsound.Beep(1000, 500)
    else:
        os.system('echo -e "\a"')

def log_attack(ip):
    with open(LOG_FILE, "a") as log:
        log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Blocked IP: {ip}\n")

def block_ip(ip):
    if ip in blocked_ips:
        return

    print(f"🚨 Blocking IP: {ip}")
    if platform.system() == "Windows":
        rule_name = f"Block {ip}"
        os.system(f'netsh advfirewall firewall add rule name="{rule_name}" dir=in action=block remoteip={ip}')
    else:
        os.system(f"sudo iptables -A INPUT -s {ip} -j DROP")

    blocked_ips[ip] = time.time()
    log_attack(ip)
    alert_system()

def unblock_ips():
    while True:
        current_time = time.time()
        for ip in list(blocked_ips.keys()):
            unblock_time = blocked_ips[ip] + random.randint(30, BLOCK_DURATION)
            if current_time > unblock_time:
                print(f"✅ Unblocking IP: {ip}")
                if platform.system() == "Windows":
                    rule_name = f"Block {ip}"
                    os.system(f'netsh advfirewall firewall delete rule name="{rule_name}"')
                else:
                    os.system(f"sudo iptables -D INPUT -s {ip} -j DROP")
                blocked_ips.pop(ip, None)
        time.sleep(5)


def extract_features(packet):
    try:
        proto = 1 if packet.haslayer(ICMP) else 6 if packet.haslayer(TCP) else 17 if packet.haslayer(UDP) else 0
        pkt_len = len(packet)
        src_port = packet.sport if hasattr(packet, 'sport') else 0
        dst_port = packet.dport if hasattr(packet, 'dport') else 0
        return [proto, pkt_len, src_port, dst_port]
    except Exception as e:
        print(f"❌ Feature extraction error: {e}")
        return None


def detect_ddos(packet):
    if not packet.haslayer(IP):
        return

    ip_src = packet[IP].src
    if ip_src in blocked_ips:
        return

    
    features = extract_features(packet)
    if features:
        try:
            scaled_features = scaler.transform([features])
            prediction = model.predict(scaled_features)

            if prediction[0] == 1:
                print(f"🤖 AI Detected Attack from {ip_src}")
                block_ip(ip_src)
            else:
                print(f"✅ Safe packet from {ip_src}")
        except Exception as e:
            print(f"❌ Prediction error: {e}")


def start_sniffing():
    sniff(filter="icmp or tcp or udp", prn=detect_ddos, store=0)

unblock_thread = threading.Thread(target=unblock_ips, daemon=True)
unblock_thread.start()

sniffing_thread = threading.Thread(target=start_sniffing)
sniffing_thread.start()

print("🔍 AI-Enhanced Defense tool is running. Press Ctrl+C to stop.")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n🛑 Stopping network monitoring...")
