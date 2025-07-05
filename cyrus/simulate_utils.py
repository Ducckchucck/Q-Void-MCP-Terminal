import numpy as np
import pandas as pd

def simulate_anomaly_row(features):
    """
    Simulates a single anomalous input row based on expected features.
    Returns a DataFrame with one row.
    """
    anomaly_values = {}

    for feat in features:
        fname = feat.lower()

        if "packet" in fname or "pkt" in fname:
            anomaly_values[feat] = np.random.uniform(1000, 20000)  # High packet count
        elif "duration" in fname or "iat" in fname:
            anomaly_values[feat] = np.random.choice([np.random.uniform(1e6, 1e7), np.random.uniform(0, 10)])
        elif "length" in fname or "bytes" in fname:
            anomaly_values[feat] = np.random.choice([0, np.random.uniform(10000, 100000)])
        elif "flag" in fname:
            anomaly_values[feat] = np.random.randint(1, 3)  # TCP flag toggling
        elif "rate" in fname or "/s" in fname or "ratio" in fname:
            anomaly_values[feat] = np.random.uniform(5000, 50000)  # Sudden spike
        elif "min" in fname or "max" in fname:
            anomaly_values[feat] = np.random.uniform(0, 10000)
        elif "init_win" in fname:
            anomaly_values[feat] = np.random.choice([0, 65535])
        elif "act_data_pkt" in fname or "seg_size" in fname:
            anomaly_values[feat] = np.random.randint(0, 1500)
        else:
            # General fallback
            anomaly_values[feat] = np.random.uniform(0, 1000)

    return pd.DataFrame([anomaly_values])
