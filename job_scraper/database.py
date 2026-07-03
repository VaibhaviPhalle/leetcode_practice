"""
SQLite database layer. All dashboard reads come from here — no live API calls on refresh.
"""

import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent / "jobs.db"

_local = threading.local()


def _conn() -> sqlite3.Connection:
    if not hasattr(_local, "conn"):
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        _local.conn = conn
    return _local.conn


def init_db() -> None:
    conn = _conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id       TEXT PRIMARY KEY,
            company_name TEXT NOT NULL,
            company_tier TEXT NOT NULL,
            title        TEXT NOT NULL,
            location     TEXT,
            job_url      TEXT,
            posted_at    TEXT,
            source       TEXT,
            first_seen   TEXT NOT NULL,
            last_seen    TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_first_seen   ON jobs (first_seen DESC);
        CREATE INDEX IF NOT EXISTS idx_company_tier ON jobs (company_tier);
        CREATE INDEX IF NOT EXISTS idx_posted_at    ON jobs (posted_at DESC);

        CREATE TABLE IF NOT EXISTS scrape_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            scraped_at  TEXT NOT NULL,
            total_seen  INTEGER,
            new_jobs    INTEGER,
            errors      INTEGER
        );
    """)
    conn.commit()


def upsert_job(job: dict) -> bool:
    """Insert or update a job. Returns True if this is a brand-new job."""
    now = datetime.now(timezone.utc).isoformat()
    conn = _conn()

    existing = conn.execute(
        "SELECT job_id FROM jobs WHERE job_id = ?", (job["job_id"],)
    ).fetchone()

    posted_at = job.get("posted_at")
    if isinstance(posted_at, datetime):
        posted_at = posted_at.isoformat()

    if existing:
        conn.execute(
            "UPDATE jobs SET last_seen = ?, location = ?, job_url = ? WHERE job_id = ?",
            (now, job.get("location", ""), job.get("job_url", ""), job["job_id"]),
        )
        conn.commit()
        return False
    else:
        conn.execute(
            """INSERT INTO jobs
               (job_id, company_name, company_tier, title, location,
                job_url, posted_at, source, first_seen, last_seen)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                job["job_id"],
                job["company_name"],
                job["company_tier"],
                job["title"],
                job.get("location", ""),
                job.get("job_url", ""),
                posted_at,
                job.get("source", ""),
                now,
                now,
            ),
        )
        conn.commit()
        return True


def log_scrape(summary: dict) -> None:
    conn = _conn()
    conn.execute(
        "INSERT INTO scrape_log (scraped_at, total_seen, new_jobs, errors) VALUES (?, ?, ?, ?)",
        (
            summary.get("scraped_at", datetime.now(timezone.utc).isoformat()),
            summary.get("total_seen", 0),
            summary.get("new_jobs", 0),
            summary.get("errors", 0),
        ),
    )
    conn.commit()


def get_jobs(
    tier: Optional[str] = None,
    location_filter: Optional[str] = None,
    days: int = 30,
    limit: int = 500,
    offset: int = 0,
) -> list[dict]:
    conn = _conn()
    query = """
        SELECT
            job_id, company_name, company_tier, title,
            location, job_url, posted_at, source, first_seen
        FROM jobs
        WHERE first_seen >= datetime('now', ?)
    """
    params: list = [f"-{days} days"]

    if tier and tier != "All":
        query += " AND company_tier = ?"
        params.append(tier)

    if location_filter == "Bay Area":
        bay_terms = [
            "san francisco", "sf", "san jose", "mountain view", "sunnyvale",
            "cupertino", "santa clara", "palo alto", "menlo park", "redwood city",
            "san mateo", "foster city", "south san francisco", "fremont",
            "oakland", "berkeley", "bay area",
        ]
        conditions = " OR ".join(["LOWER(location) LIKE ?" for _ in bay_terms])
        query += f" AND ({conditions})"
        params.extend([f"%{t}%" for t in bay_terms])
    elif location_filter == "Remote":
        query += " AND LOWER(location) LIKE '%remote%'"

    query += " ORDER BY COALESCE(posted_at, first_seen) DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def get_stats() -> dict:
    conn = _conn()
    total = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    today = conn.execute(
        "SELECT COUNT(*) FROM jobs WHERE first_seen >= datetime('now', '-1 day')"
    ).fetchone()[0]
    last_scrape = conn.execute(
        "SELECT scraped_at, new_jobs, errors FROM scrape_log ORDER BY id DESC LIMIT 1"
    ).fetchone()

    return {
        "total_jobs": total,
        "new_today": today,
        "last_scrape": dict(last_scrape) if last_scrape else None,
    }


def get_tiers() -> list[str]:
    conn = _conn()
    rows = conn.execute(
        "SELECT DISTINCT company_tier FROM jobs ORDER BY company_tier"
    ).fetchall()
    return [r[0] for r in rows]
