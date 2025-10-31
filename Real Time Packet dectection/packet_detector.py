from scapy.all import sniff, get_if_list, wrpcap, IP
import Defense_script as ds
import threading
import time
import os


import os

# Store RTPI PID
pid_file = os.path.join("logs", "rtpi.pid")
os.makedirs("logs", exist_ok=True)
with open(pid_file, "w") as f:
    f.write(str(os.getpid()))


INTERFACE = "Wi-Fi"
running = True

def pkt_call(pkt):
    try:
        print(pkt.summary())
        wrpcap("pack.pcap", pkt, append=True)
        ds.detect_ddos(pkt)

        
        if pkt.haslayer(IP) and pkt[IP].src == "1.2.3.4":
            ds.create_sandbox(pkt[IP].src, pkt)
            ds.save_forensic_snapshot(pkt[IP].src, "malicious", pkt)

    except Exception as e:
        print(f"⚠️ Error processing packet: {e}")

def start_sniffing():
    global running
    while running:
        try:
            sniff(
                iface=INTERFACE,
                prn=pkt_call,
                count=10,
                store=True,
                stop_filter=lambda x: not running
            )
            time.sleep(3)
            open("pack.pcap", "w").close()
        except Exception as e:
            print(f"⚠️ Sniffing error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    print(f"📡 Starting packet detection on interface: {INTERFACE}")
    print("🔍 Press Ctrl+C to stop detection and terminate.")
    try:
        sniff_thread = threading.Thread(target=start_sniffing)
        sniff_thread.start()
        sniff_thread.join()
    except KeyboardInterrupt:
        print("\n🛑 Exit signal received. Stopping packet capture...")
        running = False
        time.sleep(2)
    finally:
        print("✅ Packet detector stopped.")
