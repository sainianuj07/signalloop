"""SQLite data layer for SignalLoop.

Schema mirrors the product pipeline:
  feedback_items (raw)  ->  labels via classify_* columns  ->  themes  ->  opportunities
Items keep a `status` so pipeline runs are resumable after rate-limit stalls.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "signalloop.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS feedback_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,              -- 'play_store' | 'csv'
    external_id TEXT,                  -- review id / ticket id for dedup
    author TEXT,
    body TEXT NOT NULL,
    rating INTEGER,                    -- 1-5 if the source has one
    created_at TEXT,                   -- when the user wrote it
    ingested_at TEXT DEFAULT (datetime('now')),

    -- AI labels (filled by the classify stage)
    status TEXT DEFAULT 'new',         -- new | classified | reviewed | failed
    fb_type TEXT,                      -- bug | feature_request | ux_friction | pricing | praise | churn_risk | other
    product_area TEXT,
    sentiment TEXT,                    -- positive | neutral | negative
    severity INTEGER,                  -- 1 (minor) .. 4 (blocker)
    confidence REAL,                   -- model self-reported 0-1
    human_corrected INTEGER DEFAULT 0, -- 1 if a human edited the labels
    theme_id INTEGER REFERENCES themes(id),

    UNIQUE(source, external_id)
);

CREATE TABLE IF NOT EXISTS themes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    summary TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    theme_id INTEGER REFERENCES themes(id),
    reach INTEGER,                     -- item count backing the theme
    impact REAL,                       -- derived from avg severity
    confidence REAL,                   -- cluster coherence / label confidence
    effort REAL DEFAULT 2.0,           -- person-weeks, human-editable
    rice_score REAL,
    draft_prd TEXT,                    -- generated PRD markdown, if any
    updated_at TEXT DEFAULT (datetime('now'))
);
"""


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def insert_items(conn: sqlite3.Connection, items: list[dict]) -> int:
    """Insert feedback items, silently skipping duplicates (same source+external_id)."""
    inserted = 0
    for it in items:
        cur = conn.execute(
            """INSERT OR IGNORE INTO feedback_items
               (source, external_id, author, body, rating, created_at)
               VALUES (:source, :external_id, :author, :body, :rating, :created_at)""",
            it,
        )
        inserted += cur.rowcount
    conn.commit()
    return inserted


def get_unclassified_batch(conn: sqlite3.Connection, limit: int = 15) -> list[sqlite3.Row]:
    """Return up to `limit` oldest unclassified items (id + body only).

    Read-only by design: a crashed pipeline run can call this again and
    get the same work back — nothing lost, nothing double-marked.
    """
    cur = conn.execute(
        """SELECT id, body FROM feedback_items
           WHERE status = 'new'
           ORDER BY ingested_at ASC, id ASC
           LIMIT ?""",
        (limit,),
    )
    return cur.fetchall()

def save_label(conn: sqlite3.Connection, item_id: int, label: dict) -> None:
    """Write one item's AI labels and mark it 'classified'.

    Called only after classify_one succeeds — so 'classified' always
    means 'we really have a label for this'."""
    conn.execute(
        """UPDATE feedback_items
           SET fb_type = ?, product_area = ?, sentiment = ?,
               severity = ?, confidence = ?, status = 'classified'
           WHERE id = ?""",
        (label["type"], label["area"], label["sentiment"],
         label["severity"], label["confidence"], item_id),
    )
    conn.commit()


def mark_failed(conn: sqlite3.Connection, item_id: int) -> None:
    """Mark an item 'failed' so it's skipped now but recoverable later."""
    conn.execute(
        "UPDATE feedback_items SET status = 'failed' WHERE id = ?",
        (item_id,),
    )
    conn.commit()

def clear_themes(conn: sqlite3.Connection) -> None:
    """Wipe themes and unlink items, so clustering can be re-run cleanly."""
    conn.execute("DELETE FROM themes")
    conn.execute("UPDATE feedback_items SET theme_id = NULL")
    conn.commit()


def save_theme(conn: sqlite3.Connection, name: str, summary: str) -> int:
    """Insert a theme and return its new id."""
    cur = conn.execute(
        "INSERT INTO themes (name, summary) VALUES (?, ?)", (name, summary)
    )
    conn.commit()
    return cur.lastrowid


def assign_theme(conn: sqlite3.Connection, item_ids: list[int], theme_id: int) -> None:
    """Link a batch of items to a theme."""
    conn.executemany(
        "UPDATE feedback_items SET theme_id = ? WHERE id = ?",
        [(theme_id, i) for i in item_ids],
    )
    conn.commit()