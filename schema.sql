-- =========================================================
-- OFFLINE QUESTION PAPER GENERATOR
-- FULL DATABASE SCHEMA (SQLite)
-- Language: SQLite - NOT MSSQL
-- DO NOT validate with MSSQL syntax checker
-- SQLite Syntax: PRAGMA, CREATE TABLE IF NOT EXISTS, etc.
-- =========================================================

PRAGMA foreign_keys = ON;

-- =========================================================
-- COURSE MASTER
-- =========================================================
CREATE TABLE IF NOT EXISTS course (
    course_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code    TEXT UNIQUE NOT NULL,
    course_name    TEXT NOT NULL
);

-- =========================================================
-- UNITS
-- =========================================================
CREATE TABLE IF NOT EXISTS unit (
    unit_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id   INTEGER NOT NULL,
    unit_number INTEGER NOT NULL,
    unit_title  TEXT,
    UNIQUE (course_id, unit_number),
    FOREIGN KEY (course_id) REFERENCES course(course_id) ON DELETE CASCADE
);

-- =========================================================
-- COURSE OUTCOMES (CO)
-- =========================================================
CREATE TABLE IF NOT EXISTS course_outcome (
    co_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id   INTEGER NOT NULL,
    co_code     TEXT NOT NULL,
    description TEXT,
    UNIQUE (course_id, co_code),
    FOREIGN KEY (course_id) REFERENCES course(course_id) ON DELETE CASCADE
);

-- =========================================================
-- QUESTION BANK
-- =========================================================
CREATE TABLE IF NOT EXISTS question (
    question_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_id       INTEGER NOT NULL,
    question_text TEXT NOT NULL,

    -- Embedding for semantic deduplication (stores normalized NumPy bytes)
    embedding     BLOB,

    marks         REAL NOT NULL CHECK (marks IN (0.5, 2, 10, 14)),

    question_type TEXT NOT NULL CHECK (
        question_type IN (
            'MCQ',
            'FILL_BLANK',
            'TRUE_FALSE',
            'SHORT',
            'DESCRIPTIVE',
            'ESSAY',
            'VERY_LONG'
        )
    ),

    co_id         INTEGER,
    bloom_level   TEXT CHECK (
        bloom_level IN (
            'REMEMBER',
            'UNDERSTAND',
            'APPLY',
            'ANALYZE',
            'EVALUATE',
            'CREATE'
        )
    ),

    difficulty     TEXT CHECK (
        difficulty IN (
            'EASY',
            'MEDIUM',
            'HARD'
        )
    ),

    FOREIGN KEY (unit_id) REFERENCES unit(unit_id) ON DELETE CASCADE,
    FOREIGN KEY (co_id)   REFERENCES course_outcome(co_id) ON DELETE SET NULL
);

-- =========================================================
-- GENERATED QUESTION PAPERS
-- =========================================================
CREATE TABLE IF NOT EXISTS question_paper (
    paper_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_date        TEXT NOT NULL,
    total_marks      INTEGER NOT NULL,
    duration_minutes INTEGER NOT NULL,
    paper_hash       TEXT NOT NULL UNIQUE
);

-- =========================================================
-- QUESTIONS USED IN EACH PAPER
-- =========================================================
CREATE TABLE IF NOT EXISTS paper_question (
    pq_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id         INTEGER NOT NULL,
    question_id      INTEGER NOT NULL,
    part             TEXT NOT NULL CHECK (part IN ('A','B','C','D')),
    question_number  INTEGER NOT NULL,
    sub_question     TEXT,
    is_optional      INTEGER DEFAULT 0 CHECK (is_optional IN (0,1)),
    optional_group   INTEGER,

    UNIQUE (paper_id, question_id),
    UNIQUE (paper_id, part, question_number, sub_question),

    FOREIGN KEY (paper_id)    REFERENCES question_paper(paper_id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES question(question_id)  ON DELETE RESTRICT
);

-- =========================================================
-- OPTIONAL: GLOBAL NON-REUSE OF QUESTIONS (ACROSS PAPERS)
-- =========================================================
CREATE TABLE IF NOT EXISTS used_questions (
    question_id INTEGER PRIMARY KEY,
    used_on     TEXT DEFAULT CURRENT_DATE,
    FOREIGN KEY (question_id) REFERENCES question(question_id) ON DELETE CASCADE
);

-- =========================================================
-- PERFORMANCE INDEXES
-- =========================================================
CREATE INDEX IF NOT EXISTS idx_question_unit_marks
ON question (unit_id, marks);

CREATE INDEX IF NOT EXISTS idx_question_bloom
ON question (bloom_level);

CREATE INDEX IF NOT EXISTS idx_paper_question_paper
ON paper_question (paper_id);

CREATE INDEX IF NOT EXISTS idx_paper_question_question
ON paper_question (question_id);

-- =========================================================
-- END OF SCHEMA
-- =========================================================

