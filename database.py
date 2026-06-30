import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "assistant.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                details TEXT,
                amount REAL,
                currency TEXT DEFAULT 'EGP',
                remind_at TEXT,
                reminded INTEGER DEFAULT 0,
                raw_message TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                done INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER REFERENCES items(id),
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'EGP',
                expense_category TEXT,
                date TEXT DEFAULT (date('now'))
            );
        """)


# ---------- CRUD ----------

def insert_item(category, title, details=None, amount=None, currency="EGP",
                remind_at=None, raw_message=None, expense_category=None):
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO items (category, title, details, amount, currency,
               remind_at, raw_message)
               VALUES (?,?,?,?,?,?,?)""",
            (category, title, details, amount, currency, remind_at, raw_message)
        )
        item_id = cur.lastrowid
        if category == "مصروفات" and amount:
            conn.execute(
                "INSERT INTO expenses (item_id, amount, currency, expense_category) VALUES (?,?,?,?)",
                (item_id, amount, currency, expense_category or title)
            )
        return item_id


def get_items(category=None, done=None):
    query = "SELECT * FROM items"
    params = []
    conditions = []
    if category:
        conditions.append("category = ?")
        params.append(category)
    if done is not None:
        conditions.append("done = ?")
        params.append(1 if done else 0)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY created_at DESC"
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(query, params).fetchall()]


def get_pending_reminders():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM items WHERE remind_at <= ? AND reminded=0 AND done=0",
            (now,)
        ).fetchall()]


def mark_reminded(item_id):
    with get_conn() as conn:
        conn.execute("UPDATE items SET reminded=1 WHERE id=?", (item_id,))


def update_item(item_id, title, details, remind_at, amount, currency, category):
    with get_conn() as conn:
        conn.execute("""UPDATE items SET title=?, details=?, remind_at=?,
                        amount=?, currency=?, category=?, reminded=0
                        WHERE id=?""",
                     (title, details, remind_at, amount, currency, category, item_id))


def mark_done(item_id):
    with get_conn() as conn:
        conn.execute("UPDATE items SET done=1 WHERE id=?", (item_id,))


def delete_item(item_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM expenses WHERE item_id=?", (item_id,))
        conn.execute("DELETE FROM items WHERE id=?", (item_id,))


def get_expense_summary():
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT e.expense_category, SUM(e.amount) as total, e.currency
            FROM expenses e
            JOIN items i ON e.item_id = i.id
            WHERE i.done = 0
            GROUP BY e.expense_category, e.currency
            ORDER BY total DESC
        """).fetchall()
        return [dict(r) for r in rows]


def get_stats():
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        done = conn.execute("SELECT COUNT(*) FROM items WHERE done=1").fetchone()[0]
        by_cat = conn.execute(
            "SELECT category, COUNT(*) as cnt FROM items GROUP BY category"
        ).fetchall()
        return {"total": total, "done": done, "by_category": [dict(r) for r in by_cat]}
