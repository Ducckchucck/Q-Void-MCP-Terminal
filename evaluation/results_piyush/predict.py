import pandas as pd
import joblib
import time
import logging
from sklearn.ensemble import RandomForestClassifier
from typing import List, Optional
import re
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix

# 🛠️ Logging Setup
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')

class CyrusDefender:
    def __init__(self, model_path: str, scaler_path: str, features_path: str):
        logging.info("🔄 Loading model, scaler, and feature names...")  # CHANGED FROM print TO log
        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)
        self.expected_features: List[str] = joblib.load(features_path)

        print("✅ All components loaded.")
        print(f"🧠 Model type: {type(self.model).__name__}")
        print(f"📑 Expected feature count: {len(self.expected_features)}")

    def clean_column_names(self, cols: List[str]) -> List[str]:
        cleaned = []
        for col in cols:
            col = re.sub(r'[^\x00-\x7F]+', '', col)
            col = re.sub(r'[^A-Za-z0-9_]', '', col)
            col = col.strip()
            cleaned.append(col)
        return cleaned

    def load_and_clean_data(self, test_path: str) -> Optional[pd.DataFrame]:
        print(f"📂 Loading testing data from: {test_path}")
        try:
            df = pd.read_csv(test_path, encoding='ISO-8859-1', engine='python', on_bad_lines='skip')
            print(f"📊 Raw test data shape: {df.shape}")
        except Exception as e:
            print(f"❌ Error loading CSV file: {e}")
            return None

        print("🧹 Cleaning test data...")
        df.columns = self.clean_column_names(df.columns)

        drop_cols = ['id', 'label', 'attack_cat']
        df.drop(columns=[col for col in drop_cols if col in df.columns], errors='ignore', inplace=True)
        df.fillna(0, inplace=True)

        missing_features = list(set(self.expected_features) - set(df.columns))
        if missing_features:
            print(f"🔍 Missing features added with default 0: {len(missing_features)}")
            missing_df = pd.DataFrame(0.0, index=df.index, columns=missing_features)
            df = pd.concat([df, missing_df], axis=1)

        try:
            df = df[self.expected_features].copy()
        except Exception as e:
            print(f"❌ Column mismatch error: {e}")
            print(f"🛠 Current columns: {df.columns.tolist()}")
            return None

        print(f"✅ Cleaned data shape: {df.shape}")
        return df

    def predict(self, df: Optional[pd.DataFrame]) -> List[int]:
        if df is None:
            print("❌ No data to predict.")
            return []

        print("🤖 Making predictions...")
        try:
            start_time = time.time()
            scaled = self.scaler.transform(df)
            raw_preds = self.model.predict(scaled)
            preds = [int(p) for p in raw_preds]
            duration = time.time() - start_time
            print(f"⏱️ Prediction completed in {duration:.2f} seconds.")
            print(f"✅ Predictions done. Sample: {preds[:10]}")
            return preds
        except Exception as e:
            print(f"❌ Prediction error: {e}")
            return []

    def summarize_predictions(self, preds: List[int], labels: Optional[List[int]] = None):
        if not preds:
            print("❌ No predictions to summarize.")
            return

        preds_array = np.array(preds)
        total = len(preds)
        unique, counts = np.unique(preds_array, return_counts=True)
        summary = dict(zip(unique, counts))

        print("\n📊 Prediction Summary:")
        print(f"🔢 Total rows predicted: {total}")
        for label in [0, 1]:
            count = summary.get(label, 0)
            percent = (count / total) * 100
            emoji = "✅" if label == 0 else "🚨"
            print(f" {emoji} Class {label}: {count} predictions ({percent:.2f}%)")

        if labels:
            print("\n📈 Evaluation with Ground Truth:")
            labels_array = np.array(labels).astype(np.int32)
            preds_array = preds_array.astype(np.int32)
            print(confusion_matrix(labels_array, preds_array))
            print(classification_report(labels_array, preds_array, digits=4))


if __name__ == "__main__":
    model_path = "cyrus_ai_model.pkl"
    scaler_path = "scaler.pkl"
    features_path = "feature_columns.pkl"
    test_path = "C:/Users/piyus/OneDrive/Desktop/Cyrus_ai/datasets/UNSW_cleaned.csv"

    start_total = time.time()

    defender = CyrusDefender(model_path, scaler_path, features_path)
    test_df = defender.load_and_clean_data(test_path)

    ground_truth = None
    try:
        raw_df = pd.read_csv(test_path, encoding='ISO-8859-1', engine='python', on_bad_lines='skip')
        if 'label' in raw_df.columns:
            ground_truth = raw_df['label'].astype(int).tolist()
    except Exception as e:
        print(f"⚠️ Warning while loading ground truth: {e}")

    preds = defender.predict(test_df)

    if preds:
        output_file = "predictions.csv"
        pd.Series(preds, name="Predicted_Label").to_csv(output_file, index=False)
        print(f"📁 Predictions saved to {output_file}")

        defender.summarize_predictions(preds, ground_truth)

    print(f"\n✅ All done in {time.time() - start_total:.2f} seconds!")
    print("🔚 Exiting... Have a nice day My Lord!! 😎")
