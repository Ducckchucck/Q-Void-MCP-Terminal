import os
import joblib
import numpy as np

MODEL_DIR = os.path.join("models", "akhilesh")

model = joblib.load(os.path.join(MODEL_DIR, "akhilesh_model.pkl"))
scaler = joblib.load(os.path.join(MODEL_DIR, "akhilesh_scaler.pkl"))
features = joblib.load(os.path.join(MODEL_DIR, "akhilesh_features.pkl"))

def predict(text):
    # Simulate feature vector (random but controlled)
    simulated_input = np.random.uniform(low=0.1, high=1.0, size=(1, len(features)))

    scaled = scaler.transform(simulated_input)
    label = model.predict(scaled)[0]
    proba = model.predict_proba(scaled)[0]

    return {
        "verdict": label,
        "confidence": round(np.max(proba) * 100, 2)
    }
