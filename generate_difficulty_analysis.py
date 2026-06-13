import sqlite3
import os
import re
from collections import Counter, defaultdict
from typing import List, Any
from io import BytesIO

import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors

from sentence_transformers import SentenceTransformer, util
import torch

# -------------------------------------------------
# MODEL
# -------------------------------------------------
model = SentenceTransformer('all-MiniLM-L6-v2')

# -------------------------------------------------
# PATHS
# -------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "exam.db")
PDF_PATH = os.path.join(BASE_DIR, "reports", "final_report.pdf")

os.makedirs(os.path.dirname(PDF_PATH), exist_ok=True)

# -------------------------------------------------
# TEXT FUNCTIONS
# -------------------------------------------------
def clean_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()

def enhance(text: str) -> str:
    text = clean_text(text)
    if not text.endswith("?") and not text.endswith("."):
        text += "."
    return text

# -------------------------------------------------
# BLOOM LOGIC
# -------------------------------------------------
def classify_bloom(text: str) -> str:
    text = text.lower()

    create = ["design", "develop", "propose", "construct", "formulate"]
    evaluate = ["evaluate", "justify", "critique", "assess"]
    analyze = ["analyze", "compare", "differentiate", "examine", "why", "discuss"]
    apply = ["solve", "compute", "calculate", "implement", "demonstrate", "algorithm", "working"]
    understand = ["explain", "describe", "summarize", "illustrate"]
    remember = ["define", "list", "state", "identify", "what is"]

    if any(k in text for k in create):
        return "CREATE"
    if any(k in text for k in evaluate):
        return "EVALUATE"
    if any(k in text for k in analyze):
        return "ANALYZE"
    if any(k in text for k in apply):
        return "APPLY"
    if any(k in text for k in understand):
        return "UNDERSTAND"
    if any(k in text for k in remember):
        return "REMEMBER"

    wc = len(text.split())
    if wc <= 6:
        return "REMEMBER"
    elif wc <= 12:
        return "UNDERSTAND"
    elif wc <= 20:
        return "APPLY"
    else:
        return "ANALYZE"

# -------------------------------------------------
def compute_difficulty(bloom: str, text: str) -> float:
    base = {
        "REMEMBER": 1,
        "UNDERSTAND": 2,
        "APPLY": 3,
        "ANALYZE": 4,
        "EVALUATE": 5,
        "CREATE": 6
    }[bloom]
    return base + min(len(text.split()) / 10, 2)

def get_embedding(text: str) -> torch.Tensor:
    emb = model.encode(text)
    if not isinstance(emb, torch.Tensor):
        emb = torch.tensor(emb)
    return emb

def ambiguity(original: str, improved: str):
    emb1 = get_embedding(original)
    emb2 = get_embedding(improved)
    sim = float(util.cos_sim(emb1, emb2).item())
    sim = max(0.0, min(1.0, sim))
    return 1 - sim, sim

def detect_issues(text: str, sim: float, amb: float) -> str:
    issues = []
    if sim < 0.75:
        issues.append("Meaning Drift")
    if amb > 0.4:
        issues.append("Ambiguous")
    if len(text.split()) < 5:
        issues.append("Too Short")
    return "Good" if not issues else ", ".join(issues)

# -------------------------------------------------
def create_graph(x, y):
    buffer = BytesIO()
    plt.figure()
    plt.bar(x, y)
    plt.tight_layout()
    plt.savefig(buffer, format='png')
    plt.close()
    buffer.seek(0)
    return buffer

# -------------------------------------------------
# DB FETCH
# -------------------------------------------------
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("SELECT paper_id, paper_hash FROM question_paper ORDER BY paper_id DESC LIMIT 1")
paper_id, paper_hash = cur.fetchone()

cur.execute("""
SELECT pq.part, pq.question_number, pq.sub_question,
       q.question_text, q.difficulty,
       q.co_id, q.unit_id
FROM paper_question pq
JOIN question q ON pq.question_id = q.question_id
WHERE pq.paper_id = ?
ORDER BY pq.part, pq.question_number
""", (paper_id,))

rows = cur.fetchall()
conn.close()

# -------------------------------------------------
# ANALYTICS
# -------------------------------------------------
unit_counts = Counter()
bloom_counts = Counter()
section_difficulty = defaultdict(list)

total_sim = total_amb = total_diff = 0.0

for part, _, _, text, _, _, unit in rows:
    unit_counts[unit] += 1

    enhanced = enhance(text)
    amb, sim = ambiguity(text, enhanced)
    bloom = classify_bloom(enhanced)
    diff_val = compute_difficulty(bloom, enhanced)

    bloom_counts[bloom] += 1
    section_difficulty[part].append(diff_val)

    total_sim += sim
    total_amb += amb
    total_diff += diff_val

