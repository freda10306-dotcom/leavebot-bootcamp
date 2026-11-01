"""票 001 API 驗收測試（docs/06-test-plan.md TC-01～TC-11）。

預期值照抄 06；日期參考：2026-10-12 週一，10-17、18 週末，10-19 週一。
"""

import pytest

from .conftest import FIXED_NOW_ISO

URL = "/api/leave-requests"


def list_for(client, employee_id):
    response = client.get(URL, params={"employee_id": employee_id})
    assert response.status_code == 200
    return response.json()


@pytest.mark.req("TC-01", "AC-01.1", "FR-05", "FR-07", "FR-09")
def test_tc01_submit_success_and_listed(client, base_request):
    response = client.post(URL, json=base_request)

    assert response.status_code == 201
    created = response.json()
    assert created["employee_id"] == "E001"
    assert created["leave_type"] == "annual"
    assert created["start_date"] == "2026-10-12"
    assert created["end_date"] == "2026-10-14"
    assert created["period"] == "full"
    assert created["days"] == 3
    assert created["status"] == "pending"
    assert created["reason"] == ""
    assert created["created_at"] == FIXED_NOW_ISO

    listed = list_for(client, "E001")
    assert listed == [created]


@pytest.mark.req("TC-03", "FR-07")
def test_tc03_client_status_and_days_ignored(client, base_request, stored_row):
    body = {**base_request, "status": "approved", "days": 99}

    response = client.post(URL, json=body)

    assert response.status_code == 201
    created = response.json()
    assert created["status"] == "pending"
    assert created["days"] == 3
    row = stored_row(created["id"])
    assert row["status"] == "pending"
    assert row["days"] == 3


def _without(field):
    def change(body):
        del body[field]

    return change


def _set(field, value):
    def change(body):
        body[field] = value

    return change


@pytest.mark.req("TC-04", "AC-02.1", "FR-02", "FR-08")
@pytest.mark.parametrize(
    ("change", "code", "field"),
    [
        pytest.param(_without("employee_id"), "MISSING_FIELD", "employee_id", id="缺員工"),
        pytest.param(_set("employee_id", "E999"), "UNKNOWN_EMPLOYEE", "employee_id", id="員工不存在"),
        pytest.param(_set("leave_type", "vacation"), "INVALID_LEAVE_TYPE", "leave_type", id="假別不合法"),
        pytest.param(_set("period", "night"), "INVALID_PERIOD", "period", id="時段不合法"),
        pytest.param(_set("start_date", "2026-02-30"), "INVALID_DATE", "start_date", id="不存在的日期"),
        pytest.param(_set("employee_id", ["E001"]), "UNKNOWN_EMPLOYEE", "employee_id", id="員工為陣列"),
        pytest.param(_set("leave_type", {"x": 1}), "INVALID_LEAVE_TYPE", "leave_type", id="假別為物件"),
    ],
)
def test_tc04_required_and_invalid_rejected(client, base_request, leave_count, change, code, field):
    change(base_request)

    response = client.post(URL, json=base_request)

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == code
    assert error["field"] == field
    assert error["message"]
    assert leave_count() == 0


@pytest.mark.req("TC-05", "AC-02.2", "FR-03")
@pytest.mark.parametrize(
    "period",
    [
        pytest.param("full", id="①整天"),
        pytest.param("am", id="②上午-反向日期先於半天規則"),
    ],
)
def test_tc05_end_before_start_rejected(client, base_request, leave_count, period):
    base_request.update(start_date="2026-10-14", end_date="2026-10-12", period=period)

    response = client.post(URL, json=base_request)

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "END_BEFORE_START"
    assert error["field"] == "end_date"
    assert leave_count() == 0


@pytest.mark.req("TC-06", "AC-02.3", "FR-04")
def test_tc06_half_day_multi_day_rejected(client, base_request, leave_count):
    base_request.update(start_date="2026-10-12", end_date="2026-10-13", period="am")

    response = client.post(URL, json=base_request)

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "HALF_DAY_MULTI_DAY"
    assert error["field"] == "period"
    assert leave_count() == 0


