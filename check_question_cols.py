import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "exam.db")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("PRAGMA table_info(question)")
cols = cur.fetchall()
print("Columns in 'question':")
for c in cols:
    # (cid, name, type, notnull, dflt_value, pk)
    print(f" - {c[1]} ({c[2]})")
conn.close()
