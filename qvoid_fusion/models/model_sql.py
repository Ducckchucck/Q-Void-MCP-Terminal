import pickle
import os

BASE_PATH = os.path.join("models", "piyush", "SQL")

def safe_load_pickle(path):
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load pickle from {path}: {e}")
        raise

# Load model and vectorizer safely
model = safe_load_pickle(os.path.join(BASE_PATH, "piyushm2_model.pkl"))
vectorizer = safe_load_pickle(os.path.join(BASE_PATH, "piyushm2_vectorizer.pkl"))

def predict(text):
    text = text.lower()
    vector = vectorizer.transform([text])

    prediction = model.predict(vector)[0]
    proba = model.predict_proba(vector)[0]
    confidence = round(max(proba) * 100)

    return {
        "verdict": "Malicious" if prediction == 1 else "Benign",
        "confidence": confidence
    }
