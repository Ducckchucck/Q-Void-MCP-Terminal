import os, sys, json, joblib
import pandas as pd, numpy as np
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from astl_utils.dna_features import apply_dna_features

# === Load Config ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "astl_configs", "infiltration_config.json")
with open(CONFIG_PATH) as f:
    config = json.load(f)

DATA_PATH = os.path.join(config["DATA_PATH"])
MODEL_DIR = os.path.join(BASE_DIR, config["OUTPUT_DIR"])
os.makedirs(MODEL_DIR, exist_ok=True)

print(f"📂 Loading dataset from: {DATA_PATH}")
df = pd.read_csv(DATA_PATH)

# Drop non-numeric columns except 'Label'
if 'Flow ID' in df.columns:
    df.drop(['Flow ID', 'Src IP', 'Dst IP', 'Timestamp'], axis=1, errors='ignore', inplace=True)

label_col = "Label"
feature_cols = [col for col in df.columns if col != label_col]
df = df.dropna(subset=feature_cols)

# Synthetic Query for DNA Features
df["Query"] = df[feature_cols].astype(str).agg(" ".join, axis=1)
X_text = df["Query"].astype(str).reset_index(drop=True)
y = df[label_col].values

print("🧬 DNA features on synthetic 'Query' column...")
X_dna = apply_dna_features(pd.DataFrame({'Query': X_text}))
X_dna = np.nan_to_num(X_dna, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)

# === Split Data ===
X_train_val, X_unlabeled, y_train_val, _ = train_test_split(
    X_dna, y, test_size=0.4, stratify=y, random_state=42
)
X_labeled, X_val, y_labeled, y_val = train_test_split(
    X_train_val, y_train_val, test_size=0.3, stratify=y_train_val, random_state=42
)

print(f"📊 Labeled: {len(X_labeled)} | Validation: {len(X_val)} | Unlabeled: {len(X_unlabeled)}")

# === ASTL LOOP ===
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

        X_pseudo = X_unlabeled[idxs]
        y_pseudo = model.predict(X_pseudo)

        X_labeled = np.vstack([X_labeled, X_pseudo])
        y_labeled = np.concatenate([y_labeled, y_pseudo])
        X_unlabeled = np.delete(X_unlabeled, idxs, axis=0)

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

# === Train Initial Model ===
model = RandomForestClassifier(n_estimators=200, random_state=42)
model.fit(X_labeled, y_labeled)
initial_acc = accuracy_score(y_val, model.predict(X_val))
print(f"\n📈 Initial Validation Accuracy: {initial_acc:.4f}")

# === Run ASTL ===
final_model, log_data = astl_loop(model, X_labeled, y_labeled, X_unlabeled, X_val, y_val)

# === Save Model & Logs ===
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
model_path = os.path.join(MODEL_DIR, f"infiltration_astl_{timestamp}.pkl")
joblib.dump(final_model, model_path)

log_dir = os.path.join(BASE_DIR, "ASTL", "astl_logs")
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, f"infiltration_astl_log_{timestamp}.json")

with open(log_path, "w") as f:
    json.dump({
        "initial_val_acc": initial_acc,
        "loop_logs": log_data,
        "timestamp": timestamp
    }, f, indent=2)

print(f"\n💾 Final Model Saved: {model_path}")
print(f"📝 ASTL Logs Saved: {log_path}")
