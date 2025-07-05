# To run: C:\QVoid-MutantAI>python -m ASTL.akhilesh.syn_astl_hybrid

import os, sys, json, joblib
import pandas as pd, numpy as np
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Add ASTL root to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# === Load config ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "astl_configs", "syn_config.json")

with open(CONFIG_PATH) as f:
    config = json.load(f)

# Dataset and output paths
DATA_PATH = os.path.join(config["DATA_PATH"])  # Absolute from root
MODEL_DIR = os.path.join(BASE_DIR, config["OUTPUT_DIR"])
os.makedirs(MODEL_DIR, exist_ok=True)

print(f"📂 Loading dataset from: {DATA_PATH}")

# === Load dataset ===
df = pd.read_csv(DATA_PATH)

if "Label" not in df.columns:
    raise ValueError("❌ Dataset must contain a 'Label' column.")

df = df.dropna(subset=["Label"])
df = df.dropna(axis=1, how="all")  # Drop all-NaN columns

# === Drop non-numeric columns (like IPs, Flow ID, Timestamp)
non_numeric_cols = df.select_dtypes(include=["object"]).columns.tolist()
non_numeric_cols = [col for col in non_numeric_cols if col != "Label"]
print(f"🧹 Dropping non-numeric columns: {non_numeric_cols}")

X = df.drop(columns=["Label"] + non_numeric_cols)
X.replace([np.inf, -np.inf], np.nan, inplace=True)
X.fillna(0, inplace=True)

# Labels
y = df["Label"].astype(str).values

# Filter out label classes with <2 samples (ASTL needs at least 2 for stratification)
from collections import Counter
label_counts = Counter(y)
valid_idxs = [i for i, lbl in enumerate(y) if label_counts[lbl] >= 2]

if len(valid_idxs) < len(y):
    print(f"⚠️ Removed {len(y) - len(valid_idxs)} samples with rare labels (<2 instances).")

X = X.iloc[valid_idxs].reset_index(drop=True)
y = np.array([y[i] for i in valid_idxs])

# === Splitting
X_train_val, X_unlabeled, y_train_val, _ = train_test_split(
    X, y, test_size=0.4, stratify=y, random_state=42
)
X_labeled, X_val, y_labeled, y_val = train_test_split(
    X_train_val, y_train_val, test_size=0.3, stratify=y_train_val, random_state=42
)

print(f"📊 Labeled: {len(X_labeled)} | Validation: {len(X_val)} | Unlabeled: {len(X_unlabeled)}")

# === ASTL Loop ===
def astl_loop(model, X_labeled, y_labeled, X_unlabeled, X_val, y_val,
              max_loops=10, confidence_threshold=0.95, entropy_threshold=0.3):
    from scipy.stats import entropy
    logs = []
    prev_acc = accuracy_score(y_val, model.predict(X_val))

    for loop in range(1, max_loops + 1):
        print(f"\n🔁 ASTL Loop {loop}")
        probs = model.predict_proba(X_unlabeled)
        conf = np.max(probs, axis=1)
        ent = entropy(probs.T)

        idxs = np.where((conf >= confidence_threshold) & (ent <= entropy_threshold))[0]
        if len(idxs) == 0:
            print("❌ No confident samples.")
            break

        X_pseudo = X_unlabeled.iloc[idxs]
        y_pseudo = model.predict(X_pseudo)

        X_labeled = pd.concat([X_labeled, X_pseudo])
        y_labeled = np.concatenate([y_labeled, y_pseudo])
        X_unlabeled = X_unlabeled.drop(X_unlabeled.index[idxs])

        model.fit(X_labeled, y_labeled)
        val_acc = accuracy_score(y_val, model.predict(X_val))
        print(f"✅ Loop {loop}: Val Acc = {val_acc:.4f} | Added = {len(idxs)}")

        logs.append({
            "loop": loop,
            "added": int(len(idxs)),
            "val_acc": float(val_acc)
        })

        if abs(val_acc - prev_acc) < 0.001:
            print("🛑 Minimal improvement. Stopping.")
            break
        prev_acc = val_acc

    return model, logs

# === Initial Training ===
model = RandomForestClassifier(n_estimators=200, random_state=42)
model.fit(X_labeled, y_labeled)
initial_acc = accuracy_score(y_val, model.predict(X_val))
print(f"\n📈 Initial Validation Accuracy: {initial_acc:.4f}")

# === ASTL Loop Training ===
final_model, log_data = astl_loop(model, X_labeled, y_labeled, X_unlabeled, X_val, y_val)

# === Save model and logs ===
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
model_path = os.path.join(MODEL_DIR, f"syn_hybrid_astl_{timestamp}.pkl")
joblib.dump(final_model, model_path)

log_dir = os.path.join(BASE_DIR, "ASTL", "astl_logs")
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, f"syn_astl_log_{timestamp}.json")

with open(log_path, "w") as f:
    json.dump({
        "initial_val_acc": initial_acc,
        "loop_logs": log_data,
        "timestamp": timestamp
    }, f, indent=2)

print(f"\n💾 Final Model Saved: {model_path}")
print(f"📝 ASTL Logs Saved: {log_path}")
