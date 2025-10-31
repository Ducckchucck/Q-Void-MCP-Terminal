


LOG_PATH = "logs/.qvoidlog"

def get_recent_logs(keyword=None, limit=10):
    try:
        with open(LOG_PATH, "r") as f:
            lines = f.readlines()
        if keyword:
            lines = [line for line in lines if keyword.lower() in line.lower()]
        return lines[-limit:]
    except FileNotFoundError:
        return []
