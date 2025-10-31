# modules/tone_memory.py
import json
from collections import deque

FILE_PATH = "tone_data.json"

def save_tone_training_data(data):
    try:
        with open(FILE_PATH, "w") as f:
            json.dump(list(data), f)
        print("💾 Tone training data saved.")
    except Exception as e:
        print(f"⚠️ Failed to save training data: {e}")

def load_tone_training_data(maxlen=100):
    try:
        with open(FILE_PATH, "r") as f:
            raw = json.load(f)
            print(f"📦 Loaded {len(raw)} samples from file.")
            return deque(raw, maxlen=maxlen)
    except FileNotFoundError:
        print("📁 No previous training data found.")
    except Exception as e:
        print(f"⚠️ Failed to load training data: {e}")
    return deque(maxlen=maxlen)
