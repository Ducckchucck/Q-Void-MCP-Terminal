import os
import json
import time
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer
from ASTL.astl_utils.dna_features import apply_dna_features  # ← Keep this path consistent

# === Path Setup ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "astl_configs", "sql_config.json")

with open(CONFIG_PATH) as f:
    config = json.load(f)

DATA_PATH = os.path.join(BASE_DIR, config["dataset_path"])
LOG_DIR = os.path.join(BASE_DIR, config["logs_dir"])
MODEL_DIR = os.path.join(BASE_DIR, config["model_dir"])
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

# === Load Data ===
df = pd.read_csv(DATA_PATH).dropna(subset=["Query", "Label"])
X_raw = df["Query"].astype(str).reset_index(drop=True)
y = df["Label"].values

# === Feature Extraction ===
print("🔠 Generating TF-IDF features...")
tfidf = TfidfVectorizer(ngram_range=(1, 2), max_features=3000)
X_tfidf = tfidf.fit_transform(X_raw)

print("🧬 Generating DNA features...")
X_dna = apply_dna_features(pd.DataFrame({"Query": X_raw}))


print("🧠 Generating sBERT embeddings...")
sbert = SentenceTransformer("all-MiniLM-L6-v2")
X_bert = sbert.encode(X_raw.tolist(), show_progress_bar=True)

# === Combine All Features ===
print("🔗 Concatenating all features...")
X_all = np.hstack([
    X_tfidf.toarray(),
    X_dna.values,
    X_bert
])

# === Data Split ===
X_train_val, X_unlabeled, y_train_val, _ = train_test_split(
    X_all, y, test_size=0.4, stratify=y, random_state=42)

X_labeled, X_val, y_labeled, y_val = train_test_split(
    X_train_val, y_train_val, test_size=0.3, stratify=y_train_val, random_state=42)

print(f"📊 Labeled: {len(X_labeled)} | Validation: {len(X_val)} | Unlabeled: {len(X_unlabeled)}")

# === ASTL Function ===
def astl_loop(model, X_labeled, y_labeled, X_unlabeled, X_val, y_val,
              max_loops=5, confidence_threshold=0.95, entropy_threshold=0.3, min_gain=0.001):

    logs = []
    prev_acc = accuracy_score(y_val, model.predict(X_val))

    for loop in range(1, max_loops + 1):
        print(f"\n🔁 ASTL Loop {loop}")
        probs = model.predict_proba(X_unlabeled)
        confidences = np.max(probs, axis=1)
        entropy = -np.sum(probs * np.log(probs + 1e-12), axis=1)

        idxs = np.where((confidences >= confidence_threshold) & (entropy <= entropy_threshold))[0]
        if len(idxs) == 0:
            print("❌ No confident predictions. Exiting ASTL.")
            break

        X_pseudo = X_unlabeled[idxs]
        y_pseudo = model.predict(X_pseudo)

        X_labeled = np.vstack([X_labeled, X_pseudo])
        y_labeled = np.concatenate([y_labeled, y_pseudo])
        X_unlabeled = np.delete(X_unlabeled, idxs, axis=0)

        model.fit(X_labeled, y_labeled)

        val_acc = accuracy_score(y_val, model.predict(X_val))
        train_acc = accuracy_score(y_labeled, model.predict(X_labeled))

        log = {
            "loop": loop,
            "validation_accuracy": float(val_acc),
            "training_accuracy": float(train_acc),
            "samples_added": int(len(X_pseudo)),
            "remaining_unlabeled": int(len(X_unlabeled))
        }
        logs.append(log)

        print(f"✅ Loop {loop}: Val Acc={val_acc:.4f}, Train Acc={train_acc:.4f}, Added={len(X_pseudo)}")

        if abs(val_acc - prev_acc) < min_gain:
            print("🛑 Early stopping: minimal improvement.")
            break
        prev_acc = val_acc

    return model, logs

# === Base Model Training ===
model = RandomForestClassifier(n_estimators=200, max_depth=None, random_state=42)
model.fit(X_labeled, y_labeled)
print(f"📈 Initial Validation Accuracy: {accuracy_score(y_val, model.predict(X_val)):.4f}")

# === ASTL Execution ===
final_model, logs = astl_loop(
    model,
    X_labeled, y_labeled,
    X_unlabeled,
    X_val, y_val,
    max_loops=10
)

# === Save Results ===
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
model_path = os.path.join(MODEL_DIR, f"sql_hybrid_astl_{timestamp}.pkl")
log_path = os.path.join(LOG_DIR, f"sql_astl_log_{timestamp}.json")

joblib.dump(final_model, model_path)
with open(log_path, "w") as f:
    json.dump(logs, f, indent=4)

print(f"\n💾 Final Model Saved: {model_path}")
print(f"📝 ASTL Logs Saved: {log_path}")
