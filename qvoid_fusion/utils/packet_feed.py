import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scapy.all import sniff, Raw, IP
from qvoid_fusion.mcp.router import route
from datetime import datetime
import threading
import time

LOG_PATH = "logs/.qvoidlog"


def colored(text, color="green"):
    colors = {
        "green": "\033[92m",
        "red": "\033[91m",
        "yellow": "\033[93m",
        "cyan": "\033[96m",
        "blue": "\033[94m",
        "reset": "\033[0m"
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"


def log_packet(payload, verdict, confidence, plugins=None, src_ip="unknown"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {src_ip} ➤ '{payload[:50]}...' → {verdict.upper()} ({confidence}%)"

    if plugins:
        for p in plugins:
            if "report" in p:
                log_line += f"\n[PLUGIN:{p['plugin']}] 📋\n{p['report']}\n"
            elif "error" in p:
                log_line += f"\n[PLUGIN:{p['plugin']}] ❌ Error: {p['error']}\n"

    print(colored(f"\n🧾 Log ➤ {log_line}", "cyan"))
    with open(LOG_PATH, "a", encoding="utf-8") as log:
        log.write(log_line + "\n")


def handle_packet(pkt):
    print(f"\n📡 Packet: {pkt.summary()}")
    if Raw in pkt:
        try:
            payload = pkt[Raw].load.decode(errors="ignore").strip()
            if not payload:
                print(colored("[!!] Empty payload. Skipped.", "yellow"))
                return

            src_ip = pkt[IP].src if IP in pkt else "unknown"
            result = route({
                "text": payload,
                "src_ip": src_ip
            })

            verdict = result.get("verdict", "unknown")
            confidence = result.get("confidence", 0)
            plugins = result.get("plugins", [])

            if isinstance(confidence, str):
                confidence = 0

            if confidence >= 50:
                print(colored(f"[🧠] Verdict: {verdict.upper()}, Confidence: {confidence}%", "green"))
                print(colored("[!!] Threat exceeds threshold! Logging alert.\n", "red"))
                log_packet(payload, verdict, confidence, plugins, src_ip)
            else:
                print(colored("[🧠] Verdict: benign or low confidence", "yellow"))
        except Exception as e:
            print(colored(f"[ERROR] Could not decode/analyze packet: {e}", "red"))
    else:
        print(colored("[!!] No data payload to analyze.", "cyan"))


def start_sniff(count=10):
    print(colored("\n🚦 Starting live packet scan (batch of 10)...\n", "blue"))
    sniff(count=count, prn=handle_packet, store=0)
    print(colored("\n🛑 Sniffing complete. Type 'sniff' again for next 10 packets.\n", "cyan"))


def auto_sniff_loop(batch_size=10, delay=10):
    while True:
        print(colored("\n⏳ Auto-Sniff Daemon Running...", "cyan"))
        sniff(count=batch_size, prn=handle_packet, store=0)
        print(colored(f"🛑 Batch done. Waiting {delay}s before next...\n", "yellow"))
        time.sleep(delay)


def start_auto_sniff_daemon(batch_size=10, delay=10):
    thread = threading.Thread(target=auto_sniff_loop, args=(batch_size, delay), daemon=True)
    thread.start()
    print(colored(f"✅ Auto-sniff daemon launched (batch={batch_size}, delay={delay}s)\n", "green"))
