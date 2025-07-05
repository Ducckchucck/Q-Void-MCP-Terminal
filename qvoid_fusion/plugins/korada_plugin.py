import socket
import requests
import subprocess
import os
import ssl
import datetime
from OpenSSL import crypto
import sys

class QVoidPlugin:
    def init(self, config=None): pass
    def run(self, input_data): pass
    def report(self): pass
    def cleanup(self): pass

class KoradaModulePlugin(QVoidPlugin):
    def __init__(self):
        self.name = "KoradaModulePlugin"
        self.version = "1.0"
        self.description = "Security audit plugin with scanning, vulnerability checks, and flaw detection"
        self.latest_report = ""
        requests.packages.urllib3.disable_warnings()

    def init(self, config=None):
        pass

    def run(self, input_data):
        target = input_data.get("target")
        ports = input_data.get("ports") or [
            20, 21, 22, 23, 25, 53, 69, 80, 123, 143, 161, 169,
            179, 443, 500, 587, 8080, 8081, 3306, 3389
        ]

        open_ports = self.check_open_ports(target, ports)
        service_versions = self.check_service_versions(target, open_ports)
        vulnerabilities = self.check_vulnerabilities(service_versions)
        flaws = self.check_security_flaws(target, open_ports)

        self.latest_report = self.generate_report(
            target, open_ports, service_versions, vulnerabilities, flaws
        )
        return self.latest_report

    def report(self):
        return self.latest_report

    def cleanup(self):
        pass

    def check_open_ports(self, host, ports):
        open_ports = []
        for port in ports:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(1)
                    result = sock.connect_ex((host, port))
                    if result == 0:
                        try:
                            service_name = socket.getservbyport(port, 'tcp')
                        except OSError:
                            service_name = "unknown"
                        open_ports.append((port, service_name))
            except Exception as e:
                print(f"[!] Error scanning port {port}: {str(e)}", file=sys.stderr)
        return open_ports

    def get_ssh_banner(self, host, port=22, timeout=3):
        try:
            with socket.create_connection((host, port), timeout=timeout) as sock:
                banner = sock.recv(1024).decode(errors='ignore').strip()
                return banner.split('\n')[0] if banner else "SSH (no banner)"
        except Exception:
            return "SSH (no response)"

    def check_service_versions(self, host, open_ports):
        service_versions = {}
        for port, service_name in open_ports:
            try:
                if port in [80, 443, 8080, 8443]:
                    protocol = 'https' if port in [443, 8443] else 'http'
                    url = f"{protocol}://{host}:{port}"
                    response = requests.get(url, timeout=3, verify=False)
                    server_header = response.headers.get('Server', 'Unknown')
                    service_versions[port] = server_header
                elif port == 22:
                    service_versions[port] = self.get_ssh_banner(host, port)
                else:
                    service_versions[port] = f"{service_name} (no version detection)"
            except Exception as e:
                service_versions[port] = f"Error: {str(e)}"
        return service_versions

    def check_vulnerabilities(self, service_versions):
        VULNERABILITY_DB = {
            'Apache': {
                'vulnerable_versions': ['2.4.41', '2.4.39', '2.4.38', '2.4.37'],
                'cves': ['CVE-2021-42013', 'CVE-2021-41773']
            },
            'nginx': {
                'vulnerable_versions': ['1.16.0', '1.15.12', '1.14.2'],
                'cves': ['CVE-2021-23017', 'CVE-2020-12440']
            },
            'OpenSSH': {
                'vulnerable_versions': ['8.4p1', '8.3p1', '7.9p1'],
                'cves': ['CVE-2021-41617', 'CVE-2020-14145']
            },
            'Microsoft-IIS': {
                'vulnerable_versions': ['10.0.15063', '8.5'],
                'cves': ['CVE-2017-7269', 'CVE-2015-1635']
            }
        }

        vulnerabilities = []
        for port, version in service_versions.items():
            for service, data in VULNERABILITY_DB.items():
                if service in version:
                    for vuln_version in data['vulnerable_versions']:
                        if vuln_version in version:
                            cve_list = ', '.join(data['cves'])
                            vulnerabilities.append(
                                f"Port {port}: Vulnerable {service} version ({version}) - {cve_list}"
                            )
        return vulnerabilities

    def check_security_flaws(self, host, open_ports):
        flaws = []
        try:
            if any(port == 22 for port, _ in open_ports):
                if os.path.exists('/etc/ssh/sshd_config'):
                    with open('/etc/ssh/sshd_config', 'r') as f:
                        sshd_config = f.read()
                        if 'PermitRootLogin yes' in sshd_config:
                            flaws.append('SSH root login enabled (CWE-250)')
                        if 'PasswordAuthentication yes' in sshd_config:
                            flaws.append('SSH password authentication enabled (CWE-798)')
                else:
                    flaws.append('SSH configuration file not found')
        except Exception as e:
            flaws.append(f'SSH config check failed: {str(e)}')

        try:
            if os.name == 'posix':
                result = subprocess.run(['ufw', 'status'], capture_output=True, text=True)
                if 'inactive' in result.stdout.lower():
                    flaws.append('Firewall is inactive')
            elif os.name == 'nt':
                result = subprocess.run(
                    ['netsh', 'advfirewall', 'show', 'allprofiles'],
                    capture_output=True,
                    text=True
                )
                if 'OFF' in result.stdout:
                    flaws.append('Windows Firewall is inactive')
        except Exception as e:
            flaws.append(f'Firewall check failed: {str(e)}')

        for port, _ in open_ports:
            if port in [443, 8443]:
                try:
                    cert = ssl.get_server_certificate((host, port))
                    x509 = crypto.load_certificate(crypto.FILETYPE_PEM, cert)
                    expiry_bytes = x509.get_notAfter()
                    if expiry_bytes:
                        expiry = datetime.datetime.strptime(expiry_bytes.decode('utf-8'), '%Y%m%d%H%M%SZ')
                        if expiry < datetime.datetime.utcnow():
                            flaws.append(f"Expired SSL certificate on port {port}")
                except Exception as e:
                    flaws.append(f"SSL check failed on port {port}: {str(e)}")
        return flaws

    def generate_report(self, target, open_ports, service_versions, vulnerabilities, flaws):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ports_section = "✅ No open ports detected\n" if not open_ports else "\n".join(
            f"- 🔓 Port `{port}` ({service})" for port, service in open_ports
        )
        versions_section = "\n".join(
            f"- Port `{port}`: {version}" for port, version in service_versions.items()
        ) if service_versions else "No service versions detected"
        vuln_section = "✅ No vulnerabilities detected\n" if not vulnerabilities else "\n".join(
            f"- 🔥 {vuln}" for vuln in vulnerabilities
        )
        flaws_section = "✅ No security flaws detected\n" if not flaws else "\n".join(
            f"- ⚠️ {flaw}" for flaw in flaws
        )
        return f"""
## 🔒 Security Audit Report
**Target:** `{target}`  
**Scan Date:** {timestamp}  
**Generated By:** KoradaModulePlugin v1.0

### 📡 Open Ports
{ports_section}

### 🔍 Service Versions
{versions_section}

### 🚨 Identified Vulnerabilities
{vuln_section}

### ⚠️ Security Flaws
{flaws_section}
"""

def get_plugin():
    return KoradaModulePlugin()