@pytest.mark.req("TC-06", "AC-01.2", "FR-04", "FR-05")
def test_tc06_half_day_same_day_accepted(client, base_request):
    base_request.update(start_date="2026-10-12", end_date="2026-10-12", period="pm")

    response = client.post(URL, json=base_request)

    assert response.status_code == 201
    assert response.json()["days"] == 0.5


@pytest.mark.req("TC-07", "AC-02.4", "FR-05")
@pytest.mark.parametrize(
    ("start", "end", "period"),
    [
        pytest.param("2026-10-17", "2026-10-18", "full", id="①週六至週日"),
        pytest.param("2026-10-17", "2026-10-17", "pm", id="②週六下午"),
    ],
)
def test_tc07_no_working_days_rejected(client, base_request, leave_count, start, end, period):
    base_request.update(start_date=start, end_date=end, period=period)

    response = client.post(URL, json=base_request)

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "NO_WORKING_DAYS"
    assert error["field"] == "start_date"
    assert leave_count() == 0


# TC-08 依 06 v0.2（D-07，卡 J）修訂：上限 200 → 100。
# 原 201 字拒絕案例由檔尾的 test_tc08_reason_101_chars_rejected 取代。


@pytest.mark.req("TC-08", "AC-02.5", "FR-06")
def test_tc08_reason_100_chars_accepted(client, base_request):
    base_request["reason"] = "假" * 100

    response = client.post(URL, json=base_request)

    assert response.status_code == 201
    assert response.json()["reason"] == "假" * 100


@pytest.mark.req("TC-08", "AC-02.5", "FR-06")
def test_tc08_reason_trimmed_before_counting(client, base_request, stored_row):
    base_request["reason"] = "   " + "假" * 100 + "   "

    response = client.post(URL, json=base_request)

    assert response.status_code == 201
    created = response.json()
    assert created["reason"] == "假" * 100
    assert stored_row(created["id"])["reason"] == "假" * 100


@pytest.mark.req("TC-09", "AC-03.1", "AC-03.2", "FR-09")
def test_tc09_list_isolated_newest_first_and_empty(client, base_request):
    a = client.post(URL, json=base_request).json()
    b_request = {**base_request, "start_date": "2026-10-19", "end_date": "2026-10-19"}
    b = client.post(URL, json=b_request).json()
    e2 = client.post(URL, json={**base_request, "employee_id": "E002"}).json()

    e001 = list_for(client, "E001")
    assert [row["id"] for row in e001] == [b["id"], a["id"]]
    assert {row["employee_id"] for row in e001} == {"E001"}

    e002 = list_for(client, "E002")
    assert [row["id"] for row in e002] == [e2["id"]]
    assert e002[0]["employee_id"] == "E002"

    assert list_for(client, "E003") == []


@pytest.mark.req("TC-10", "AC-01.3", "FR-10")
def test_tc10_duplicate_submissions_both_saved(client, base_request):
    first = client.post(URL, json=base_request)
    second = client.post(URL, json=base_request)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] != second.json()["id"]
    assert len(list_for(client, "E001")) == 2


DANGEROUS_REASON = "<script>alert(1)</script>'); DROP TABLE x;--"


@pytest.mark.req("TC-11", "NFR-01", "NFR-02")
def test_tc11_dangerous_text_kept_and_survives_restart(make_client, base_request):
    first_app = make_client()
    response = first_app.post(URL, json={**base_request, "reason": DANGEROUS_REASON})
    assert response.status_code == 201

    restarted = make_client()
    listed = list_for(restarted, "E001")

    assert len(listed) == 1
    assert listed[0]["reason"] == DANGEROUS_REASON


@pytest.mark.req("TC-08", "AC-02.5", "FR-06", "FR-08")
def test_tc08_reason_101_chars_rejected(client, base_request, leave_count):
    """D-07（卡 J）：上限 100 字；101 字是剛好超過上限的邊界。"""
    base_request["reason"] = "假" * 101

    response = client.post(URL, json=base_request)

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "REASON_TOO_LONG"
    assert error["field"] == "reason"
    assert error["message"] == "理由最多 100 字"
    assert leave_count() == 0
