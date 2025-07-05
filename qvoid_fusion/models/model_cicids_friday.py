

import pickle
import os

BASE_PATH = os.path.join("models", "piyush", "cicids")

with open(os.path.join(BASE_PATH, "piyushm1_model.pkl"), "rb") as f:
    model = pickle.load(f)
with open(os.path.join(BASE_PATH, "piyushm1_feature.pkl"), "rb") as f:
    features = pickle.load(f)

def extract_features(text):
    text = text.lower()
    return {f: int(f in text) for f in features}

def predict(text):
    extracted = extract_features(text)
    x = [[extracted.get(f, 0) for f in features]]

    try:
        prediction = model.predict(x)[0]
        proba = model.predict_proba(x)[0]
        confidence = round(max(proba) * 100)

        return {
            "verdict": prediction,
            "confidence": confidence
        }

    except Exception as e:
        return {
            "verdict": "Prediction Error",
            "confidence": str(e)
        }