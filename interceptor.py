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
DATA_PATH = r"datasets/piyush/SQL/Modified_SQL_Dataset.csv"
OUTPUT_DIR = r"models/piyush/SQL"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === Payload Generators ===

classic_sqli_payloads = [
    "' OR 'a'='a",
    "' OR 1=1--",
    "' OR 'x'='x",
    "admin' --",
    "admin' or '1'='1",
    "' OR EXISTS(SELECT * FROM users)",
    "UNION SELECT username, password FROM users--",
    "' OR sleep(5)--",
    "' OR pg_sleep(5)--",
    "' OR benchmark(1000000, MD5(1))--",
    "' OR 1=1#",
    "' OR 1=1/*",
    "' OR 1=1 AND ''='",
    "' OR ''='",
    "' OR 1=1 LIMIT 1--",
    "'; EXEC xp_cmdshell('whoami'); --",
    "' OR load_file('/etc/passwd')--",
    "' OR 0x61646D696E=0x61646D696E--",
    "' UNION SELECT NULL, NULL, version()--",
    "-1 UNION/**/SELECT/**/NULL,NULL,user(),password/**/FROM/**/users--+",
    "' OR (SELECT COUNT(*) FROM information_schema.tables) > 0 --",
    "' AND (SELECT SUBSTRING(@@version,1,1))='5",
    "1' AND IF(1=1, SLEEP(5), 0)--+",
    "' OR 1=1 OR ''='",
    "' or 1=1--",
    "1; DROP TABLE users",
    "' OR 1=1; --",
    "\" OR \"\"=\"",
    "' OR 1=CONVERT(INT,(SELECT @@version))--",
    "' UNION SELECT ALL NULL,NULL,NULL,NULL--",
    "' OR (SELECT table_name FROM information_schema.tables LIMIT 1) IS NOT NULL--",
    "admin'/**/OR/**/'1'='1",
    "' OR '1'='1'--",
    "1' OR 1=1 LIMIT 1--",
    "admin' OR 1=1 --",
    "' OR ASCII(SUBSTRING((SELECT @@version),1,1))=5 --",
    "' || '1'='1",
    "' OR 1=1 AND '1'='1",
    "' AND 'x'='x",
    "' AND 'x'='y",
    "' OR 1=1 UNION SELECT NULL,NULL--",
    "admin'/*comment*/OR/*bypass*/'1'='1",
    "AdMiN' OR '1'='1",
    "1=1--",
    "' OR 1=1#",
    "admin') OR ('1'='1--",
    "'UNION SELECT NULL,NULL,NULL--",
    "SELECT * FROM login WHERE username='admin'--",
    "SELECT table_name FROM information_schema.tables WHERE table_schema='db'--",
    "0'XOR(IF(1=1,SLEEP(5),0))--+"
]

# === Noise Generator ===
def add_noise(payload):
    noises = [" ", "/**/", "--", "#", "%20", "/*random*/", "//"]
    return payload.replace(" ", random.choice(noises))

noisy_aug = [add_noise(p) for p in classic_sqli_payloads]

# === Augmented Payload DataFrame ===
aug_df = pd.DataFrame({
    "Query": classic_sqli_payloads + noisy_aug,
    "Label": [1] * (len(classic_sqli_payloads) + len(noisy_aug))
})

# === Hard Benign Payloads ===
benign_queries = [
    "SELECT name FROM products WHERE price < 1000",
    "INSERT INTO logs (user, action) VALUES ('admin', 'login')",
    "SELECT COUNT(*) FROM orders",
    "UPDATE users SET last_login = NOW() WHERE id = 5",
    "DELETE FROM sessions WHERE expires < NOW()"
]

benign_df = pd.DataFrame({
    "Query": benign_queries,
    "Label": [0] * len(benign_queries)
})

# === Load + Merge ===
print(f"📂 Loading dataset: {DATA_PATH}")
df = pd.read_csv(DATA_PATH)
original_len = len(df)
df = pd.concat([df, aug_df, benign_df], ignore_index=True)
df.drop_duplicates(inplace=True)
df.dropna(subset=['Query', 'Label'], inplace=True)

print(f"✅ Original Samples: {original_len} → After Augmentation: {len(df)}")

# === Preprocessing ===
X = df['Query'].astype(str)
y = df['Label']

# === TF-IDF ===
vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=3000)
X_vec = vectorizer.fit_transform(X)

# === Split ===
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

print("🧠 Training model with full augmented SQLi payloads...")
start = time.time()
search.fit(X_train, y_train)
end = time.time()

# === Evaluation ===
best_model = search.best_estimator_
y_pred = best_model.predict(X_test)
acc = accuracy_score(y_test, y_pred)

print(f"\n🏆 Best Parameters: {search.best_params_}")
print(f"🧠 Best CV Score: {search.best_score_:.4f}")
print(f"⏱️ Time Taken: {(end-start)/60:.2f} mins")
print(f"✅ Test Accuracy: {acc:.4f}")
print("🧾 Confusion Matrix:\n", confusion_matrix(y_test, y_pred))

# === Debug: Show Misclassifications ===
wrong = X_test[(y_pred != y_test)]
print(f"\n⚠️ Misclassified Samples: {len(wrong)}")
for i in range(min(10, len(wrong))):
    print("🚫", X.iloc[wrong.index[i]], "| True:", y_test.iloc[wrong.index[i]], "| Pred:", y_pred[wrong.index[i]])

# === Save Artifacts ===
with open(os.path.join(OUTPUT_DIR, "piyushm2_model.pkl"), "wb") as f:
    pickle.dump(best_model, f)

with open(os.path.join(OUTPUT_DIR, "piyushm2_vectorizer.pkl"), "wb") as f:
    pickle.dump(vectorizer, f)

with open(os.path.join(OUTPUT_DIR, "piyushm2_feature.pkl"), "wb") as f:
    pickle.dump(vectorizer.get_feature_names_out().tolist(), f)

print("✅ Model, Vectorizer, and Features saved to:", OUTPUT_DIR)