total = len(rows)

avg_sim = total_sim / total if total else 0
avg_amb = total_amb / total if total else 0
avg_diff = total_diff / total if total else 0
difficulty_percent = (avg_diff / 6) * 100 if total else 0

# -------------------------------------------------
# PDF SETUP
# -------------------------------------------------
doc = SimpleDocTemplate(PDF_PATH, pagesize=A4)
styles = getSampleStyleSheet()

question_style = ParagraphStyle('Q', parent=styles['Normal'], fontSize=9, leading=13)
small = ParagraphStyle('S', parent=styles['Normal'], fontSize=9, leading=11)

story: List[Any] = []

# -------------------------------------------------
# TITLE
# -------------------------------------------------
story.append(Paragraph("<b>ADVANCED ANALYTICS REPORT</b>", styles["Title"]))
story.append(Spacer(1, 6))

story.append(Paragraph(f"<b>Paper ID:</b> {str(paper_id)}", styles["Normal"]))
story.append(Paragraph(f"<b>Paper Hash:</b> {str(paper_hash)}", styles["Normal"]))
story.append(Spacer(1, 12))

# -------------------------------------------------
# OVERALL TABLE
# -------------------------------------------------
overall_table = [
    ["Metric", "Value"],
    ["Avg Similarity", f"{float(avg_sim):.2f}"],
    ["Avg Ambiguity", f"{float(avg_amb):.2f}"],
    ["Avg Difficulty", f"{float(avg_diff):.2f}"],
    ["Difficulty %", f"{float(difficulty_percent):.2f}%"]
]

story.append(Paragraph("<b>Overall Analysis</b>", styles["Heading2"]))
story.append(Table(overall_table))
story.append(Spacer(1, 12))

# -------------------------------------------------
# UNIT DISTRIBUTION
# -------------------------------------------------
unit_table = [["Unit", "Count", "%"]]
for u, c in unit_counts.items():
    perc = (c / total) * 100 if total else 0
    unit_table.append([f"U{str(u)}", str(c), f"{perc:.2f}%"])

story.append(Paragraph("<b>Unit Distribution</b>", styles["Heading2"]))
story.append(Table(unit_table))
story.append(Image(create_graph(list(unit_counts.keys()), list(unit_counts.values())), width=400, height=200))
story.append(Spacer(1, 12))

# -------------------------------------------------
# BLOOM DISTRIBUTION
# -------------------------------------------------
bloom_table = [["Level", "Count", "%"]]
for b in ["REMEMBER","UNDERSTAND","APPLY","ANALYZE","EVALUATE","CREATE"]:
    c = bloom_counts[b]
    perc = (c / total) * 100 if total else 0
    bloom_table.append([str(b), str(c), f"{perc:.2f}%"])

story.append(Paragraph("<b>Bloom Distribution</b>", styles["Heading2"]))
story.append(Table(bloom_table))
story.append(Image(create_graph(list(bloom_counts.keys()), list(bloom_counts.values())), width=400, height=200))
story.append(Spacer(1, 12))

# -------------------------------------------------
# QUESTION TABLE (FIXED FOR PYLANCE)
# -------------------------------------------------
table_data: List[List[Any]] = [["Question","CO","Unit","Bloom","Diff","Sim","Amb","Issues"]]

for part, qno, sub, text, _, co, unit in rows:
    label = f"{qno}{f'({sub})' if sub else ''}"
    enhanced = enhance(text)

    amb, sim = ambiguity(text, enhanced)
    bloom = classify_bloom(enhanced)
    dval = compute_difficulty(bloom, enhanced)

    table_data.append([
        Paragraph(f"<b>{str(label)}.</b> {str(enhanced)}", question_style),
        Paragraph(f"CO{str(co)}", small),
        Paragraph(f"U{str(unit)}", small),
        Paragraph(str(bloom), small),
        Paragraph(f"{float(dval):.2f}", small),
        Paragraph(f"{float(sim):.2f}", small),
        Paragraph(f"{float(amb):.2f}", small),
        Paragraph(str(detect_issues(enhanced, sim, amb)), small)
    ])

qt = Table(table_data, repeatRows=1)
qt.setStyle(TableStyle([
    ("GRID",(0,0),(-1,-1),0.3,colors.black),
    ("BACKGROUND",(0,0),(-1,0),colors.lightgrey),
]))

story.append(qt)

# -------------------------------------------------
# BUILD
# -------------------------------------------------
doc.build(story)

print("✅ FINAL PERFECT REPORT GENERATED")