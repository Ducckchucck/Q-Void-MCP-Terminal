from qvoid_fusion.models import (
    model_sql,
    model_syn,
    model_malware,
    model_phishing,
    model_cicids_friday,
    model_anomaly
)

from qvoid_fusion.plugins import registered_plugins


def route(input_data):
    """
    input_data can be either:
    - str (raw text)
    - dict with keys: 'text', 'src_ip', 'dst_ip', etc.
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

    # Step 2: Model routing
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

    # Step 3: Trigger plugins
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

    # Step 4: Final response
    return {
        "model": model_name,
        "verdict": result.get("verdict", "N/A"),
        "confidence": result.get("confidence", 0),
        "plugins": plugin_reports
    }
