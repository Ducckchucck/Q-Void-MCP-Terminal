import faiss
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import os
import pickle

# === Paths ===
DATA_PATH = "data/payload_knowledge.csv"
VEC_PATH = "qvoid_fusion/core/faiss_index.idx"
VEC_META = "qvoid_fusion/core/texts.pkl"
VEC_TFIDF = "qvoid_fusion/core/faiss_vectorizer.pkl"

# === Train and Save Index (Run once) ===
def train_index():
    df = pd.read_csv(DATA_PATH)
    texts = df['text'].astype(str).tolist()

    # Vectorize
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=3000)
    X = vectorizer.fit_transform(texts).toarray()

    # Build FAISS Index
    index = faiss.IndexFlatL2(X.shape[1])
    index.add(X)

    # Save index and metadata
    faiss.write_index(index, VEC_PATH)
    with open(VEC_META, "wb") as f:
        pickle.dump(df.to_dict(orient="records"), f)
    with open(VEC_TFIDF, "wb") as f:
        pickle.dump(vectorizer, f)

    print("✅ FAISS index built and saved.")

# === Query from FAISS ===
def query_similar(text_input, top_k=5):
    if not all(os.path.exists(p) for p in [VEC_PATH, VEC_META, VEC_TFIDF]):
        print("❌ FAISS index not found. Please run train_index() first.")
        return

    # Load artifacts
    index = faiss.read_index(VEC_PATH)
    with open(VEC_META, "rb") as f:
        metadata = pickle.load(f)
    with open(VEC_TFIDF, "rb") as f:
        vectorizer = pickle.load(f)

    vec = vectorizer.transform([text_input]).toarray()
    D, I = index.search(vec, top_k)

    print(f"\n🔍 Top {top_k} Similar Entries for: \"{text_input}\"")
    for rank, idx in enumerate(I[0]):
        if idx >= len(metadata): continue
        entry = metadata[idx]
        print(f"{rank+1}. \"{entry['text']}\" ➤ Label: {entry['label']}")

# === For Testing ===
if __name__ == "__main__":
    train_index()
    query_similar("' OR 1=1--")
