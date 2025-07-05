import os
import time
import pickle
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.feature_extraction.text import TfidfVectorizer

# === Paths ===
DATA_PATH = r"datasets/piyush/SQL/Modified_SQL_Dataset.csv"
OUTPUT_DIR = r"models/piyush/SQL"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# === Load Dataset ===
print(f"📄 Loading: {DATA_PATH}")
df = pd.read_csv(DATA_PATH)

# === Basic Sanity Checks ===
if 'Query' not in df.columns or 'Label' not in df.columns:
    raise ValueError("Dataset must contain 'Query' and 'Label' columns.")

df = df.dropna(subset=['Query', 'Label'])

# === Label Distribution ===
print("📊 Label distribution:\n", df['Label'].value_counts())

# === Features and Labels ===
X = df['Query'].astype(str)
y = df['Label'].astype(int)

# === Train-Test Split ===
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

# === TF-IDF Vectorization ===
vectorizer = TfidfVectorizer(
    lowercase=True,
    max_features=1000,
    ngram_range=(1, 3),
    stop_words='english'
)

X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# === Save the Vectorizer ===
with open(os.path.join(OUTPUT_DIR, "piyushm2_vectorizer.pkl"), "wb") as f:
    pickle.dump(vectorizer, f)

# === Save Feature List ===
feature_names = vectorizer.get_feature_names_out()
with open(os.path.join(OUTPUT_DIR, "piyushm2_feature.pkl"), "wb") as f:
    pickle.dump(feature_names.tolist(), f)

# === Define Hyperparameter Space ===
param_dist = {
    'n_estimators': [50, 100, 200],
    'max_depth': [10, 20, 30, None],
    'min_samples_split': [2, 5, 10],
    'max_features': ['sqrt', 'log2']
}

# === Train the Model ===
search = RandomizedSearchCV(
    estimator=RandomForestClassifier(),
    param_distributions=param_dist,
    n_iter=400,
    cv=10,
    verbose=2,
    n_jobs=-1
)

print("🧠 Starting training...")
start = time.time()
search.fit(X_train_vec, y_train)
end = time.time()

# === Evaluation ===
best_model = search.best_estimator_
y_pred = best_model.predict(X_test_vec)
acc = accuracy_score(y_test, y_pred)

print(f"\n🏆 Best Parameters:\n{search.best_params_}")
print(f"🧠 Best CV Score: {search.best_score_:.4f}")
print(f"📊 CV Folds: {search.cv}")
print(f"⏱️ Time Taken: {(end - start)/60:.2f} mins")
print(f"✅ Test Accuracy: {acc:.4f}")
print("🧾 Confusion Matrix:\n", confusion_matrix(y_test, y_pred))

# === Save Model ===
with open(os.path.join(OUTPUT_DIR, "piyushm2_model.pkl"), "wb") as f:
    pickle.dump(best_model, f)

print("✅ Model, Vectorizer, and Features saved to:", OUTPUT_DIR)
