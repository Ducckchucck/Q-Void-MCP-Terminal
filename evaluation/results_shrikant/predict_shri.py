import pandas as pd
import joblib
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve

# ======== Paths to Shrikant's Files =========
model_path = "shrikant_model.pkl"
scaler_path = "shrikant_scaler.pkl"
features_path = "shrikant_features.pkl"
test_path = "PhiUSIIL_Phishing_URL_Dataset.csv"

# ========== Load the Components ============
print("📦 Loading model, scaler, and features...")
model = joblib.load(model_path)
scaler = joblib.load(scaler_path)
expected_features = joblib.load(features_path)

# ========== Load Test Data ============
print("📂 Loading test data...")
df = pd.read_csv(test_path, encoding='ISO-8859-1', engine='python', on_bad_lines='skip')

# ========== Clean Columns ============
df.columns = [col.encode('ascii', 'ignore').decode('ascii') for col in df.columns]
df.columns = [col.strip().replace(' ', '').replace('-', '_') for col in df.columns]
raw_df = df.copy()

drop_cols = ['id', 'label', 'attack_cat']
df.drop(columns=[col for col in drop_cols if col in df.columns], errors='ignore', inplace=True)
df.fillna(0, inplace=True)

missing_features = list(set(expected_features) - set(df.columns))
if missing_features:
    print(f"🔧 Adding missing features: {len(missing_features)}")
    for col in missing_features:
        df[col] = 0.0

df = df[expected_features]

# ========== Predict ============
print("🤖 Predicting...")
scaled = scaler.transform(df)
preds = model.predict(scaled)

# ========== Save Predictions ============
pd.Series(preds, name="Shrikant_Predictions").to_csv("shrikant_predictions.csv", index=False)
print("✅ Saved predictions to shrikant_predictions.csv")

# ========== Evaluation ============
print("\n📈 Evaluation:")
try:
    if 'label' in raw_df.columns:
        labels = raw_df['label'].astype(int).tolist()
        preds = list(map(int, preds))

        print(f"🧪 Sample Ground Truth: {labels[:5]}")
        print(f"🧪 Sample Predictions  : {preds[:5]}")
        print(f"🔍 Types -> y_true: {type(labels[0])}, y_pred: {type(preds[0])}")

        # Confusion Matrix
        print("\n📊 Confusion Matrix:")
        print(confusion_matrix(labels, preds))

        # Classification Report
        print("\n📋 Classification Report:")
        print(classification_report(labels, preds, digits=4))

        # ROC & AUC
        print("\n📉 ROC Curve & AUC Score:")
        fpr, tpr, _ = roc_curve(labels, preds)
        auc = roc_auc_score(labels, preds)
        print(f"AUC Score: {auc:.4f}")

        plt.figure(figsize=(6, 5))
        plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {auc:.4f})')
        plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('Receiver Operating Characteristic')
        plt.legend(loc="lower right")
        plt.grid(True)
        plt.savefig("roc_curve_shrikant.png")
        print("📊 ROC curve saved as 'roc_curve_shrikant.png'")

        # Save Errors
        df_errors = raw_df.copy()
        df_errors['prediction'] = preds
        df_errors['label'] = labels
        fp = df_errors[(df_errors['label'] == 0) & (df_errors['prediction'] == 1)]
        fn = df_errors[(df_errors['label'] == 1) & (df_errors['prediction'] == 0)]

        fp.to_csv("false_positives.csv", index=False)
        fn.to_csv("false_negatives.csv", index=False)
        print("🚫 False Positives saved to false_positives.csv")
        print("🚫 False Negatives saved to false_negatives.csv")

    else:
        print("⚠️ No 'label' column found. Skipping evaluation.")
except Exception as e:
    print(f"⚠️ Error during evaluation: {e}")