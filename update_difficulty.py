import sqlite3
import os

# -------------------------------------------------
# PATHS
# -------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "exam.db")

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

# -------------------------------------------------
# UPDATE DIFFICULTY FOR EXISTING QUESTIONS
# -------------------------------------------------
def update_difficulty():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    try:
        # Get all questions without difficulty
        cur.execute("""
            SELECT question_id, question_text
            FROM question
            WHERE difficulty IS NULL OR difficulty = ''
        """)

        questions = cur.fetchall()
        updated = 0

        for qid, qtext in questions:
            difficulty = infer_difficulty(qtext)
            cur.execute("""
                UPDATE question
                SET difficulty = ?
                WHERE question_id = ?
            """, (difficulty, qid))
            updated += 1

        conn.commit()
        print(f"✅ Updated difficulty for {updated} questions")

    except Exception as e:
        print(f"❌ Error updating difficulty: {e}")
        conn.rollback()

    finally:
        conn.close()

if __name__ == "__main__":
    update_difficulty()