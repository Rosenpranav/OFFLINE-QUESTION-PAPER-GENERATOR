import sqlite3
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "exam.db")
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
# List tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("📦 Tables:", cur.fetchall())
# Count rows in paper_question
cur.execute("SELECT COUNT(*) FROM paper_question")
print("🧮 Rows in paper_question:", cur.fetchone()[0])
# Count rows in question
cur.execute("SELECT COUNT(*) FROM question")
print("🧮 Rows in question:", cur.fetchone()[0])
conn.close()
