import sqlite3
import os
import textwrap
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

# -------------------------------------------------
# CONFIGURATION
# -------------------------------------------------
SHOW_DIFFICULTY = False
COURSE_CODE = "21AD521"   # ✅ Course Code

# -------------------------------------------------
# PATH SETUP
# -------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "exam.db")
PDF_PATH = os.path.join(BASE_DIR, "Question_Paper.pdf")

# -------------------------------------------------
# CONNECT DB
# -------------------------------------------------
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# -------------------------------------------------
# GET LATEST GENERATED PAPER
# -------------------------------------------------
cur.execute("""
    SELECT paper_id, paper_hash
    FROM question_paper
    ORDER BY paper_id DESC
    LIMIT 1
""")

row = cur.fetchone()

if not row:
    raise Exception("❌ No question paper found.")

paper_id, paper_hash = row

# -------------------------------------------------
# CHECK QUESTIONS EXIST
# -------------------------------------------------
cur.execute("""
    SELECT COUNT(*)
    FROM paper_question
    WHERE paper_id = ?
""", (paper_id,))

if cur.fetchone()[0] == 0:
    raise Exception("❌ No questions found.")

# -------------------------------------------------
# FETCH QUESTIONS
# -------------------------------------------------
cur.execute("""
    SELECT
        pq.part,
        pq.question_number,
        pq.sub_question,
        pq.is_optional,
        pq.optional_group,
        q.question_text,
        q.difficulty,
        q.bloom_level
    FROM paper_question pq
    JOIN question q ON pq.question_id = q.question_id
    WHERE pq.paper_id = ?
    ORDER BY pq.part, pq.question_number, pq.sub_question
""", (paper_id,))

rows = cur.fetchall()
conn.close()

# -------------------------------------------------
# PDF SETUP
# -------------------------------------------------
c = canvas.Canvas(PDF_PATH, pagesize=A4)
width, height = A4

LEFT = 2 * cm
RIGHT = width - 2 * cm
CENTER = width / 2
TOP = height - 2 * cm
BOTTOM = 2 * cm

LINE_HEIGHT = 14
y = TOP

# ✅ PAGE TRACKING
page_number = 1


def draw_footer():
    """Draw footer with page number and paper ID"""
    c.setFont("Times-Roman", 10)

    # Center footer → Page Number
    page_text = f"Page {page_number}"
    text_width = c.stringWidth(page_text, "Times-Roman", 10)
    c.drawString(CENTER - text_width / 2, 1.5 * cm, page_text)

    # Right footer → Paper ID
    right_text = f"Paper ID: {paper_id}"
    text_width = c.stringWidth(right_text, "Times-Roman", 10)
    c.drawString(RIGHT - text_width, 1.5 * cm, right_text)


def new_page():
    global y, page_number
    draw_footer()
    c.showPage()
    page_number += 1
    y = TOP


def draw_center(text, bold=False):
    global y
    c.setFont("Times-Bold" if bold else "Times-Roman", 12)
    text_width = c.stringWidth(text, "Times-Bold" if bold else "Times-Roman", 12)
    c.drawString(CENTER - text_width / 2, y, text)
    y -= LINE_HEIGHT


def draw_lr(left_text, right_text):
    global y
    c.setFont("Times-Roman", 12)
    c.drawString(LEFT, y, left_text)
    text_width = c.stringWidth(right_text, "Times-Roman", 12)
    c.drawString(RIGHT - text_width, y, right_text)
    y -= LINE_HEIGHT


def draw(text, bold=False, indent=0):
    global y
    c.setFont("Times-Bold" if bold else "Times-Roman", 12)
    wrap_width = int((RIGHT - LEFT - indent) / 6)

    for line in textwrap.wrap(text, wrap_width):
        if y < BOTTOM:
            new_page()
        c.drawString(LEFT + indent, y, line)
        y -= LINE_HEIGHT


# -------------------------------------------------
# HEADER
# -------------------------------------------------
draw_center("END SEMESTER EXAMINATION", bold=True)
draw_center("B.E / B.Tech Degree Examination", bold=True)
draw_center("Artificial Intelligence and Data Science", bold=True)

# ✅ Course Code moved here
draw_center(f"Course Code: {COURSE_CODE}", bold=True)

y -= 5

draw_lr(f"Paper ID : {paper_id}", f"Paper Hash : {paper_hash}")
draw_lr("Time : 3 Hours", "Maximum Marks : 100")

draw("-" * 95)

# -------------------------------------------------
# QUESTIONS
# -------------------------------------------------
current_part = None
printed_or_group = set()

for part, qno, sub, is_opt, opt_group, text, difficulty, bloom in rows:

    if part != current_part:
        y -= 5

        if part == "A":
            draw("PART A (20 × 0.5 = 10)", bold=True)
            draw("Answer ALL questions", bold=True)

        elif part == "B":
            draw("PART B (5 × 2 = 10)", bold=True)
            draw("Answer ALL questions", bold=True)

        elif part == "C":
            draw("PART C (Answer ANY FIVE) (5 × 14 = 70)", bold=True)

        elif part == "D":
            draw("PART D (Answer ANY ONE) (1 × 10 = 10)", bold=True)

        draw("-" * 95)
        current_part = part
        printed_or_group.clear()

    label = str(qno)
    if sub:
        label += f"({sub})"

    if SHOW_DIFFICULTY:
        question_text = f"{label}. {text} [{difficulty}]"
    else:
        question_text = f"{label}. {text}"

    if part == "D" and is_opt:
        if opt_group not in printed_or_group:
            draw(question_text, indent=10)
            printed_or_group.add(opt_group)
        else:
            draw("OR", bold=True, indent=20)
            draw(question_text, indent=10)
    else:
        draw(question_text, indent=10)

# -------------------------------------------------
# FINAL FOOTER
# -------------------------------------------------
draw_footer()

# -------------------------------------------------
# SAVE PDF
# -------------------------------------------------
c.save()

print("✅ PDF Generated Successfully")
print("📄 Paper ID:", paper_id)
print("📁 File:", PDF_PATH)