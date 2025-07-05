import pickle
import pandas as pd
import numpy as np

# Load model, scaler, and feature names
def load_pickle(file_name):
    try:
        with open(file_name, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        print(f"❌ Error loading {file_name}: {e}")
        exit()

model = load_pickle("cyrus_ai_model.pkl")
scaler = load_pickle("scaler.pkl")
feature_names = load_pickle("feature_columns.pkl")

print("✅ Model, Scaler, and Feature Names loaded successfully!")

# Load and clean test dataset
try:
    df = pd.read_csv("datasets/1-Neris-20110810.csv")
    print("✅ Real dataset loaded successfully!")
except Exception as e:
    print(f"❌ Error loading test dataset: {e}")
    exit()

try:
    # ✅ Keep only the features used during training
    X = df.loc[:, df.columns.isin(feature_names)].copy()

    # ✅ Reorder columns to match training order (this is super important)
    X = X[feature_names]

    # ✅ Scale the input data using the same scaler used during training
    X_scaled = scaler.transform(X)

    # ✅ Make predictions
    predictions = model.predict(X_scaled)

    # ✅ Save predictions to CSV
    df["Predicted_Label"] = predictions
    df[["Predicted_Label"]].to_csv("predictions.csv", index=False)
    
    print("✅ Predictions completed and saved to 'predictions.csv'!")

except Exception as e:
    print(f"❌ Prediction error: {e}")
