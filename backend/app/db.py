"""SQLite 資料存取（docs/05-sds.md 資料模型、app.db）。

所有 SQL 使用 ? 參數（NFR-01）。
"""

import sqlite3
from pathlib import Path

EMPLOYEES = [
    ("E001", "王小明"),
    ("E002", "李小華"),
    ("E003", "陳大同"),
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS employees (
    id   TEXT PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS leave_requests (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id TEXT NOT NULL REFERENCES employees(id),
    leave_type  TEXT NOT NULL CHECK (leave_type IN ('annual', 'personal', 'sick')),
    start_date  TEXT NOT NULL,
    end_date    TEXT NOT NULL,
    period      TEXT NOT NULL CHECK (period IN ('full', 'am', 'pm')),
    days        REAL NOT NULL CHECK (days > 0),
    reason      TEXT NOT NULL DEFAULT '',
    status      TEXT NOT NULL DEFAULT 'pending' CHECK (status = 'pending'),
    created_at  TEXT NOT NULL,
    CHECK (end_date >= start_date)
);
"""

LEAVE_COLUMNS = (
    "id, employee_id, leave_type, start_date, end_date, period, "
    "days, reason, status, created_at"
)


def connect(path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(path: str | Path) -> None:
    """冪等：建表並寫入員工；重複呼叫不重複寫入、不刪資料。"""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = connect(path)
    try:
        with conn:
            conn.executescript(SCHEMA)
            conn.executemany(
                "INSERT OR IGNORE INTO employees (id, name) VALUES (?, ?)", EMPLOYEES
            )
    finally:
        conn.close()


def list_employees(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT id, name FROM employees ORDER BY id").fetchall()
    return [dict(row) for row in rows]


def employee_ids(conn: sqlite3.Connection) -> set[str]:
    return {row["id"] for row in conn.execute("SELECT id FROM employees")}


def insert_leave(conn: sqlite3.Connection, data: dict, created_at: str) -> dict:
    """單一交易新增一筆；狀態固定 pending（FR-07）。失敗時回滾並往上拋。"""
    with conn:
        cursor = conn.execute(
            "INSERT INTO leave_requests "
            "(employee_id, leave_type, start_date, end_date, period, days, reason, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)",
            (
                data["employee_id"],
                data["leave_type"],
                data["start_date"],
                data["end_date"],
                data["period"],
                data["days"],
                data["reason"],
                created_at,
            ),
        )
    row = conn.execute(
        f"SELECT {LEAVE_COLUMNS} FROM leave_requests WHERE id = ?", (cursor.lastrowid,)
    ).fetchone()
    return dict(row)


def list_leaves(conn: sqlite3.Connection, employee_id: str) -> list[dict]:
    """只回傳該員工的假單，新到舊（FR-09、ADR-02）。"""
    rows = conn.execute(
        f"SELECT {LEAVE_COLUMNS} FROM leave_requests WHERE employee_id = ? ORDER BY id DESC",
        (employee_id,),
    ).fetchall()
    return [dict(row) for row in rows]
