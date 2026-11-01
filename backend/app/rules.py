"""請假業務規則（docs/03-srs.md FR-02～FR-06；docs/05-sds.md app.rules）。

純函式：不讀資料庫、不讀時鐘。
"""

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class LeaveError:
    code: str
    field: str | None
    message: str


LEAVE_TYPES = {"annual", "personal", "sick"}
PERIODS = {"full", "am", "pm"}
REASON_MAX_CHARS = 100  # D-07（卡 J）：由 200 改為 100

FIELD_LABELS = {
    "employee_id": "員工",
    "leave_type": "假別",
    "start_date": "開始日期",
    "end_date": "結束日期",
    "period": "時段",
}


def _is_blank(value: object) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _parse_date(value: object) -> date | None:
    if not isinstance(value, str) or len(value) != 10:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def validate_leave(payload: object, employee_ids: set[str]) -> dict | LeaveError:
    """依 SRS 驗證順序 FR-02→06→03→04→05 檢查，回傳清理後的欄位與天數，或第一個錯誤。"""
    if not isinstance(payload, dict):
        return LeaveError("INVALID_BODY", None, "請求格式錯誤")

    # FR-02：依欄位順序，先檢查缺漏，再檢查合法值。
    for field in ("employee_id", "leave_type", "start_date", "end_date", "period"):
        value = payload.get(field)
        if _is_blank(value):
            return LeaveError("MISSING_FIELD", field, f"請填寫{FIELD_LABELS[field]}")
        # 非字串的非空值（數字、陣列、物件）視為不合法值（SDS API-03 第 2 步）。
        # 先檢查型別，避免陣列／物件做集合查詢時拋出 TypeError（卡 I）。
        is_text = isinstance(value, str)
        if field == "employee_id" and (not is_text or value not in employee_ids):
            return LeaveError("UNKNOWN_EMPLOYEE", field, "找不到這位員工")
        if field == "leave_type" and (not is_text or value not in LEAVE_TYPES):
            return LeaveError("INVALID_LEAVE_TYPE", field, "假別不正確")
        if field in ("start_date", "end_date") and _parse_date(value) is None:
            return LeaveError("INVALID_DATE", field, "日期格式不正確")
        if field == "period" and (not is_text or value not in PERIODS):
            return LeaveError("INVALID_PERIOD", field, "時段不正確")

    start = _parse_date(payload["start_date"])
    end = _parse_date(payload["end_date"])
    period = payload["period"]
    # FR-06：選填；先去除前後空白，再以字元（code point）計數（D-01、D-05）。
    raw_reason = payload.get("reason")
    if raw_reason is None:
        reason = ""
    elif isinstance(raw_reason, str):
        reason = raw_reason.strip()
    else:
        return LeaveError("INVALID_REASON", "reason", "理由格式不正確")
    if len(reason) > REASON_MAX_CHARS:
        return LeaveError("REASON_TOO_LONG", "reason", f"理由最多 {REASON_MAX_CHARS} 字")

    # FR-03
    if end < start:
        return LeaveError("END_BEFORE_START", "end_date", "結束日期不能早於開始日期")

    # FR-04
    if period in ("am", "pm") and start != end:
        return LeaveError("HALF_DAY_MULTI_DAY", "period", "半天假只能是同一天")

    # FR-05
    days = count_days(start, end, period)
    if days == 0:
        return LeaveError("NO_WORKING_DAYS", "start_date", "區間內沒有工作日")

    return {
        "employee_id": payload["employee_id"],
        "leave_type": payload["leave_type"],
        "start_date": payload["start_date"],
        "end_date": payload["end_date"],
        "period": period,
        "reason": reason,
        "days": days,
    }


def count_days(start: date, end: date, period: str) -> float:
    """含首尾計算週一至週五的工作日；整天每日 1 天，上午／下午 0.5 天（FR-05）。"""
    workdays = 0
    current = start
    while current <= end:
        if current.weekday() < 5:
            workdays += 1
        current += timedelta(days=1)
    return workdays * (1.0 if period == "full" else 0.5)
