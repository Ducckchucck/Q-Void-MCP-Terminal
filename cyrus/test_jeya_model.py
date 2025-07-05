import pandas as pd
import joblib
import numpy as np
from simulate_utils import simulate_anomaly_row

# === Paths ===
MODEL_PATH = "models/jeya/jeya_model.pkl"
SCALER_PATH = "models/jeya/jeya_scaler.pkl"
FEATURE_PATH = "models/jeya/jeya_features.pkl"

# === Load trained model, scaler, and feature list ===
print("📦 Loading model, scaler, and feature list...")
model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)
features = joblib.load(FEATURE_PATH)

print(f"🧬 Feature count expected: {len(features)}")

# === Generate Simulated Anomaly Input ===
print("🔬 Generating simulated anomaly...")
anomaly_df = simulate_anomaly_row(features)

# === Preprocess ===
anomaly_scaled = scaler.transform(anomaly_df)

# === Prediction ===
prediction = model.predict(anomaly_scaled)[0]
probabilities = model.predict_proba(anomaly_scaled)[0]

# === Output ===
print("\n🚨 Simulated Input Features:")
print(anomaly_df.to_string(index=False))

print("\n🧠 Model Prediction:")
print(f"➡️  Predicted Label: {prediction}")
print("📊 Class Probabilities:")
for cls, prob in zip(model.classes_, probabilities):
    print(f" - {cls}: {prob:.4f}")
