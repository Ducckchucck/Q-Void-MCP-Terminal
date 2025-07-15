import os
import re
import platform
from termcolor import colored

# Common malware file indicators
SUSPICIOUS_PATTERNS = [
    # Keywords commonly in malware filenames
    r'(?i)keylogger',
    r'(?i)rat',
    r'(?i)backdoor',
    r'(?i)autorun\.inf',
    r'(?i)hacktool',
    r'(?i)ransom',
    r'(?i)ransomware',
    r'(?i)injector',
    r'(?i)exploit',
    r'(?i)trojan',
    r'(?i)rootkit',
    r'(?i)logger',
    r'(?i)sniffer',
    r'(?i)phisher',
    r'(?i)payload',
    r'(?i)obfuscated',
    r'(?i)worm',
    r'(?i)dropper',
    r'(?i)botnet',
    r'(?i)shellcode',
    r'(?i)bindshell',
    r'(?i)persistence',
    r'(?i)malicious',
    r'(?i)reverse_shell',
    r'(?i)cmd_hack',
    r'(?i)portscan',
    r'(?i)socialengineer',
    r'(?i)crypto_miner',
    r'(?i)metasploit',
    r'(?i)scan_result',
    r'(?i)suspicious',

    # Suspicious file extensions (executable, scripting, autorun)
    r'(?i)\.exe$',
    r'(?i)\.vbs$',
    r'(?i)\.bat$',
    r'(?i)\.cmd$',
    r'(?i)\.scr$',
    r'(?i)\.js$',
    r'(?i)\.jar$',
    r'(?i)\.ps1$',    # PowerShell
    r'(?i)\.lnk$',    # Windows shortcut
    r'(?i)\.dll$',    # DLL (possible injected or rogue lib)
    r'(?i)\.bin$',    # Binary blob
    r'(?i)\.apk$',    # Android package
    r'(?i)\.py$',     # Python script
    r'(?i)\.sh$',     # Shell script
    r'(?i)\.hta$',    # HTML application

    # Heavily suspicious filenames (exact or close matches)
    r'(?i)virus',
    r'(?i)hacked',
    r'(?i)crack',
    r'(?i)keygen',
    r'(?i)unlocker',
    r'(?i)passwords',
    r'(?i)stealer',
    r'(?i)banking',
    r'(?i)wallet_backup',
    r'(?i)wallet.dat',
    r'(?i)decrypt_instructions',
    r'(?i)how_to_recover_files',
    r'(?i)readme_for_decryption',
    r'(?i)restore_your_data',
]


def list_usb_drives():
    if platform.system() == "Windows":
        from string import ascii_uppercase
        return [f"{d}:/" for d in ascii_uppercase if os.path.exists(f"{d}:/") and os.path.exists(f"{d}:/autorun.inf") or os.path.isdir(f"{d}:/")]
    elif platform.system() == "Linux":
        return [os.path.join("/media", user, d) for user in os.listdir("/media") for d in os.listdir(f"/media/{user}")]
    return []

def scan_usb_for_malware():
    usb_drives = list_usb_drives()
    if not usb_drives:
        print(colored("🔌 No USB drives detected.", "yellow"))
        return

    print(colored(f"\n💾 Detected USB drives: {usb_drives}", "cyan"))

    for drive in usb_drives:
        print(colored(f"\n🔍 Scanning USB: {drive}", "blue"))
        for root, dirs, files in os.walk(drive):
            for fname in files:
                fpath = os.path.join(root, fname)
                for pattern in SUSPICIOUS_PATTERNS:
                    if re.search(pattern, fname):
                        print(colored(f"[ALERT] Suspicious File: {fpath}", "red"))
                        break  # Skip further pattern checking on this file
        print(colored(f"✅ Scan complete for {drive}", "green"))
