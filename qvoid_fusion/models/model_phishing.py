

import pickle
import os

BASE_PATH = os.path.join("models", "shrikant")

with open(os.path.join(BASE_PATH, "shrikant_model.pkl"), "rb") as f:
    model = pickle.load(f)
with open(os.path.join(BASE_PATH, "shrikant_feature.pkl"), "rb") as f:
    features = pickle.load(f)

def extract_features(text):
    text = text.lower()
    return {f: int(f in text) for f in features}

def predict(text):
    extracted = extract_features(text)
    print(f"[DEBUG] Extracted features: {extracted}")  

    x = [[extracted.get(f, 0) for f in features]]

    try:
        prediction = model.predict(x)[0]
        proba = model.predict_proba(x)[0]
        confidence = round(max(proba) * 100)

        print(f"[DEBUG] Prediction: {prediction}, Confidence: {confidence}")  

        return {
            "verdict": prediction,
            "confidence": confidence
        }

    except Exception as e:
        return {
            "verdict": "Prediction Error",
            "confidence": str(e)
        }

