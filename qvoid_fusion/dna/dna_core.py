import json
import os
from datetime import datetime

# ✅ Verdict mapping cleanup
def sanitize_verdict(verdict):
    mapping = {
        -1: "PHISHING",
        0: "BENIGN",
        1: "MALWARE",
        2: "SQL_INJECTION",
        3: "SYN_ATTACK",
        4: "PHISHING",
        "Normal": "SYN_ATTACK",
        "normal": "SYN_ATTACK",
        "Benign": "BENIGN",
        "benign": "BENIGN",
        "BENIGN": "BENIGN",
        "UNKNOWN": "UNKNOWN",
        "unknown": "UNKNOWN",
        "Malware": "MALWARE",
        "malware": "MALWARE",
        "sql": "SQL_INJECTION",
        "Sql": "SQL_INJECTION",
        "PHISHING": "PHISHING"
    }
    return mapping.get(str(verdict), str(verdict).upper())

# ✅ Log file setup
DNA_LOG_PATH = "logs/threat_log.jsonl"
os.makedirs("logs", exist_ok=True)
if not os.path.exists(DNA_LOG_PATH):
    with open(DNA_LOG_PATH, "w", encoding="utf-8") as f:
        pass

# ✅ DNA Logger Class
class QVoidDNA:
    def __init__(self):
        self.memory_file = DNA_LOG_PATH

    def store_event(self, data):
        """Store a threat or input scan result in the DNA memory log"""
        try:
            raw_verdict = data.get("verdict", "UNKNOWN")
            clean_verdict = sanitize_verdict(raw_verdict)
            data["verdict"] = clean_verdict
            data["timestamp"] = datetime.now().isoformat()

            json_ready = {
                k: int(v) if isinstance(v, bool)
                else str(v) if isinstance(v, (bytes, bytearray))
                else v
                for k, v in data.items()
            }

            with open(self.memory_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(json_ready) + "\n")

        except Exception as e:
            print(f"[!!] Logging error: {e}")

    def count_logs(self):
        """Count total log entries"""
        try:
            with open(self.memory_file, "r", encoding="utf-8") as f:
                return sum(1 for _ in f if _.strip())
        except:
            return 0

    def clear(self):
        """Clear memory log"""
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                f.write("")
        except Exception as e:
            print(f"[!!] Clear error: {e}")

    def search_memory(self, keyword):
        """Return all memory events that match a given keyword"""
        results = []
        try:
            with open(self.memory_file, "r", encoding="utf-8") as f:
                for line in f:
                    if keyword.lower() in line.lower():
                        results.append(json.loads(line))
        except Exception:
            pass
        return results

    def full_dump(self):
        """Dump the entire memory"""
        try:
            with open(self.memory_file, "r", encoding="utf-8") as f:
                return [json.loads(line) for line in f if line.strip()]
        except Exception:
            return []

    def stats(self):
        """Return verdict counts, all sanitized"""
        all_entries = self.full_dump()
        verdict_counts = {}
        for entry in all_entries:
            verdict = sanitize_verdict(entry.get("verdict", "UNKNOWN"))
            verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1
        return verdict_counts
