"""feedback/collector.py — SQLite feedback storage and analytics."""
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from config import FEEDBACK_DB


def _get_connection() -> sqlite3.Connection:
    Path(FEEDBACK_DB).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(FEEDBACK_DB))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create feedback table if it doesn't exist."""
    with _get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                response TEXT NOT NULL,
                query_type TEXT,
                confidence REAL,
                rating TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def save_feedback(
    query: str,
    response: str,
    query_type: str,
    confidence: float,
    rating: str,  # 'helpful' or 'not_helpful'
):
    """Save a single feedback entry."""
    init_db()
    with _get_connection() as conn:
        conn.execute(
            """INSERT INTO feedback (query, response, query_type, confidence, rating, timestamp)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (query, response, query_type, confidence, rating, datetime.now().isoformat()),
        )
        conn.commit()


def get_stats() -> Dict[str, Any]:
    """Return overall feedback statistics."""
    init_db()
    with _get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
        helpful = conn.execute("SELECT COUNT(*) FROM feedback WHERE rating='helpful'").fetchone()[0]
        not_helpful = conn.execute("SELECT COUNT(*) FROM feedback WHERE rating='not_helpful'").fetchone()[0]
        avg_conf = conn.execute("SELECT AVG(confidence) FROM feedback").fetchone()[0]

    satisfaction = round((helpful / total * 100), 1) if total > 0 else 0.0
    return {
        "total": total,
        "helpful": helpful,
        "not_helpful": not_helpful,
        "satisfaction_rate": satisfaction,
        "avg_confidence": round(avg_conf or 0.0, 3),
    }


def get_by_type() -> List[Dict]:
    """Return feedback count grouped by query type."""
    init_db()
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT query_type, COUNT(*) as count FROM feedback GROUP BY query_type ORDER BY count DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def get_recent(n: int = 20) -> List[Dict]:
    """Return the most recent N feedback entries."""
    init_db()
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM feedback ORDER BY timestamp DESC LIMIT ?", (n,)
        ).fetchall()
    return [dict(row) for row in rows]


def get_satisfaction_over_time() -> List[Dict]:
    """Return daily satisfaction rates for charting."""
    init_db()
    with _get_connection() as conn:
        rows = conn.execute("""
            SELECT
                DATE(timestamp) as date,
                COUNT(*) as total,
                SUM(CASE WHEN rating='helpful' THEN 1 ELSE 0 END) as helpful
            FROM feedback
            GROUP BY DATE(timestamp)
            ORDER BY date ASC
        """).fetchall()
    result = []
    for row in rows:
        r = dict(row)
        r["satisfaction"] = round(r["helpful"] / r["total"] * 100, 1) if r["total"] > 0 else 0.0
        result.append(r)
    return result


def get_confidence_distribution() -> List[Dict]:
    """Return confidence score buckets for histogram."""
    init_db()
    with _get_connection() as conn:
        rows = conn.execute("SELECT confidence FROM feedback WHERE confidence IS NOT NULL").fetchall()
    scores = [r[0] for r in rows]
    buckets = {"high (>0.7)": 0, "medium (0.5-0.7)": 0, "low (0.35-0.5)": 0, "insufficient (<0.35)": 0}
    for s in scores:
        if s >= 0.7:
            buckets["high (>0.7)"] += 1
        elif s >= 0.5:
            buckets["medium (0.5-0.7)"] += 1
        elif s >= 0.35:
            buckets["low (0.35-0.5)"] += 1
        else:
            buckets["insufficient (<0.35)"] += 1
    return [{"bucket": k, "count": v} for k, v in buckets.items()]


def export_to_csv() -> str:
    """Export all feedback to CSV string."""
    import csv, io
    rows = get_recent(10000)
    if not rows:
        return ""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()
