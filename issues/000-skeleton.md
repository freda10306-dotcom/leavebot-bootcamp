# 000 骨架可啟動並回報健康狀態

- 狀態：完成（2026-11-01），待小組驗收
- 估計：小（約 30～45 分鐘）
- 依賴：無
- 被依賴：`issues/001-submit-leave.md`

## 成果

FastAPI 提供首頁，首頁以 `fetch('/api/health')` 顯示「已連線」；health 測試實際執行通過。**不寫任何請假邏輯**：沒有資料庫、員工或假單 API。

## 必讀規格

- `course/01-上課/04-STACK.md`：「骨架票 000 的要求」第 1～5 點、「安裝與執行」。
- `docs/05-sds.md`：API-01、「模組與公開函式」中 `app.main.create_app` 的簽名與掛載順序。
- `docs/04-sad.md`：元件與資料流（靜態檔由同一個 FastAPI 提供、同來源）。
- `AGENTS.md`：實作與驗收、技術邊界。

## 範圍

1. 根目錄 `pyproject.toml`：
   - `requires-python = ">=3.12"`；依賴只有 `fastapi`、`uvicorn`、`httpx`；`[project.optional-dependencies] dev = ["pytest"]`。
   - setuptools：`package-dir = {"" = "backend"}`、`[tool.setuptools.packages.find] where = ["backend"]`，並包含 `app/static/*` 為 package data。
   - pytest：`testpaths = ["backend/tests"]`、`pythonpath = ["backend"]`、`addopts = "--import-mode=importlib"`，註冊 `req` marker。
2. `backend/app/__init__.py`、`backend/app/main.py`：
   - 提供 `create_app(db_path=None, now=None) -> FastAPI`。本票的兩個參數只要先保留簽名，不使用。
   - 模組層提供 `app = create_app()`。
   - 先登記 `GET /api/health`，最後才 `app.mount("/", StaticFiles(..., html=True))`。
3. `backend/app/static/index.html`、`app.js`、`style.css`：首頁呼叫 `/api/health`，成功顯示「已連線」，失敗顯示「無法連線」。用 `textContent` 寫入。
4. `backend/tests/` 底下一個 health 測試，用 `TestClient(create_app())`。

不做：`app.rules`、`app.db`、API-02～04、表單、資料庫檔。

## 骨架檢查（無 TC 編號）

- [x] `GET /api/health` 回 `200` 與 `{"status": "ok"}`（自動化測試）。
- [x] `GET /` 回 `200`，內容為 `index.html`（自動化測試或人工）。
- [x] 安裝指令在既有 `.venv` 重跑不出錯。
- [x] 實際啟動 uvicorn，瀏覽器開首頁看到「已連線」；Ctrl+C 停止後再啟動一次仍可開啟。
- [x] `.gitignore` 已涵蓋 `backend/data/`、`.venv/`、`*.egg-info/`（目前已有，確認即可）。

## 驗收指令（Windows，repo 根目錄）

```powershell
.venv\Scripts\python.exe -m pip install -c course/01-上課/05-constraints.txt -e ".[dev]"
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend
```

啟動後開 `http://127.0.0.1:8000/`；port 被占用時加 `--port 8001`。macOS／Linux 把 `.venv\Scripts\python.exe` 換成 `.venv/bin/python`。

## 完成時回報

- 實際執行的 pytest 輸出。
- 啟動網址與首頁結果。
- 實際安裝的套件版本（記在交付紀錄）。
- 未驗證事項。
- 有偏差時記到 `docs/LESSONS.md`。
