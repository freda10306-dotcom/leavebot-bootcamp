# DELIVERY — LeaveBot 交付紀錄

- 日期：2026-11-01（D2 卡 K）
- 範圍：本組今天產生的全部檔案（這裡不是 git repo，沒有基準 SHA）：
  - `pyproject.toml`
  - `backend/`
  - `docs/`
  - `issues/`
  - `diagrams/`
  - `AGENTS.md` 本專案決策段
  - `README.md` 末尾的「本組成果」段
- 交付內容：
  - 票 000 骨架。
  - 票 001 表單主線。
  - 票 002 理由上限 100 字（卡 J 需求變更）。
  - 卡 I 修復非字串欄位值回 500 的問題。
- 狀態：已驗證，待小組確認後自行保存版本。agent 沒有 commit 或 push。

## 啟動指令

repo 根目錄，Windows PowerShell：

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -c course/01-上課/05-constraints.txt -e ".[dev]"
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend
```

- 瀏覽器開 `http://127.0.0.1:8000/`。port 被占用時加 `--port 8001`。
- 資料庫預設在 `backend/data/leavebot.db`，可用 `LEAVEBOT_DB` 指定。人工驗收用的是暫存檔：`$env:LEAVEBOT_DB = "$env:TEMP\leavebot-manual.db"`。
- macOS／Linux：把 `.venv\Scripts\python.exe` 換成 `.venv/bin/python`，第一行改成 `python3 -m venv .venv`。

## 實際環境

| 項目 | 版本 |
|---|---|
| 作業系統 | Windows 10 Pro 10.0.19045 |
| Python | 3.12.10（`.venv`） |
| fastapi／starlette | 0.162.0／1.10.0 |
| uvicorn | 0.54.0 |
| httpx | 0.28.1 |
| pytest | 9.1.1 |
| Node（只用於 Archify 畫圖） | v26.13.0 |

套件依 `course/01-上課/05-constraints.txt` 安裝。只在 Windows 上驗證過；macOS／Linux 沒有實測。

## 測試證據

```text
.venv\Scripts\python.exe -m pytest
29 passed, 1 warning in 0.78s
```

- 29 個測試的組成：
  - TC-01、TC-03～TC-11：API 驗收測試 19 個，含卡 I 兩個回歸變體、TC-08 v0.2。
  - TC-02：天數單元測試 6 個。
  - health：2 個。
  - 標了 `req` 的測試共 25 個（API 19 個加單元 6 個）。
- 警告是 `StarletteDeprecationWarning`，與 httpx 有關，不影響結果；STACK 的白名單是 `httpx`，所以不換套件（見 LESSONS）。
- 測試只用暫存資料庫：完整 pytest 之後 `backend/data/` 不存在。
- 各 TC 的紅綠燈與改壞實作檢查：見 `docs/06-test-plan.md` 的「追溯與執行證據」。

## 人工驗收證據（卡 K，2026-11-01）

以 Playwright（MCP）操作 `http://127.0.0.1:8000/`，資料庫為 `%TEMP%\leavebot-manual.db`。

| 流程 | 操作 | 實際結果 |
|---|---|---|
| 成功送出 | E003 送出病假 2026-10-16～10-19 整天，理由「感冒」 | 顯示「已送出，狀態：待審核」；列表 1 筆，2 天，待審核 |
| 拒絕不存檔 | E003 送出特休 2026-10-17～10-18（只有週末） | 顯示「區間內沒有工作日」；列表仍是 1 筆 |
| 重新整理 | 重新載入頁面，再選 E003 | 那 1 筆仍在 |
| 換員工 | 改選 E001 | 只列 E001 的 3 筆，沒有 E003 的「感冒」假單 |

先前的人工驗收：
- TC-12：按鈕停用、錯誤後保留表單、`<script>` 原樣顯示成文字、重啟服務後資料仍在。
- 卡 I：curl 重現與修復。
- 票 002：標籤與 101 字錯誤訊息。

以上紀錄都在 `docs/06-test-plan.md`。

另外，E001 有一筆「特休 2026-11-13～11-14，1 天」不是 agent 送出的，推測是小組自己在頁面上手動操作留下的。天數正確：11-13 是週五，11-14 是週六。

## 追溯抽查：AC-02.4

| 環節 | 位置與內容 |
|---|---|
| AC | `docs/02-prd.md:37`：10-17～10-18（只有週末）→ 拒絕，指出沒有工作日 |
| FR | `docs/03-srs.md:16` FR-05：工作日數為 0 → 拒絕 |
| API | `docs/05-sds.md:91`、`:146`：`422 NO_WORKING_DAYS`，`field=start_date`，驗證第 6 步 |
| TC | `docs/06-test-plan.md:143-148` TC-07 ①②，筆數 0 |
| 程式 | `backend/app/rules.py:87-90` |
| 測試斷言 | `backend/tests/acceptance/test_submit_leave.py:137-154`：斷言 `422`、`code`、`field`，以及 `leave_count() == 0`。marker 為 `req("TC-07", "AC-02.4", "FR-05")` |
| 結果 | `pytest -k tc07`：2 passed（2026-11-01） |

小組仍需依 LEAVEBOT 交付要求，親手核對至少一條追溯鏈。

## 版控安全檢查

- 專案內（不含 `.venv`）沒有 `*.db`、`*.sqlite*`、`.env*`、`*.pem`、`*.key`。
- 程式與文件中沒有 api key、secret、password、token 等字樣。
- `.gitignore` 已涵蓋：
  - `backend/data/`、`data/`
  - `.venv/`、`*.egg-info/`、`__pycache__/`、`.pytest_cache/`
  - `.playwright-mcp/`（截圖與 console 紀錄）、`.archify/`、`.env`
- 這裡不是 git repo，所以無法以 `git status` 實際確認追蹤狀態。保存版本前請 `git init`（或移到 fork），執行 `git status`，只用明確路徑加入檔案。

## 未完成與已知缺口

- **測試缺口**（小組已接受）：`DB_ERROR`（500）、`INVALID_BODY`、`INVALID_REASON`、時段為陣列的情況，以及 API-04 的 `MISSING_FIELD`／`UNKNOWN_EMPLOYEE`，都已實作但沒有自動化 TC。NFR-05 效能待量測。
- **已於卡 K 處理（2026-11-01）**：
  - `docs/01`～`05` 的狀態改成「已確認」。
  - `docs/06-test-plan.md` 各 TC 的「執行方式」由「未執行」改成「已執行通過（見追溯表）」。
  - SDS「驗證責任與注入」補上模組層 `app` 由 conftest 隔離的說明。
  - 刪除 `diagrams/` 根目錄 3 份過時的檢查紀錄（`browser-check`、`finalize`、`finalize-summary`）。保留 `submit-leave.delivery.json`，因為它對應目前的 HTML；最新的完整檢查紀錄在 `diagrams/review-1/`。
- **平台**：macOS／Linux 沒有實測。
- **部署**：不適用，只在本機執行；上線前的缺口見 `docs/04-sad.md`。
