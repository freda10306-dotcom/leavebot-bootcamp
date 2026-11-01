# 001 表單送出、驗證、存檔與我的假單

- 狀態：完成（2026-11-01），待小組驗收
- 估計：中到大（約 75～90 分鐘）
- 依賴：`issues/000-skeleton.md`（需要 `pyproject.toml`、pytest 設定、`create_app` 與靜態掛載）

## 成果

員工在首頁選自己 → 填假別、日期、時段、理由 → 送出 → 後端依 SRS 驗證 → 合法時存進 SQLite，狀態為 `pending` → 「我的假單」立即顯示「待審核」。拒絕時顯示錯誤、保留表單，資料庫不變。

## 必讀規格

- `docs/03-srs.md`：FR-01～FR-10、驗證順序、天數與日期決策表、理由長度例子、NFR-01～04。
- `docs/05-sds.md`：
  - 資料模型與不變量（`employees` E001～E003、`leave_requests`）。
  - API-02～API-04、錯誤格式與錯誤碼表、驗證順序細節。
  - UI-01。
  - 模組與公開函式（`count_days`、`validate_leave`、`app.db.*`、`create_app`）。
  - 驗證責任與注入。
- `docs/04-sad.md`：信任邊界、ADR-01（手寫驗證，只回第一個錯誤）、ADR-02（依 `id` 由大到小排序）。
- `docs/06-test-plan.md`：TC-01～TC-12 的輸入、預期值與人工步驟。
- `docs/02-prd.md`：AC-01.1～AC-03.2（只用來對照，不重新解讀）。

## TC 與 TDD 順序

每個測試標 `@pytest.mark.req("TC-xx", "<AC/FR 編號>")`。每次先看到「預期原因」的紅燈，再寫最少的程式轉綠。預期值照 06 抄，不呼叫實作函式來算答案。

| 順序 | TC | 層級 | 位置 | 對應 |
|---|---|---|---|---|
| 1 | TC-02 天數計算邊界 | 單元 | `backend/tests/unit/` | AC-01.2、FR-05 |
| 2 | TC-01 成功送出並出現在列表 | API | `backend/tests/acceptance/` | AC-01.1、FR-05/07/09 |
| 3 | TC-03 不採用客戶端的狀態與天數 | API | acceptance | FR-07 |
| 4 | TC-04 必填與非法值 | API | acceptance | AC-02.1、FR-02/08 |
| 5 | TC-05 反向日期與驗證順序 | API | acceptance | AC-02.2、FR-03 |
| 6 | TC-06 半天限同一天 | API | acceptance | AC-02.3、AC-01.2、FR-04 |
| 7 | TC-07 沒有工作日 | API | acceptance | AC-02.4、FR-05 |
| 8 | TC-08 理由長度邊界 | API | acceptance | AC-02.5、FR-06 |
| 9 | TC-09 員工隔離、排序、空清單 | API | acceptance | AC-03.1、AC-03.2、FR-09 |
| 10 | TC-10 重複送出不去重 | API | acceptance | AC-01.3、FR-10 |
| 11 | TC-11 危險文字原樣保存、重啟後仍在 | API | acceptance | NFR-01、NFR-02 |
| 12 | TC-12 畫面流程 | 人工 | 06「人工驗收」步驟 | AC-01.1、AC-01.3、D-04、NFR-01/04 |

第一個業務測試（TC-02）跑出紅燈後**先停下**，讓人確認紅燈原因，再做綠燈。

## 實作邊界

- **測試隔離**：一律用 `create_app(db_path=tmp_path / "test.db", now=lambda: datetime(2026, 10, 12, 1, 0, tzinfo=timezone.utc))`，不讀寫 `backend/data/leavebot.db`。
- **SQL**：一律用 `?` 參數；`PRAGMA foreign_keys = ON`；每個請求開連線，在 `finally` 關閉。
- **前端**：
  - 只呼叫相對路徑 `/api/...`。
  - 使用者文字一律用 `textContent`。
  - 不加 `required` 或長度限制。
  - 送出期間停用按鈕，結束後恢復。
- **不做**：登入、主管核准、額度、同組提醒、國定假日、LLM、後端去重、`LEAVEBOT_TODAY`（D-02 使主線不需要它）。
- **不在本票測試範圍**（06 已列為缺口）：`DB_ERROR`、`INVALID_BODY`、`INVALID_REASON`、效能。程式仍要依 SDS 實作這些錯誤處理。

## 驗收指令（Windows，repo 根目錄）

```powershell
.venv\Scripts\python.exe -m pytest
$env:LEAVEBOT_DB = "$env:TEMP\leavebot-manual.db"; .venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend
```

第二行啟動後，照 `docs/06-test-plan.md` 的「TC-12 步驟與預期畫面」操作。macOS／Linux 把 `.venv\Scripts\python.exe` 換成 `.venv/bin/python`，環境變數用 `LEAVEBOT_DB=/tmp/leavebot-manual.db`。

## 完成條件

- [x] TC-01～TC-11 的自動化測試都存在、有 `req` marker，斷言與 06 的預期一致。
- [x] 完整 `pytest` 實際執行全部通過，輸出貼在回報中。
- [x] TC-12 人工操作完成（瀏覽器工具或由人操作），結果記錄在案。
- [x] `docs/06-test-plan.md` 追溯表回填實際指令、日期、通過或失敗數；沒有執行的維持「未執行」。
- [x] 實際偏差記入 `docs/LESSONS.md`。
- [x] 不刪除、跳過或放寬測試；規格有錯時先提出證據，等人確認。
