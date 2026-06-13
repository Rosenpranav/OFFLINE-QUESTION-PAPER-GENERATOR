import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "exam.db")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# course_id = 1 (from insert_course.py)
units = [
    (1, 1, 1, "Introduction to Neural Networks"),
    (2, 1, 2, "Deep Learning Basics"),
    (3, 1, 3, "Convolutional Neural Networks"),
    (4, 1, 4, "Recurrent & Generative Models"),
    (5, 1, 5, "Advanced Deep Learning")
]

cur.executemany("""
    INSERT INTO unit (unit_id, course_id, unit_number, unit_title)
    VALUES (?, ?, ?, ?)
""", units)

conn.commit()
conn.close()

print("✅ Units inserted successfully")
