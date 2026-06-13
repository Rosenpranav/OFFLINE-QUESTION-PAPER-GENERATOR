import sqlite3
import os

# -------------------------------------------------
# PATH SETUP
# -------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "exam.db")

# -------------------------------------------------
# CONNECT DB
# -------------------------------------------------
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

print("\n🔧 NORMALIZING QUESTION BANK")
print("=" * 50)

# -------------------------------------------------
# STEP 1: TRIM & UPPERCASE question_type
# -------------------------------------------------
cur.execute("""
    UPDATE question
    SET question_type = UPPER(TRIM(question_type))
""")
print("✅ Trimmed & uppercased question_type")

# -------------------------------------------------
# STEP 2: NORMALIZATION MAP (AUTHORITATIVE)
# -------------------------------------------------
NORMALIZATION_MAP = {
    # ---- OBJECTIVE ----
    "MCQ QUESTION": "MCQ",
    "MULTIPLE CHOICE": "MCQ",
    "MULTIPLE CHOICE QUESTION": "MCQ",
    "MCQS": "MCQ",
    "MCQ": "MCQ",

    "FILL IN THE BLANK": "FILL_BLANK",
    "FILL IN THE BLANKS": "FILL_BLANK",
    "FILL_BLANK": "FILL_BLANK",

    "TRUE OR FALSE": "TRUE_FALSE",
    "TRUE/FALSE": "TRUE_FALSE",
    "TRUE_FALSE": "TRUE_FALSE",

    # ---- SHORT ----
    "SHORT": "SHORT",
    "SHORT ANSWER": "SHORT",
    "SHORT ANSWER QUESTION": "SHORT",

    # ---- ESSAY (PART C) ----
    "ESSAY": "ESSAY",
    "LONG ANSWER": "ESSAY",
    "LONG ANSWER QUESTION": "ESSAY",

    # ---- VERY LONG / PART D ----
    "VERY LONG": "VERY_LONG",
    "VERY LONG ANSWER": "VERY_LONG",
    "VERY_LONG": "VERY_LONG",

    "DESCRIPTIVE": "DESCRIPTIVE",
    "DESCRIPTIVE QUESTION": "DESCRIPTIVE"
}

updated_types = 0

for old, new in NORMALIZATION_MAP.items():
    cur.execute("""
        UPDATE question
        SET question_type = ?
        WHERE question_type = ?
    """, (new, old))
    updated_types += cur.rowcount

print(f"✅ Normalized question_type values ({updated_types} rows updated)")

# -------------------------------------------------
# STEP 3: NORMALIZE MARKS (CRITICAL FIX)
# -------------------------------------------------
# Convert integer-like marks to float correctly
cur.execute("""
    UPDATE question
    SET marks = 0.5
    WHERE marks IN ('.5', '0.50', '0.500', '1/2')
""")

cur.execute("""
    UPDATE question
    SET marks = 0.5
    WHERE marks = 1 AND question_type IN ('MCQ','FILL_BLANK','TRUE_FALSE')
""")

cur.execute("""
    UPDATE question
    SET marks = 2
    WHERE marks IN ('2.0', '2.00')
""")

cur.execute("""
    UPDATE question
    SET marks = 14
    WHERE marks IN ('14.0', '14.00')
""")

print("✅ Normalized marks values")

# -------------------------------------------------
# STEP 4: REPORT FINAL DISTRIBUTION
# -------------------------------------------------
print("\n📊 FINAL DISTRIBUTION (unit_id, question_type, marks):")
print("-" * 50)

cur.execute("""
    SELECT unit_id, question_type, marks, COUNT(*)
    FROM question
    GROUP BY unit_id, question_type, marks
    ORDER BY unit_id, question_type, marks
""")

rows = cur.fetchall()
for u, qt, m, c in rows:
    print(f"Unit {u:<2} | {qt:<12} | {m:<4} | {c}")

# -------------------------------------------------
# STEP 5: COMMIT & CLOSE
# -------------------------------------------------
conn.commit()
conn.close()

print("\n🎉 NORMALIZATION COMPLETED SUCCESSFULLY")
print("👉 Now run: python database/generate_paper.py")
