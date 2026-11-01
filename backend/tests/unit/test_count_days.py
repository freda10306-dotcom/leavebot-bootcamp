"""TC-02 天數計算邊界（docs/06-test-plan.md）。

預期值取自 06 的人工算例表，不由實作函式產生。
日期參考：2026-10-12 週一，10-16 週五，10-17、18 週末，10-19 週一，10-23 週五。
"""

from datetime import date

import pytest

from app.rules import count_days


@pytest.mark.req("TC-02", "AC-01.2", "FR-05")
@pytest.mark.parametrize(
    ("start", "end", "period", "expected"),
    [
        pytest.param(date(2026, 10, 12), date(2026, 10, 12), "full", 1, id="週一單日整天"),
        pytest.param(date(2026, 10, 12), date(2026, 10, 14), "full", 3, id="週一至週三"),
        pytest.param(date(2026, 10, 12), date(2026, 10, 12), "am", 0.5, id="單日上午"),
        pytest.param(date(2026, 10, 16), date(2026, 10, 19), "full", 2, id="跨週末扣週六日"),
        pytest.param(date(2026, 10, 12), date(2026, 10, 23), "full", 10, id="兩週"),
        pytest.param(date(2026, 10, 17), date(2026, 10, 18), "full", 0, id="只有週末"),
    ],
)
def test_count_days(start, end, period, expected):
    assert count_days(start, end, period) == expected
