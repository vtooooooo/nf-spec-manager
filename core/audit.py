# core/audit.py
import sqlite3, os
from datetime import datetime

DB_PATH = os.path.join("db", "audit.db")

def init_db():
    os.makedirs("db", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            username  TEXT NOT NULL,
            role      TEXT NOT NULL,
            action    TEXT NOT NULL,
            spec_name TEXT,
            from_env  TEXT,
            to_env    TEXT,
            status    TEXT NOT NULL,
            message   TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_action(user, action, spec_name=None, from_env=None,
               to_env=None, status="SUCCESS", message=""):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO audit_log
            (timestamp, username, role, action, spec_name, from_env, to_env, status, message)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (datetime.utcnow().isoformat(), user["username"], user["role"],
          action, spec_name, from_env, to_env, status, message))
    conn.commit()
    conn.close()

def get_logs(limit=100):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("""
        SELECT timestamp, username, role, action, spec_name,
               from_env, to_env, status, message
        FROM audit_log ORDER BY id DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    cols = ["timestamp","username","role","action","spec_name",
            "from_env","to_env","status","message"]
    return [dict(zip(cols, row)) for row in rows]