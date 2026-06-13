import sqlite3
import os
import numpy as np
from sentence_transformers import SentenceTransformer

# Config
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "exam.db")
MODEL_NAME = "all-MiniLM-L6-v2"
MODEL_CACHE = os.path.join(BASE_DIR, "..", "models")
EMBEDDING_DTYPE = np.float32

# Load model (offline-safe if model files present in models folder)
def load_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(MODEL_NAME, cache_folder=MODEL_CACHE)

model = None

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("SELECT question_id, question_text FROM question WHERE embedding IS NULL OR embedding = ''")
rows = cur.fetchall()

print(f"Found {len(rows)} questions without embeddings.")

for qid, text in rows:
    if model is None:
        model = load_model()
    vec = np.array(model.encode(text, convert_to_numpy=True, normalize_embeddings=True), dtype=EMBEDDING_DTYPE)
    blob = vec.tobytes()
    cur.execute("UPDATE question SET embedding = ? WHERE question_id = ?", (blob, qid))
    print(f"Updated question_id={qid}")

conn.commit()
conn.close()

print("Done. Consider running this inside a virtualenv with sentence-transformers installed.")
