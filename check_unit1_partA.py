import sqlite3, os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "exam.db")
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("""
    SELECT question_type, marks, COUNT(*)
    FROM question
    WHERE unit_id = 1
    GROUP BY question_type, marks
""")
rows = cur.fetchall()
conn.close()
print("Unit-1 distribution:")
for r in rows:
    print(r)
