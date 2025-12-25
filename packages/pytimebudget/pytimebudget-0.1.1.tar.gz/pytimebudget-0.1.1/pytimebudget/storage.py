import sqlite3
from .config import DATA_DIR
from .project import project_id

DB_PATH = DATA_DIR / f"{project_id()}.db"

def get_conn():
    DATA_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS timings (
            id INTEGER PRIMARY KEY,
            name TEXT,
            elapsed_ms REAL,
            max_ms REAL,
            timestamp REAL
        )
    """)
    return conn

def store_sample(record):
    conn = get_conn()
    conn.execute(
        "INSERT INTO timings (name, elapsed_ms, max_ms, timestamp) VALUES (?, ?, ?, ?)",
        (
            record["name"],
            record["elapsed_ms"],
            record["max_ms"],
            record["timestamp"],
        )
    )
    conn.commit()
    conn.close()

def fetch_samples(name, limit=50):
    conn = get_conn()
    cur = conn.execute(
        "SELECT elapsed_ms FROM timings WHERE name=? ORDER BY id DESC LIMIT ?",
        (name, limit),
    )
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows][::-1]
