from qvoid_fusion.models import (
    model_sql,
    model_syn,
    model_malware,
    model_phishing,
    model_cicids_friday,
    model_anomaly
)

from qvoid_fusion.plugins import registered_plugins
from qvoid_fusion.mcp.memory import DNAMemory
# from qvoid_fusion.qcrypt.qvoidcrypt_qkd import simulate_qkd_keypair  # Future integration

memory = DNAMemory()


def route(input_data):
    """
    QVoid MCP Routing Engine 🧠⚛️

    input_data can be either:
    - str (raw input)
    - dict with keys: 'text', 'src_ip', etc.
    """

    # Step 1: Normalize input
    if isinstance(input_data, str):
        text = input_data.lower()
        src_ip = None
    elif isinstance(input_data, dict):
        text = input_data.get("text", "").lower()
        src_ip = input_data.get("src_ip", None)
    else:
        return {"verdict": "invalid input", "confidence": 0}

    model_name = "unknown"
    previous_label = "UNKNOWN"
    result = {"verdict": "unknown", "confidence": 0}

    # Step 2: Model Routing
    if any(k in text for k in ["select", "drop", "union", "insert", "--"]):
        result = model_sql.predict(text)
        model_name = "model_sql"

    elif any(k in text for k in ["syn", "tcp flood", "ddos", "packet blast"]):
        result = model_syn.predict(text)
        model_name = "model_syn"

    elif any(k in text for k in ["malware", "payload", "inject", "syscall", "memory thread"]):
        result = model_malware.predict(text)
        model_name = "model_malware"

    elif any(k in text for k in ["login", "credential", "reset", "verify", "email", "phishing", "click here"]):
        result = model_phishing.predict(text)
        model_name = "model_phishing"

    elif any(k in text for k in ["ftp", "http", "dos", "brute", "slowloris"]):
        result = model_cicids_friday.predict(text)
        model_name = "model_cicids_friday"

    elif any(k in text for k in ["anomaly", "weird", "unexpected", "unknown thread"]):
        result = model_anomaly.predict(text)
        model_name = "model_anomaly"

    else:
        return {"verdict": "unknown", "confidence": 0}

    # Step 3: Update DNA Memory
    memory.update(result["verdict"], previous=previous_label)

    # Step 4: Plugin Hooks
    plugin_reports = []
    for plugin in registered_plugins:
        if hasattr(plugin, "run"):
            try:
                report = plugin.run({
                    "target": src_ip or "127.0.0.1",
                })
                plugin_reports.append({
                    "plugin": plugin.name,
                    "report": report
                })
            except Exception as e:
                plugin_reports.append({
                    "plugin": plugin.name,
                    "error": str(e)
                })

    # Step 5: Return Response
    return {
        "model": model_name,
        "verdict": result.get("verdict", "N/A"),
        "confidence": result.get("confidence", 0),
        "plugins": plugin_reports
        # Optional Future: 'qkd_keys': simulate_qkd_keypair()  # when live
    }
