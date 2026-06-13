import sqlite3
import os
import sys

# -------------------------------------------------
# PATH CONFIGURATION (OPTION 2 FIX)
# init_db.py is INSIDE database/
# -------------------------------------------------

# Go UP one level to project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_DIR = os.path.join(BASE_DIR, "database")
SQL_DIR = os.path.join(BASE_DIR, "sql")
DB_PATH = os.path.join(DB_DIR, "exam.db")
# Prefer fixed schema if present (helps when schema.sql is corrupted)
SCHEMA_PATH = os.path.join(SQL_DIR, "schema.sql")
FIXED_SCHEMA_PATH = os.path.join(SQL_DIR, "schema_fixed.sql")
if os.path.exists(FIXED_SCHEMA_PATH):
    print("Using fixed schema file:", FIXED_SCHEMA_PATH)
    SCHEMA_PATH = FIXED_SCHEMA_PATH

# -------------------------------------------------
# SAFETY CHECKS
# -------------------------------------------------
if not os.path.exists(SCHEMA_PATH):
    print("❌ schema.sql not found at:", SCHEMA_PATH)
    sys.exit(1)

os.makedirs(DB_DIR, exist_ok=True)

# -------------------------------------------------
# INITIALIZE DATABASE
# -------------------------------------------------
def init_db():
    print("📦 Initializing database...")
    print("📁 Database path:", DB_PATH)
    print("📄 Schema path  :", SCHEMA_PATH)

    conn = sqlite3.connect(DB_PATH)

    try:
        # 🔐 CRITICAL: Enforce foreign keys
        conn.execute("PRAGMA foreign_keys = ON")

        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        conn.executescript(schema_sql)
        conn.commit()

        # -------------------------------------------------
        # Migration: ensure `embedding` column exists in question
        # -------------------------------------------------
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(question);")
        cols = [r[1] for r in cur.fetchall()]

        if "embedding" not in cols:
            print("🔧 Migrating: adding 'embedding' column to 'question' table...")
            try:
                conn.execute("ALTER TABLE question ADD COLUMN embedding BLOB;")
                conn.commit()
                print("✅ Migration applied: 'embedding' column added.")
            except sqlite3.Error as me:
                print("⚠️ Migration failed:", me)
                # Not fatal: continue

        if "difficulty" not in cols:
            print("🔧 Migrating: adding 'difficulty' column to 'question' table...")
            try:
                conn.execute("ALTER TABLE question ADD COLUMN difficulty TEXT CHECK (difficulty IN ('EASY','MEDIUM','HARD'));")
                conn.commit()
                print("✅ Migration applied: 'difficulty' column added.")
            except sqlite3.Error as me:
                print("⚠️ Migration failed:", me)
                # Not fatal: continue

        print("✅ Database initialized successfully")

    except sqlite3.Error as e:
        print("❌ Database initialization failed")
        print("Reason:", e)
        conn.rollback()
        sys.exit(1)

    finally:
        conn.close()

# -------------------------------------------------
# ENTRY POINT
# -------------------------------------------------
if __name__ == "__main__":
    init_db()
