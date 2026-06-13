import os
import csv
import sqlite3
from typing import Dict, Optional, List, Tuple, cast

import numpy as np
from sentence_transformers import SentenceTransformer


# -------------------------------------------------
# PATHS & CONFIG
# -------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "exam.db")
CSV_PATH = os.path.join(BASE_DIR, "data", "question_bank.csv")
MODEL_CACHE = os.path.join(BASE_DIR, "models")

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DTYPE = np.float32

VALID_MARKS = {0.5, 2.0, 10.0, 14.0}


# -------------------------------------------------
# LOAD EMBEDDING MODEL (OFFLINE SAFE)
# -------------------------------------------------
model = None
MODEL_LOADED = False

def load_model():
    global model, MODEL_LOADED
    if not MODEL_LOADED or model is None:
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(MODEL_NAME, cache_folder=MODEL_CACHE)
            MODEL_LOADED = True
        except Exception as e:
            print("⚠️ Embedding model unavailable:", e)
            model = None
            MODEL_LOADED = False
    return model


# -------------------------------------------------
# DIFFICULTY INFERENCE
# -------------------------------------------------
def infer_difficulty(question: str) -> str:
    q = question.lower()

    if any(x in q for x in (
        "part a", "part b", "part c", "part d",
        "answer all", "answer any"
    )):
        return "EASY"  # Default for structural text

    hard_keywords = (
        "derive", "prove", "analyze", "evaluate",
        "design", "justify", "algorithm",
        "architecture", "case study", "critically",
        "gan", "autoencoder", "optimization",
        "complexity", "theorem", "proof"
    )

    medium_keywords = (
        "explain", "discuss", "describe",
        "illustrate", "differentiate",
        "working", "application", "compare",
        "contrast", "advantages", "disadvantages"
    )

    if any(k in q for k in hard_keywords) or len(q) > 180:
        return "HARD"

    if any(k in q for k in medium_keywords) or len(q) > 100:
        return "MEDIUM"

    return "EASY"
QTYPE_MAP: Dict[str, str] = {
    "MCQ": "MCQ",
    "FILL BLANK": "FILL_BLANK",
    "FILL_BLANK": "FILL_BLANK",
    "TRUE OR FALSE": "TRUE_FALSE",
    "TRUE_FALSE": "TRUE_FALSE",
    "SHORT": "SHORT",
    "SHORT ANSWER": "SHORT",
    "DESCRIPTIVE": "DESCRIPTIVE",
    "ESSAY": "ESSAY",
    "LONG ANSWER": "VERY_LONG",
    "VERY LONG": "VERY_LONG",
}

BLOOM_MAP: Dict[str, str] = {
    "K1": "REMEMBER",
    "K2": "UNDERSTAND",
    "K3": "APPLY",
    "K4": "ANALYZE",
    "K5": "EVALUATE",
    "K6": "CREATE",
}


# -------------------------------------------------
# DATABASE CONNECT
# -------------------------------------------------
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()


# -------------------------------------------------
# CO GET / CREATE (PYLANCE-SAFE)
# -------------------------------------------------
def get_or_create_co(co_code: str) -> int:
    cur.execute(
        "SELECT co_id FROM course_outcome WHERE co_code = ?",
        (co_code,),
    )
    row = cur.fetchone()
    if row is not None:
        return int(row[0])

    # Insert if missing
    cur.execute(
        """
        INSERT INTO course_outcome (course_id, co_code, description)
        VALUES (1, ?, ?)
        """,
        (co_code, f"Auto-created outcome {co_code}"),
    )

    # Re-select to guarantee ID
    cur.execute(
        "SELECT co_id FROM course_outcome WHERE co_code = ?",
        (co_code,),
    )
    row = cur.fetchone()
    if row is None:
        raise RuntimeError(f"Failed to create CO {co_code}")

    return int(row[0])


# -------------------------------------------------
# CSV PROCESSING
# -------------------------------------------------
errors: List[Tuple[int, str]] = []
inserted = 0

with open(CSV_PATH, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    print("CSV Headers detected:", reader.fieldnames)

    for line_no, row in enumerate(reader, start=2):
        try:
            # ---------- QUESTION TEXT ----------
            qtext = (row.get("question_text") or "").strip()
            if not qtext:
                raise ValueError("Empty question_text")

            # ---------- UNIT ID ----------
            unit_raw = (row.get("unit_id") or "").strip()
            if not unit_raw.isdigit():
                raise ValueError(f"Invalid unit_id '{unit_raw}'")
            unit_id = int(unit_raw)

            # ---------- MARKS ----------
            marks_raw = (row.get("marks") or "").strip()
            try:
                marks = float(marks_raw)
            except ValueError:
                raise ValueError(f"Invalid marks '{marks_raw}'")
            if marks not in VALID_MARKS:
                raise ValueError(f"Marks {marks} not allowed")

            # ---------- QUESTION TYPE ----------
            qtype_raw = (row.get("question_type") or "").strip().upper()
            qtype = QTYPE_MAP.get(qtype_raw)
            if not qtype:
                raise ValueError(f"Invalid question_type '{qtype_raw}'")

            # ---------- BLOOM ----------
            bloom_raw = (row.get("bloom_level") or "").strip().upper()
            bloom = BLOOM_MAP.get(bloom_raw)
            if not bloom:
                raise ValueError(f"Invalid bloom '{bloom_raw}'")

            # ---------- CO ----------
            co_code = (row.get("co_id") or "").strip().upper()
            if not co_code:
                raise ValueError("Missing CO code")
            co_id = get_or_create_co(co_code)

            # ---------- DIFFICULTY ----------
            difficulty = infer_difficulty(qtext)

            # ---------- EMBEDDING ----------
            embedding_blob: Optional[bytes] = None
            model = load_model()
            if MODEL_LOADED and model is not None:
                vec = cast(
                    np.ndarray,
                    model.encode(
                        qtext,
                        convert_to_numpy=True,
                        normalize_embeddings=True,
                    ),
                )
                embedding_blob = vec.astype(EMBEDDING_DTYPE).tobytes()

            # ---------- INSERT QUESTION ----------
            cur.execute(
                """
                INSERT INTO question
                (unit_id, question_text, marks, question_type, co_id, bloom_level, difficulty, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (unit_id, qtext, marks, qtype, co_id, bloom, difficulty, embedding_blob),
            )

            inserted += 1

        except Exception as e:
            errors.append((line_no, str(e)))

conn.commit()
conn.close()


# -------------------------------------------------
# REPORT
# -------------------------------------------------
print(f"\n✅ Questions inserted: {inserted}")

if errors:
    print(f"\n⚠️ {len(errors)} rows skipped:")
    for ln, msg in errors[:15]:
        print(f"Line {ln}: {msg}")
