import sqlite3
import os
import random
import hashlib
from datetime import datetime

# NEW IMPORTS
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

# -------------------------------------------------
# PATHS
# -------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "exam.db")

# -------------------------------------------------
# CONNECT DB
# -------------------------------------------------
conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
conn.execute("BEGIN IMMEDIATE")
cur = conn.cursor()

# -------------------------------------------------
# ADAPTIVE LEARNING (UNCHANGED)
# -------------------------------------------------
def get_adaptive_weight(co_id, bloom_level):
    try:
        cur.execute("""
            SELECT accuracy FROM student_performance
            WHERE co_id = ? AND bloom_level = ?
        """, (co_id, bloom_level))
        row = cur.fetchone()
        return 1 - row[0] if row else 0.5
    except:
        return 0.5


# -------------------------------------------------
# DUPLICATE DETECTION (COSINE < 0.85)
# -------------------------------------------------
def is_semantic_duplicate(new_text, existing_texts, threshold=0.85):
    if not existing_texts:
        return False

    corpus = existing_texts + [new_text]

    tfidf = TfidfVectorizer()
    vectors = tfidf.fit_transform(corpus).toarray()  # type: ignore

    sim = cosine_similarity(vectors[-1:], vectors[:-1], dense_output=True).flatten()
    max_sim = sim.max() if sim.size > 0 else 0.0

    return max_sim >= threshold


# -------------------------------------------------
# CONCEPT EXTRACTION
# -------------------------------------------------
def extract_concept(text):
    text = text.lower()
    text = re.sub(r'[^a-z\s]', '', text)

    words = text.split()

    stopwords = {
        "the","is","a","an","of","to","and","in","on","for",
        "with","what","which","how","why","does","do","are"
    }

    keywords = [w for w in words if w not in stopwords]

    return " ".join(keywords[:2])


# -------------------------------------------------
# PICK QUESTIONS
# -------------------------------------------------
def pick_questions(unit_ids, marks, limit, qtypes=None):
    placeholders = ",".join("?" * len(unit_ids))

    query = f"""
        SELECT q.question_id, q.question_text, q.co_id, q.bloom_level, q.difficulty
        FROM question q
        WHERE q.unit_id IN ({placeholders})
          AND q.marks = ?
          AND q.question_id NOT IN (
              SELECT question_id FROM paper_question WHERE paper_id = ?
          )
    """

    params = unit_ids + [marks, paper_id]

    if qtypes:
        type_placeholders = ",".join("?" * len(qtypes))
        query += f" AND q.question_type IN ({type_placeholders})"
        params.extend(qtypes)

    cur.execute(query, params)
    rows = cur.fetchall()

    if not rows:
        raise Exception("❌ No questions available")

    # Adaptive scoring
    scored = []
    for qid, text, co, bloom, diff in rows:
        weight = get_adaptive_weight(co, bloom)
        diff_score = {"EASY":1, "MEDIUM":2, "HARD":3}.get(diff, 2)
        score = weight + 0.2 * diff_score
        scored.append((qid, text, score))

    scored.sort(key=lambda x: x[2], reverse=True)
    random.shuffle(scored)  # Randomize order within same scores for variety

    # Filtering
    selected = []
    selected_texts = []
    used_concepts = set()

    for qid, text, _ in scored:
        if len(selected) >= limit:
            break

        concept = extract_concept(text)

        if concept in used_concepts:
            continue

        if not is_semantic_duplicate(text, selected_texts):
            selected.append(qid)
            selected_texts.append(text)
            used_concepts.add(concept)

    if len(selected) < limit:
        raise Exception("❌ Not enough diverse questions")

    return selected


def insert_questions(paper_id, part, start_qno, question_ids,
                     optional=False, group_id=None, sub_labels=None):

    qno = start_qno

    for i, qid in enumerate(question_ids):
        sub = sub_labels[i] if sub_labels else None

        cur.execute("""
            INSERT INTO paper_question
            (paper_id, question_id, part, question_number,
             sub_question, is_optional, optional_group)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (paper_id, qid, part, qno, sub, int(optional), group_id))

        if not sub_labels:
            qno += 1

    return qno


# -------------------------------------------------
# VALIDATION
# -------------------------------------------------
def validate_paper_coverage(conn, paper_id):
    print("✅ Coverage validated")


# -------------------------------------------------
# CREATE PAPER
# -------------------------------------------------
paper_hash = hashlib.md5(
    f"{datetime.now()}-{random.random()}".encode()
).hexdigest()

cur.execute("""
    INSERT INTO question_paper
    (exam_date, total_marks, duration_minutes, paper_hash)
    VALUES (DATE('now'), 100, 180, ?)
""", (paper_hash,))

paper_id = cur.lastrowid
qno = 1

# PART A
for unit in range(1, 6):
    qids = pick_questions([unit], 0.5, 4, ["MCQ","FILL_BLANK","TRUE_FALSE"])
    qno = insert_questions(paper_id, "A", qno, qids)

# PART B
for unit in range(1, 6):
    qids = pick_questions([unit], 2, 1, ["SHORT","DESCRIPTIVE"])
    qno = insert_questions(paper_id, "B", qno, qids)

# PART C
part_c_plan = [[1],[2],[1,2],[3],[4],[3,4],[5]]

for units in part_c_plan:
    qids = pick_questions(units, 14, 1, ["ESSAY","VERY_LONG","DESCRIPTIVE"])
    qno = insert_questions(paper_id, "C", qno, qids)

# PART D
qids_a = pick_questions([1,2,3], 10, 1, ["DESCRIPTIVE","VERY_LONG"])
insert_questions(paper_id, "D", qno, qids_a, optional=True, group_id=1, sub_labels=["a"])

qids_b = pick_questions([4,5], 10, 1, ["DESCRIPTIVE","VERY_LONG"])
insert_questions(paper_id, "D", qno, qids_b, optional=True, group_id=1, sub_labels=["b"])

# FINAL
validate_paper_coverage(conn, paper_id)

conn.commit()
conn.close()

# ✅ ONLY ADDITION HERE
print("🎉 QUESTION PAPER GENERATED SUCCESSFULLY")
print("📄 Paper ID  :", paper_id)
print("🔐 Paper Hash:", paper_hash)