import os
import time
import pickle
import random
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, confusion_matrix

# === Paths ===
DATA_PATH = r"datasets/shrikant/phishing_cleaned.csv"
OUTPUT_DIR = r"models/shrikant"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === Sample Augmented Payloads (Phishing Examples) ===
phishing_payloads = [
    "login to your account to verify your identity",
    "update your bank information urgently",
    "click here to reset your password",
    "you have won a prize, claim now",
    "your account has been suspended, verify now",
    "dear user, confirm your payment details",
    "download the attached invoice and review",
    "your email has been compromised",
    "confirm your identity to avoid suspension",
    "this is a final warning about your account",
    "click to unlock your account",
    "action required: verify billing info",
    "security update required immediately",
    "your payment has failed, update card",
    "paypal alert: unusual activity",
    "apple ID login attempt blocked",
    "IRS notice: tax fraud detected",
    "bank account alert: login attempt",
    "Microsoft license expired click here",
    "click here for your refund",
    "verify OTP to continue",
    "your transaction was declined",
    "deactivate your firewall now",
    "malware alert: download patch",
    "unauthorized login from Russia",
    "confirm Google account",
    "Outlook login blocked",
    "Dropbox sharing violation detected",
    "download this important file",
    "your certificate expired",
    "unauthorized login attempt detected",
    "reset your credentials here",
    "we detected suspicious traffic from your IP",
    "alert: your password will expire soon",
    "please confirm your recent purchase",
    "fraud attempt detected on your credit card",
    "your bank card has been locked",
    "Amazon order on hold, verify address",
    "security code: 28493",
    "your mobile carrier suspended access",
    "urgent billing verification needed",
    "Google Drive quota exceeded, reactivate",
    "we couldn’t deliver your package",
    "Facebook security confirmation required",
    "Win a brand new iPhone now!",
    "complete the captcha to proceed",
    "scan QR to reactivate device",
    "urgent: confirm ownership of your wallet",
    "unauthorized PayPal invoice issued",
    "Apple billing mismatch detected",
    "government notice: respond immediately",
]

# === Augment benign messages too
benign_payloads = [
    "view your dashboard and reports",
    "reset password using the settings page",
    "your account is secured with 2FA",
    "thank you for your purchase",
    "here is your invoice for the month",
    "your order has been shipped",
    "track your delivery in your account",
    "meeting scheduled for tomorrow",
    "follow our latest product update",
    "congrats on your promotion",
    "here are your requested documents",
    "important update on company policies",
    "check your appointment confirmation",
    "Zoom link for today’s call",
    "monthly newsletter attached",
    "settings updated successfully",
    "see your subscription summary",
    "profile photo updated",
    "connected to Wi-Fi successfully",
    "your OTP is 439201",
    "logging activity from Mumbai",
    "event reminder for next week",
    "your device is connected securely",
    "see statement from last month",
    "confirm address for delivery",
]

# === Create Augmented DataFrame
aug_df = pd.DataFrame({
    "text": phishing_payloads + benign_payloads,
    "label": [1] * len(phishing_payloads) + [0] * len(benign_payloads)
})

# === Load Existing Dataset
print(f"📂 Loading phishing dataset: {DATA_PATH}")
df = pd.read_csv(DATA_PATH)

# === Ensure correct column names
if "class" in df.columns and "text" not in df.columns:
    df.rename(columns={"class": "label"}, inplace=True)

# === Ensure 'label' is int
df['label'] = df['label'].astype(int)

# === If 'text' column is missing, fuse features into one string
if "text" not in df.columns:
    feature_cols = df.columns.tolist()
    feature_cols.remove("label")
    df['text'] = df[feature_cols].astype(str).agg(" ".join, axis=1)

# === Display diagnostic
print(f"🧪 Columns: {df.columns.tolist()}")
print(f"🧪 Sample Rows:\n{df.head()}")

# === Merge datasets
df = pd.concat([df[['text', 'label']], aug_df], ignore_index=True)
df.drop_duplicates(inplace=True)
df.dropna(subset=['text', 'label'], inplace=True)

print(f"✅ Total Samples: {len(df)}")

# === Preprocessing
X = df['text'].astype(str)
y = df['label'].astype(int)

vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=3000)
X_vec = vectorizer.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(
    X_vec, y, test_size=0.2, stratify=y, random_state=42
)

# === RandomizedSearch ===
param_dist = {
    'n_estimators': [50, 100, 200],
    'max_depth': [10, 20, None],
    'min_samples_split': [2, 5, 10],
    'max_features': ['sqrt', 'log2']
}

search = RandomizedSearchCV(
    RandomForestClassifier(),
    param_distributions=param_dist,
    n_iter=50,
    cv=10,
    verbose=2,
    n_jobs=-1
)

print("🧠 Training phishing detection model...")
start = time.time()
search.fit(X_train, y_train)
end = time.time()

# === Evaluation
best_model = search.best_estimator_
y_pred = best_model.predict(X_test)
acc = accuracy_score(y_test, y_pred)

print(f"\n🏆 Best Parameters: {search.best_params_}")
print(f"🧠 Best CV Score: {search.best_score_:.4f}")
print(f"⏱️ Time Taken: {(end-start)/60:.2f} mins")
print(f"✅ Test Accuracy: {acc:.4f}")
print("🧾 Confusion Matrix:\n", confusion_matrix(y_test, y_pred))

# === Show Misclassified
wrong_idx = [i for i, (a, b) in enumerate(zip(y_test, y_pred)) if a != b]
print(f"\n⚠️ Misclassified Samples: {len(wrong_idx)}")
for i in wrong_idx[:10]:
    print("🚫", X.iloc[y_test.index[i]], "| True:", y_test.iloc[i], "| Pred:", y_pred[i])

# === Save
with open(os.path.join(OUTPUT_DIR, "shrikant_model.pkl"), "wb") as f:
    pickle.dump(best_model, f)

with open(os.path.join(OUTPUT_DIR, "shrikant_vectorizer.pkl"), "wb") as f:
    pickle.dump(vectorizer, f)

with open(os.path.join(OUTPUT_DIR, "shrikant_feature.pkl"), "wb") as f:
    pickle.dump(vectorizer.get_feature_names_out().tolist(), f)

print("✅ Model, Vectorizer, and Features saved to:", OUTPUT_DIR)
