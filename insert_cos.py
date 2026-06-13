import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "exam.db")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Course Outcomes as per Lesson Plan
cos = [
    (1, "1", "Understand the structure and function of neural networks"),
    (1, "2", "Learn the backpropagation algorithm and issues like vanishing gradients"),
    (1, "3", "Implement convolutional neural networks for image classification"),
    (1, "4", "Study advanced architectures such as LSTM, GRU, autoencoders, and GANs"),
    (1, "5", "Apply deep learning techniques in image segmentation, object detection, and NLP"),
]

cur.executemany("""
INSERT INTO course_outcome (course_id, co_code, description)
VALUES (?, ?, ?)
""", cos)

conn.commit()
conn.close()

print("✅ Course Outcomes inserted as per Lesson Plan")
