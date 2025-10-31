import os
import re
from termcolor import colored

SUSPICIOUS_PATTERNS = [
    r'(?i)keylogger', r'(?i)rat', r'(?i)backdoor', r'(?i)autorun\.inf', r'(?i)hacktool',
    r'(?i)ransom', r'(?i)ransomware', r'(?i)injector', r'(?i)exploit', r'(?i)trojan',
    r'(?i)rootkit', r'(?i)logger', r'(?i)sniffer', r'(?i)phisher', r'(?i)payload',
    r'(?i)obfuscated', r'(?i)worm', r'(?i)dropper', r'(?i)botnet', r'(?i)shellcode',
    r'(?i)bindshell', r'(?i)persistence', r'(?i)malicious', r'(?i)reverse_shell',
    r'(?i)cmd_hack', r'(?i)portscan', r'(?i)socialengineer', r'(?i)crypto_miner',
    r'(?i)metasploit', r'(?i)scan_result', r'(?i)suspicious',
    r'(?i)\.exe$', r'(?i)\.vbs$', r'(?i)\.bat$', r'(?i)\.cmd$', r'(?i)\.scr$', r'(?i)\.js$',
    r'(?i)\.jar$', r'(?i)\.ps1$', r'(?i)\.lnk$', r'(?i)\.dll$', r'(?i)\.bin$', r'(?i)\.apk$',
    r'(?i)\.py$', r'(?i)\.sh$', r'(?i)\.hta$', r'(?i)virus', r'(?i)hacked', r'(?i)crack',
    r'(?i)keygen', r'(?i)unlocker', r'(?i)passwords', r'(?i)stealer', r'(?i)banking',
    r'(?i)wallet_backup', r'(?i)wallet.dat', r'(?i)decrypt_instructions',
    r'(?i)how_to_recover_files', r'(?i)readme_for_decryption', r'(?i)restore_your_data',
]

def scan_usb(path):
    print(colored(f"🔍 Scanning path: {path}", "cyan"))
    threats = []

    for root, dirs, files in os.walk(path):
        for file in files:
            full_path = os.path.join(root, file)
            for pattern in SUSPICIOUS_PATTERNS:
                if re.search(pattern, file):
                    threats.append(full_path)
                    break

    if threats:
        print(colored(f"\n⚠️ Suspicious files detected: {len(threats)}\n", "red"))
        for f in threats:
            print(colored(f" - {f}", "yellow"))
    else:
        print(colored("✅ No suspicious files found.", "green"))

# Run test
if __name__ == "__main__":
    scan_usb("test_usb")  # 🔁 replace with actual drive letter like "E:\\" when testing real USB
