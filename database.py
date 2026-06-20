import sqlite3
from datetime import datetime
from config import DATABASE_PATH


def get_conn():
    return sqlite3.connect(DATABASE_PATH)


def init_db():
    with get_conn() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            task_name TEXT,
            deadline TEXT,
            is_done INTEGER DEFAULT 0,
            notified_24h INTEGER DEFAULT 0,
            notified_1h INTEGER DEFAULT 0,
            notified_0h INTEGER DEFAULT 0
        )''')


def add_task(user_id, name, deadline):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO tasks (user_id, task_name, deadline) VALUES (?,?,?)",
                    (user_id, name, deadline.strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        return cur.lastrowid


def get_pending_tasks(user_id):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, task_name, deadline FROM tasks WHERE user_id=? AND is_done=0", (user_id,))
        rows = cur.fetchall()
        return [(r[0], r[1], datetime.strptime(r[2], '%Y-%m-%d %H:%M:%S')) for r in rows]


def mark_done(task_id, user_id):
    with get_conn() as conn:
        conn.execute("UPDATE tasks SET is_done=1 WHERE id=? AND user_id=?", (task_id, user_id))


def delete_task(task_id, user_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM tasks WHERE id=? AND user_id=?", (task_id, user_id))


def get_tasks_to_notify(notif_type):
    col = 'notified_24h' if notif_type == '24h' else 'notified_1h' if notif_type == '1h' else 'notified_0h'
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT id, user_id, task_name, deadline FROM tasks WHERE is_done=0 AND {col}=0")
        rows = cur.fetchall()
        return [(r[0], r[1], r[2], datetime.strptime(r[3], '%Y-%m-%d %H:%M:%S')) for r in rows]


def mark_notified(task_id, notif_type):
    col = 'notified_24h' if notif_type == '24h' else 'notified_1h' if notif_type == '1h' else 'notified_0h'
    with get_conn() as conn:
        conn.execute(f"UPDATE tasks SET {col}=1 WHERE id=?", (task_id,))


# ── Fungsi tambahan untuk dashboard API ─────────────────────────────────────
def get_all_tasks():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, user_id, task_name, deadline, is_done FROM tasks ORDER BY deadline ASC")
        return cur.fetchall()


def mark_done_by_id(task_id):
    with get_conn() as conn:
        conn.execute("UPDATE tasks SET is_done=1 WHERE id=?", (task_id,))


def delete_task_by_id(task_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
