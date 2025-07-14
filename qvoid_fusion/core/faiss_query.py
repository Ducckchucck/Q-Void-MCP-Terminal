import faiss
import pickle
from sentence_transformers import SentenceTransformer

# === Paths ===
INDEX_PATH = "qvoid_fusion/core/faiss_index.idx"
TEXTS_PATH = "qvoid_fusion/core/texts.pkl"

# === Load Index and Texts ===
print("📥 Loading index and texts...")
index = faiss.read_index(INDEX_PATH)

with open(TEXTS_PATH, "rb") as f:
    texts = pickle.load(f)

model = SentenceTransformer("all-MiniLM-L6-v2")

def search(query, top_k=5):
    vec = model.encode([query])
    distances, indices = index.search(vec, top_k)
    print("\n🔍 Top Matches:")
    for i, idx in enumerate(indices[0]):
        print(f"{i+1}. {texts[idx]} (score: {distances[0][i]:.4f})")

# === Input ===
while True:
    user_input = input("\nEnter a security question or 'exit': ")
    if user_input.lower() == "exit":
        break
    search(user_input)
