# to run: python -m qvoid_fusion.core.main
# test: syn flood tcp overflow on 80, ' OR 0x61646D696E=0x61646D696E --, '; EXEC xp_cmdshell('whoami'); --
# test: scan 192.168.1.1
# test: sniff
# test: autosniff
# test: simulate attack
# test: dna stats

import warnings
warnings.filterwarnings("ignore")

from qvoid_fusion.mcp.router import route
from qvoid_fusion.core.config import CONFIG
from qvoid_fusion.qcrypt.qvoidcrypt_core import QVoidCrypt
from qvoid_fusion.dna.dna_core import QVoidDNA
from datetime import datetime
import os

LOG_PATH = "logs/.qvoidlog"
os.makedirs("logs", exist_ok=True)

qcrypt = QVoidCrypt()
dna = QVoidDNA()


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


def log_result(input_text, verdict, confidence):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] '{input_text}' → {verdict} ({confidence}%)"
    print(colored(f"🧾 Log ➤ {log_line}", "cyan"))
    with open(LOG_PATH, "a", encoding="utf-8") as log:
        log.write(log_line + "\n")


print(colored("\n🧠 QVoid MCP Defense Terminal (Post-Quantum Ready)\n", "green"))

while True:
    cmd = input(colored(" Enter input (or 'exit'): ", "yellow")).strip()

    if cmd.lower() == "exit":
        print(colored(" Exiting QVoid Terminal. Stay Secure.", "red"))
        break

    if cmd.lower() == "sniff":
        from qvoid_fusion.utils.packet_feed import start_sniff
        start_sniff(count=10)
        continue

    if cmd.lower() == "autosniff":
        from qvoid_fusion.utils.packet_feed import start_auto_sniff_daemon
        start_auto_sniff_daemon(batch_size=10, delay=15)
        continue

    if cmd.lower() == "simulate attack":
        from qvoid_fusion.utils.attack_simulator import (
            simulate_syn_flood,
            simulate_sql_injection_http,
            simulate_phishing_url
        )
        simulate_syn_flood()
        simulate_sql_injection_http()
        simulate_phishing_url()
        print(colored(" Attack simulation complete!", "red"))
        continue

    if cmd.lower().startswith("scan "):
        ip = cmd.split(" ")[1]
        try:
            print(colored(f"\n🔍 Running Korada plugin scan on: {ip} ...\n", "blue"))
            from qvoid_fusion.plugins.korada_plugin import get_plugin
            korada = get_plugin()
            result = korada.run({"target": ip})
            print(result)
        except Exception as e:
            print(colored(f"[ERROR] Korada plugin failed: {e}", "red"))
        continue

    if cmd.lower().startswith("dna search"):
        keyword = cmd.split(" ", 2)[-1]
        matches = dna.search_memory(keyword)
        if matches:
            print(colored(f"\n🔍 Found {len(matches)} matching threat records:\n", "blue"))
            for entry in matches:
                print(f" - [{entry['timestamp']}] {entry['input']} → {entry['verdict']} ({entry['confidence']}%)")
        else:
            print(colored(" No matching entries found.", "yellow"))
        continue

    if cmd.lower() == "dna stats":
        stats = dna.stats()
        print(colored("\n🧬 DNA Memory Stats:\n", "green"))
        for verdict, count in stats.items():
            print(f" - {verdict.upper()} ➤ {count}")
        continue

    try:
        encrypted_cmd, tag = qcrypt.encrypt_and_tag(cmd)

        print(colored("\n--- QVoidCrypt Encryption Layer ---", "blue"))
        print(f" AES Session Key : {qcrypt.session_key.hex()[:32]}...")
        print(f" Encrypted Blob  : {encrypted_cmd.hex()[:48]}...")
        print(f" HMAC Tag        : {tag.hex()}")
        print(colored(" Decrypting and Verifying...", "yellow"))

        decrypted_cmd = qcrypt.verify_and_decrypt(encrypted_cmd, tag)
        print(colored(f"✅ Decrypted Input : {decrypted_cmd}", "green"))
        print(colored("--- End QVoidCrypt Layer ---\n", "blue"))

        result = route(decrypted_cmd)
        verdict = result.get("verdict")
        confidence = result.get("confidence")

        if isinstance(confidence, (str, type(None))):
            print(colored(f"[✅] Verdict: {verdict}, Confidence: {confidence}%", "green"))
        else:
            if confidence >= CONFIG["confidence_threshold"]:
                print(colored(f"[✅] Verdict: {verdict}, Confidence: {confidence}%", "green"))
                print(colored("[!!] Threat exceeds threshold! Taking note.", "red"))
            else:
                print(colored(f"[✅] Verdict: {verdict}, Confidence: {confidence}%", "yellow"))
                print(colored("[!!] Confidence below threshold. Ignored.", "cyan"))

        # Log to flat file and DNA memory both
        log_result(decrypted_cmd, verdict, confidence)
        dna.store_event({
            "input": decrypted_cmd,
            "verdict": verdict,
            "confidence": confidence
        })

    except Exception as e:
        print(colored(f"[ ERROR] {e}", "red"))
