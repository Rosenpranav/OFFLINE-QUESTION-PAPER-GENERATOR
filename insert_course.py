import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "exam.db")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("""
    INSERT INTO course (course_code, course_name)
    VALUES (?, ?)
""", ("AI_DS", "Artificial Intelligence and Data Science"))

conn.commit()
conn.close()

print("✅ Course inserted successfully")
