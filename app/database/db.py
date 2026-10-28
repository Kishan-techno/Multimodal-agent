"""
SQLite Database interface for Multimodal Attendance & Engagement Agent.
Manages persistent records for students, lecture sessions, attendance logs,
multimodal engagement time-series, and AI teaching suggestions.
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import config

DB_FILE = config.DATABASE_PATH

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes database schema with required tables and indexes."""
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        email TEXT,
        department TEXT DEFAULT 'Computer Science',
        roll_no TEXT,
        image_path TEXT,
        embedding_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_name TEXT NOT NULL,
        instructor_name TEXT DEFAULT 'Prof. Instructor',
        subject TEXT DEFAULT 'AI & Machine Learning',
        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_time TIMESTAMP,
        is_active INTEGER DEFAULT 1,
        total_enrolled INTEGER DEFAULT 0,
        total_present INTEGER DEFAULT 0,
        avg_engagement REAL DEFAULT 0.0
    );

    CREATE TABLE IF NOT EXISTS attendance_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        student_id TEXT NOT NULL,
        first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        sustained_duration_seconds REAL DEFAULT 0.0,
        status TEXT DEFAULT 'ABSENT', -- 'PRESENT', 'PARTIAL', 'ABSENT'
        verification_confidence REAL DEFAULT 0.0,
        FOREIGN KEY (session_id) REFERENCES sessions(id),
        FOREIGN KEY (student_id) REFERENCES students(student_id),
        UNIQUE(session_id, student_id)
    );

    CREATE TABLE IF NOT EXISTS engagement_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        overall_score REAL NOT NULL,
        visual_attention REAL NOT NULL,
        facial_valence REAL NOT NULL,
        audio_activity REAL NOT NULL,
        body_motion REAL NOT NULL,
        state_label TEXT NOT NULL,
        active_faces_count INTEGER DEFAULT 0,
        FOREIGN KEY (session_id) REFERENCES sessions(id)
    );

    CREATE TABLE IF NOT EXISTS teaching_suggestions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        suggestion_type TEXT NOT NULL, -- 'PACING', 'INTERACTION', 'BREAK', 'REINFORCEMENT'
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        priority TEXT DEFAULT 'MEDIUM', -- 'LOW', 'MEDIUM', 'HIGH'
        is_dismissed INTEGER DEFAULT 0,
        FOREIGN KEY (session_id) REFERENCES sessions(id)
    );

    CREATE INDEX IF NOT EXISTS idx_metrics_session ON engagement_metrics(session_id, timestamp);
    CREATE INDEX IF NOT EXISTS idx_attendance_session ON attendance_logs(session_id);
    """)

    conn.commit()
    conn.close()

# --- Student Queries ---

def add_student(student_id: str, name: str, email: str, department: str, roll_no: str, image_path: str = "", embedding: Optional[List[float]] = None) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    emb_json = json.dumps(embedding) if embedding else None
    cursor.execute("""
        INSERT INTO students (student_id, name, email, department, roll_no, image_path, embedding_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(student_id) DO UPDATE SET
            name=excluded.name,
            email=excluded.email,
            department=excluded.department,
            roll_no=excluded.roll_no,
            image_path=coalesce(nullif(excluded.image_path, ''), students.image_path),
            embedding_json=coalesce(excluded.embedding_json, students.embedding_json)
    """, (student_id, name, email, department, roll_no, image_path, emb_json))
    student_pk = cursor.lastrowid
    conn.commit()
    conn.close()
    return student_pk

def get_all_students() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students ORDER BY name ASC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_student(student_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

# --- Session Queries ---

def create_session(session_name: str, instructor_name: str = "Dr. Sarah Adams", subject: str = "Applied AI Systems") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    # Close any other active sessions
    cursor.execute("UPDATE sessions SET is_active = 0, end_time = CURRENT_TIMESTAMP WHERE is_active = 1")
    
    # Get total enrolled students count
    cursor.execute("SELECT COUNT(*) FROM students")
    enrolled_count = cursor.fetchone()[0]

    cursor.execute("""
        INSERT INTO sessions (session_name, instructor_name, subject, start_time, is_active, total_enrolled)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP, 1, ?)
    """, (session_name, instructor_name, subject, enrolled_count))
    session_id = cursor.lastrowid

    # Initialize attendance logs for all enrolled students as ABSENT
    cursor.execute("SELECT student_id FROM students")
    students = cursor.fetchall()
    for s in students:
        cursor.execute("""
            INSERT OR IGNORE INTO attendance_logs (session_id, student_id, status, sustained_duration_seconds)
            VALUES (?, ?, 'ABSENT', 0.0)
        """, (session_id, s['student_id']))

    conn.commit()
    conn.close()
    return session_id

def get_active_session() -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE is_active = 1 ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_session(session_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def end_session(session_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Calculate total present and avg engagement
    cursor.execute("SELECT COUNT(*) FROM attendance_logs WHERE session_id = ? AND status = 'PRESENT'", (session_id,))
    total_present = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(overall_score) FROM engagement_metrics WHERE session_id = ?", (session_id,))
    avg_eng = cursor.fetchone()[0] or 0.0

    cursor.execute("""
        UPDATE sessions
        SET is_active = 0,
            end_time = CURRENT_TIMESTAMP,
            total_present = ?,
            avg_engagement = ?
        WHERE id = ?
    """, (total_present, round(avg_eng, 2), session_id))
    conn.commit()
    conn.close()

# --- Attendance Queries ---

def update_attendance_presence(session_id: int, student_id: str, duration_increment: float, confidence: float):
    """
    Increments sustained presence duration for a student and updates status
    according to sustained presence thresholds.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT sustained_duration_seconds FROM attendance_logs
        WHERE session_id = ? AND student_id = ?
    """, (session_id, student_id))
    row = cursor.fetchone()

    sustained_seconds = config.ATTENDANCE_CONFIG["SUSTAINED_PRESENCE_SECONDS"]
    partial_seconds = config.ATTENDANCE_CONFIG["PARTIAL_PRESENCE_SECONDS"]

    if row:
        new_duration = row[0] + duration_increment
        status = 'PRESENT' if new_duration >= sustained_seconds else ('PARTIAL' if new_duration >= partial_seconds else 'ABSENT')
        cursor.execute("""
            UPDATE attendance_logs
            SET sustained_duration_seconds = ?,
                last_seen = CURRENT_TIMESTAMP,
                status = ?,
                verification_confidence = MAX(verification_confidence, ?)
            WHERE session_id = ? AND student_id = ?
        """, (round(new_duration, 2), status, confidence, session_id, student_id))
    else:
        status = 'PRESENT' if duration_increment >= sustained_seconds else ('PARTIAL' if duration_increment >= partial_seconds else 'ABSENT')
        cursor.execute("""
            INSERT INTO attendance_logs (session_id, student_id, first_seen, last_seen, sustained_duration_seconds, status, verification_confidence)
            VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?, ?, ?)
        """, (session_id, student_id, round(duration_increment, 2), status, confidence))

    conn.commit()
    conn.close()

def get_session_attendance(session_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.*, s.name, s.roll_no, s.department, s.email
        FROM attendance_logs a
        JOIN students s ON a.student_id = s.student_id
        WHERE a.session_id = ?
        ORDER BY 
            CASE a.status 
                WHEN 'PRESENT' THEN 1 
                WHEN 'PARTIAL' THEN 2 
                ELSE 3 
            END, s.name ASC
    """, (session_id,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

# --- Metrics Queries ---

def log_engagement_metric(session_id: int, overall: float, visual: float, facial: float, audio: float, motion: float, state: str, active_faces: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO engagement_metrics (session_id, overall_score, visual_attention, facial_valence, audio_activity, body_motion, state_label, active_faces_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (session_id, round(overall, 2), round(visual, 2), round(facial, 2), round(audio, 2), round(motion, 2), state, active_faces))
    conn.commit()
    conn.close()

def get_session_metrics(session_id: int, limit: int = 120) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM engagement_metrics
        WHERE session_id = ?
        ORDER BY timestamp ASC
    """, (session_id,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows[-limit:] if limit else rows

# --- AI Teaching Suggestions Queries ---

def add_teaching_suggestion(session_id: int, stype: str, title: str, description: str, priority: str = "MEDIUM") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO teaching_suggestions (session_id, suggestion_type, title, description, priority)
        VALUES (?, ?, ?, ?, ?)
    """, (session_id, stype, title, description, priority))
    suggestion_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return suggestion_id

def get_session_suggestions(session_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM teaching_suggestions
        WHERE session_id = ?
        ORDER BY id DESC
    """, (session_id,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def dismiss_suggestion(suggestion_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE teaching_suggestions SET is_dismissed = 1 WHERE id = ?", (suggestion_id,))
    conn.commit()
    conn.close()
