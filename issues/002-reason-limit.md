# 002 理由長度上限改為 100 字

- 狀態：完成（2026-11-01），待小組驗收
- 估計：小（約 20～30 分鐘）
- 依賴：`issues/001-submit-leave.md`（已完成）
- 變更來源：卡 J；小組決策 D-07（2026-11-01）

## 成果

理由去除前後空白後最多 100 個字元：
- 101 字被拒絕，回 `422 REASON_TOO_LONG`，訊息為「理由最多 100 字」，資料不變。
- 剛好 100 字可以送出。
- 畫面標籤顯示「最多 100 字」。

計算方式（D-05：先去除前後空白，再以 code point 計數）、錯誤碼、驗證順序都不變。其他行為不變，原本有效的測試都要繼續通過。

## 必讀規格

- `docs/01-brief.md`：決策表 D-01（長度已由 D-07 取代）、D-07。
- `docs/02-prd.md`：AC-02.5 與變更紀錄。
- `docs/03-srs.md` v0.2：FR-06、理由長度例子表。
- `docs/05-sds.md` v0.2：資料表 `leave_requests.reason`、錯誤碼表 `REASON_TOO_LONG`、API-03 驗證步驟 3、UI-01 理由欄位。
- `docs/06-test-plan.md` v0.2：TC-08 修訂後的三個子案例與修訂紀錄。
- `AGENTS.md`：本專案決策段的理由規則。

## 程式位置（目前）

- `backend/app/rules.py:19`：`REASON_MAX_CHARS = 200`
- `backend/app/rules.py:77`：錯誤訊息寫死為 `"理由最多 200 字"`。要改成由常數產生，例如 `f"理由最多 {REASON_MAX_CHARS} 字"`。
- `backend/app/static/index.html:52`：標籤「理由（選填，最多 200 字）」。

不改：`main.py`、`db.py`、`app.js`。前端只顯示後端訊息，而且不加 `maxlength`。

## TDD 順序

測試檔：`backend/tests/acceptance/test_submit_leave.py` 的 TC-08 區塊。

1. **先紅燈**：新增 `test_tc08_reason_101_chars_rejected`，標 `@pytest.mark.req("TC-08", "AC-02.5", "FR-06", "FR-08")`。
   - 輸入：`"假" * 101`。
   - 斷言：`422`、`REASON_TOO_LONG`、`field == "reason"`、`message == "理由最多 100 字"`、筆數 0。
   - 在舊實作下必須跑出預期原因的紅燈，也就是 101 字被接受，出現 `assert 201 == 422`。看到紅燈後先停下，請人確認。
2. **依 06 v0.2 修訂既有的 TC-08 測試**（已經人確認，依據是 D-07）：
   - `test_tc08_reason_200_chars_accepted` 改為 100 字可送出，函式名稱跟著改。
   - `test_tc08_reason_201_chars_rejected` 由第 1 步的 101 字測試取代，刪掉原本這條。
   - `test_tc08_reason_trimmed_before_counting` 改成前後空白加 100 字。
3. **綠燈**：改 `rules.py` 的常數與訊息，以及 `index.html` 的標籤。
4. 跑完整 pytest。

除了上面第 2 步列出的修訂之外，不刪除、跳過或放寬任何測試。

## 驗收指令（Windows，repo 根目錄）

```powershell
.venv\Scripts\python.exe -m pytest backend/tests/acceptance -k tc08
.venv\Scripts\python.exe -m pytest
```

接著到瀏覽器手動確認，伺服器要重啟才會載入新程式：
- 標籤顯示「最多 100 字」。
- 送出 101 字理由時，顯示「理由最多 100 字」，表單保留。
- 送出 100 字理由時成功。

## 完成條件

- [x] 101 字的測試先在舊實作跑出紅燈，並保留紅燈輸出作為證據。
- [x] TC-08 三個子案例依 06 v0.2 修訂，並標上 `req` marker。
- [x] 完整 pytest 實際執行全部通過，輸出貼在回報中。
- [x] 人工確認標籤與錯誤訊息。
- [x] `docs/06-test-plan.md` 回填 TC-08 v0.2 的執行結果，以及 AC-02.5、FR-06 列。
- [x] `docs/LESSONS.md` 記錄這次變更的實際偏差（如果有）。
- [x] 不自動 commit 或 push。
