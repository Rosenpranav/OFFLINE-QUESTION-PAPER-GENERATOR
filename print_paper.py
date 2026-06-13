import sqlite3
import os

# -------------------------------------------------
# Path handling
# -------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "exam.db")

# -------------------------------------------------
# Connect to DB
# -------------------------------------------------
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# -------------------------------------------------
# Determine the latest generated paper (source of truth)
# -------------------------------------------------
cur.execute("SELECT MAX(paper_id) FROM question_paper")
row = cur.fetchone()
if not row or row[0] is None:
    raise Exception("❌ No question paper found. Run generate_paper.py first.")

paper_id = row[0]

# -------------------------------------------------
# Fetch questions for that paper
# -------------------------------------------------
cur.execute("""
    SELECT
        pq.part,
        pq.question_number,
        pq.sub_question,
        pq.is_optional,
        pq.optional_group,
        q.question_text,
        q.marks
    FROM paper_question pq
    JOIN question q ON pq.question_id = q.question_id
    WHERE pq.paper_id = ?
    ORDER BY
        pq.part,
        pq.question_number,
        pq.sub_question
""", (paper_id,))

rows = cur.fetchall()
conn.close()

# -------------------------------------------------
# Print paper
# -------------------------------------------------
current_part = None
printed_or_groups = set()

for part, qno, sub, is_opt, opt_group, text, marks in rows:

    # Print part heading once
    if part != current_part:
        print(f"\n--- PART {part} ---")
        current_part = part
        printed_or_groups.clear()

    # Build question label
    label = str(qno)
    if sub is not None:
        label += sub   # a / b

    # Handle OR logic
    if is_opt == 1:
        if opt_group not in printed_or_groups:
            print(f"{label}. {text} ({marks} marks)")
            printed_or_groups.add(opt_group)
        else:
            print("   OR")
            print(f"{label}. {text} ({marks} marks)")
    else:
        print(f"{label}. {text} ({marks} marks)")
