"""FastAPI 應用程式進入點（docs/05-sds.md：app.main.create_app）。"""

import logging
import os
import sqlite3
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app import db
from app.rules import LeaveError, validate_leave

STATIC_DIR = Path(__file__).parent / "static"
DEFAULT_DB = Path(__file__).resolve().parents[1] / "data" / "leavebot.db"

logger = logging.getLogger("leavebot")


def error_response(status: int, code: str, field: str | None, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "field": field, "message": message}},
    )


def db_error() -> JSONResponse:
    return error_response(500, "DB_ERROR", None, "系統暫時無法存檔，請稍後再試")


def create_app(
    db_path: str | Path | None = None,
    now: Callable[[], datetime] | None = None,
) -> FastAPI:
    """建立 app。db_path 未給時讀 LEAVEBOT_DB，再沒有則用 backend/data/leavebot.db。"""
    resolved_db = Path(db_path or os.environ.get("LEAVEBOT_DB") or DEFAULT_DB)
    clock = now or (lambda: datetime.now(timezone.utc))
    db.init_db(resolved_db)

    app = FastAPI(title="LeaveBot")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/employees")
    def list_employees():
        conn = None
        try:
            conn = db.connect(resolved_db)
            return db.list_employees(conn)
        except sqlite3.Error:
            logger.exception("list employees failed")
            return db_error()
        finally:
            if conn is not None:
                conn.close()

    @app.post("/api/leave-requests", status_code=201)
    async def submit_leave(request: Request):
        try:
            payload = await request.json()
        except ValueError:
            payload = None

        conn = None
        try:
            conn = db.connect(resolved_db)
            result = validate_leave(payload, db.employee_ids(conn))
            if isinstance(result, LeaveError):
                return error_response(422, result.code, result.field, result.message)
            created = db.insert_leave(conn, result, clock().isoformat())
            return JSONResponse(status_code=201, content=created)
        except sqlite3.Error:
            logger.exception("submit leave failed")
            return db_error()
        finally:
            if conn is not None:
                conn.close()

    @app.get("/api/leave-requests")
    def list_leaves(employee_id: str | None = None):
        conn = None
        try:
            if employee_id is None or employee_id.strip() == "":
                return error_response(422, "MISSING_FIELD", "employee_id", "請填寫員工")
            conn = db.connect(resolved_db)
            if employee_id not in db.employee_ids(conn):
                return error_response(422, "UNKNOWN_EMPLOYEE", "employee_id", "找不到這位員工")
            return db.list_leaves(conn, employee_id)
        except sqlite3.Error:
            logger.exception("list leaves failed")
            return db_error()
        finally:
            if conn is not None:
                conn.close()

    # 所有 /api 路由登記完後，最後才掛載靜態頁。
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
    return app


app = create_app()
