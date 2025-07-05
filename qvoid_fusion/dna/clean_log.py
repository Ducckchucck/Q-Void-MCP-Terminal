# clean_log.py
import json
from dna import sanitize_verdict  # make sure this is imported

with open("logs/threat_log.jsonl", "r", encoding="utf-8") as f:
    lines = f.readlines()

with open("logs/threat_log.jsonl", "w", encoding="utf-8") as f:
    for line in lines:
        data = json.loads(line)
        data["verdict"] = sanitize_verdict(str(data.get("verdict", "UNKNOWN")))
        f.write(json.dumps(data) + "\n")
