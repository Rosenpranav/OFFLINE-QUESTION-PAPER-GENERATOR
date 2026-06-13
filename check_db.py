import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(BASE_DIR, "database", "exam.db")

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# List all tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cur.fetchall()

print("📦 Tables in database:")
for t in tables:
    print(" -", t[0])

# Check questions
print("\n📝 Questions in database:")
cur.execute("SELECT question_id, question_text, unit_id, marks FROM question;")
rows = cur.fetchall()

if not rows:
    print("❌ No questions found")
else:
    for r in rows:
        print(r)

conn.close()
