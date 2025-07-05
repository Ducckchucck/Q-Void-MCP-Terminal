import os
import pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from qvoid_fusion.utils.feature_extractor import extract_numerical_features_from_text

MODEL_PATH = "models/jeya/jeya_model.pkl"
SCALER_PATH = "models/jeya/jeya_scaler.pkl"
FEATURE_PATH = "models/jeya/jeya_features.pkl"

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

with open(SCALER_PATH, "rb") as f:
    scaler = pickle.load(f)

with open(FEATURE_PATH, "rb") as f:
    features = pickle.load(f)

def predict(text: str):
    feats = extract_numerical_features_from_text(text)
    x = [feats.get(f, 0) for f in features]
    x_scaled = scaler.transform([x])
    pred = model.predict(x_scaled)[0]

    if hasattr(model, "predict_proba"):
        confidence = round(max(model.predict_proba(x_scaled)[0]) * 100, 2)
    else:
        confidence = 0.0

    return {"verdict": pred, "confidence": confidence}
