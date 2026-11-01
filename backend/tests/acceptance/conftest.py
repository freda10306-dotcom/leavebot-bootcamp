"""驗收測試共用設定：每個測試一個暫存資料庫與固定時鐘（docs/06-test-plan.md 環境段）。"""

import sqlite3
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

FIXED_NOW = datetime(2026, 10, 12, 1, 0, tzinfo=timezone.utc)
FIXED_NOW_ISO = "2026-10-12T01:00:00+00:00"


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test.db"


@pytest.fixture
def make_client(db_path):
    """以同一個暫存資料庫建立 app；可呼叫多次模擬重啟。"""

    def _make():
        return TestClient(create_app(db_path=db_path, now=lambda: FIXED_NOW))

    return _make


@pytest.fixture
def client(make_client):
    return make_client()


@pytest.fixture
def base_request():
    """06 的「基本請求」。每次回傳新的 dict，測試可自由修改。"""
    return {
        "employee_id": "E001",
        "leave_type": "annual",
        "start_date": "2026-10-12",
        "end_date": "2026-10-14",
        "period": "full",
    }


@pytest.fixture
def leave_count(db_path):
    """直接查暫存資料庫的假單總數，用來核對「資料不變」。"""

    def _count():
        conn = sqlite3.connect(db_path)
        try:
            return conn.execute("SELECT COUNT(*) FROM leave_requests").fetchone()[0]
        finally:
            conn.close()

    return _count


@pytest.fixture
def stored_row(db_path):
    """直接讀資料庫中某筆假單，避免只相信 API 回應。"""

    def _row(leave_id):
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                "SELECT * FROM leave_requests WHERE id = ?", (leave_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    return _row
