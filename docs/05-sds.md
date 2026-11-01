# 05 SDS — LeaveBot 請假系統

- 版本：v0.2（2026-11-01，卡 J：理由上限 200 → 100，D-07）
- 負責人：本組（D2 卡 E）
- 狀態：已確認（2026-11-01，小組於卡 K 確認）
- 上游：`docs/04-sad.md`、`docs/03-srs.md`。契約變更時同步更新 `docs/06-test-plan.md` 的 TC。

## 目錄

- [資料模型與不變量](#資料模型與不變量)
- [API 契約](#api-契約)
- [UI 與模組契約](#ui-與模組契約)
- [變更與未決](#變更與未決)

## 資料模型與不變量

員工資料在啟動時預先建立，本次不提供維護功能。假單只能經 API-03 新增，本次沒有修改或刪除功能。`days`、`status`、`id`、`created_at` 都由伺服器決定。

### `employees`

| 欄位 | 型別、格式與可空性 | 預設／約束 | 來源 |
|---|---|---|---|
| `employees.id` | TEXT，非空 | 主鍵 | FR-01 |
| `employees.name` | TEXT，非空 | — | FR-01 |

初始資料（2026-11-01 小組確認）：

| id | name |
|---|---|
| `E001` | 王小明 |
| `E002` | 李小華 |
| `E003` | 陳大同 |

### `leave_requests`

| 欄位 | 型別、格式與可空性 | 預設／約束 | 來源 |
|---|---|---|---|
| `leave_requests.id` | INTEGER，非空 | 主鍵，`AUTOINCREMENT` | FR-09（排序） |
| `leave_requests.employee_id` | TEXT，非空 | 外鍵 → `employees.id` | FR-01、FR-07 |
| `leave_requests.leave_type` | TEXT，非空 | `CHECK IN ('annual','personal','sick')` | FR-02 |
| `leave_requests.start_date` | TEXT `YYYY-MM-DD`，非空 | — | FR-02、FR-03 |
| `leave_requests.end_date` | TEXT `YYYY-MM-DD`，非空 | `end_date >= start_date` | FR-03 |
| `leave_requests.period` | TEXT，非空 | `CHECK IN ('full','am','pm')` | FR-02、FR-04 |
| `leave_requests.days` | REAL，非空 | `CHECK (days > 0)`，0.5 的倍數 | FR-05 |
| `leave_requests.reason` | TEXT，非空 | 預設 `''`；已去除前後空白，長度 ≤ 100 | FR-06 |
| `leave_requests.status` | TEXT，非空 | 預設 `'pending'`，`CHECK (status = 'pending')` | FR-07 |
| `leave_requests.created_at` | TEXT，ISO 8601 UTC，非空 | 由注入的時鐘產生 | FR-07 |

**不變量**
- 每筆假單的 `employee_id` 都存在於 `employees`。連線時開啟 `PRAGMA foreign_keys = ON`。
- `days` 等於 `count_days(start_date, end_date, period)`，而且大於 0。
- `status` 只會是 `pending`；資料表的 CHECK 是最後一道防線。
- 半天假（`am`、`pm`）的 `start_date == end_date`。
- 空理由存成 `''`，不存 `NULL`。

**交易與重複**
- 一次合法的 API-03 只執行一個 `INSERT`，包在單一交易中。
- 驗證失敗時不開始寫入；寫入失敗時回滾。
- 重複送出不去重，每次合法請求都新增一筆，`id` 不同（D-03）。

**初始化**
- `init_db(path)` 是冪等的：`CREATE TABLE IF NOT EXISTS`，員工用 `INSERT OR IGNORE`。
- 重複呼叫不會重複寫入員工，也不會刪除假單。

## API 契約

所有路由都在 `/api/` 下，前端用相對路徑呼叫，不開 CORS。回應是 JSON，`Content-Type: application/json`。

**錯誤格式**（API-02～04 共用）：

```json
{ "error": { "code": "END_BEFORE_START", "field": "end_date", "message": "結束日期不能早於開始日期" } }
```

`field` 在不屬於單一欄位時為 `null`。

**錯誤碼**

| code | HTTP | field | message | 規則 |
|---|---|---|---|---|
| `INVALID_BODY` | 422 | `null` | 請求格式錯誤 | 本文不是 JSON 物件 |
| `MISSING_FIELD` | 422 | 缺漏的欄位 | 請填寫＜欄位中文名＞ | FR-02 |
| `UNKNOWN_EMPLOYEE` | 422 | `employee_id` | 找不到這位員工 | FR-01、FR-02 |
| `INVALID_LEAVE_TYPE` | 422 | `leave_type` | 假別不正確 | FR-02 |
| `INVALID_DATE` | 422 | `start_date` 或 `end_date` | 日期格式不正確 | FR-02 |
| `INVALID_PERIOD` | 422 | `period` | 時段不正確 | FR-02 |
| `INVALID_REASON` | 422 | `reason` | 理由格式不正確 | FR-06（非字串） |
| `REASON_TOO_LONG` | 422 | `reason` | 理由最多 100 字（由上限常數產生） | FR-06 |
| `END_BEFORE_START` | 422 | `end_date` | 結束日期不能早於開始日期 | FR-03 |
| `HALF_DAY_MULTI_DAY` | 422 | `period` | 半天假只能是同一天 | FR-04 |
| `NO_WORKING_DAYS` | 422 | `start_date` | 區間內沒有工作日 | FR-05 |
| `DB_ERROR` | 500 | `null` | 系統暫時無法存檔，請稍後再試 | SAD 故障處理 |

欄位中文名：`employee_id` 員工、`leave_type` 假別、`start_date` 開始日期、`end_date` 結束日期、`period` 時段。

### API-01｜GET /api/health

用途：確認服務啟動（票 000）。不碰資料庫。

- 成功：`200 {"status": "ok"}`。
- 失敗：服務沒有啟動時無回應；首頁顯示「無法連線」。

### API-02｜GET /api/employees（FR-01）

頁面載入時呼叫，取得下拉選單內容。沒有副作用。

- 成功：`200`，依 `id` 由小到大：

  ```json
  [{"id": "E001", "name": "王小明"}, {"id": "E002", "name": "李小華"}, {"id": "E003", "name": "陳大同"}]
  ```

- 失敗：資料庫錯誤回 `500 DB_ERROR`。

### API-03｜POST /api/leave-requests（FR-02～FR-08、FR-10）

使用者按送出時呼叫。合法時新增一筆假單，拒絕時資料不變。

**請求**

```json
{
  "employee_id": "E001",
  "leave_type": "annual",
  "start_date": "2026-10-12",
  "end_date": "2026-10-14",
  "period": "full",
  "reason": "家庭旅遊"
}
```

- `reason` 可省略或為 `null`，都視為空。
- 未知欄位（例如 `status`、`days`、`id`）一律忽略，不報錯（FR-07）。

**驗證順序**：依序檢查，遇到第一個錯誤就回傳。

1. 本文必須是 JSON 物件，否則 `INVALID_BODY`。
2. FR-02，欄位依 `employee_id` → `leave_type` → `start_date` → `end_date` → `period` 的順序：
   - 缺漏、`null`、非字串的空值，或去除空白後為空字串 → `MISSING_FIELD`。
   - 值不合法 → 該欄位的 `UNKNOWN_EMPLOYEE`、`INVALID_LEAVE_TYPE`、`INVALID_DATE` 或 `INVALID_PERIOD`。
   - 非字串的非空值（例如數字）視為不合法值。
   - 日期以 `date.fromisoformat` 解析，而且必須剛好 10 個字元，例如 `2026-2-3` 不合法。
3. FR-06：`reason` 不是字串也不是 `null` → `INVALID_REASON`；去除前後空白後 `len > 100` → `REASON_TOO_LONG`。上限與錯誤訊息都由 `app.rules.REASON_MAX_CHARS` 產生，只改一處。
4. FR-03：`end_date < start_date` → `END_BEFORE_START`。
5. FR-04：`period` 是 `am` 或 `pm`，而且 `start_date != end_date` → `HALF_DAY_MULTI_DAY`。
6. FR-05：工作日數為 0 → `NO_WORKING_DAYS`。

**成功**：`201`，回傳新增的整筆資料：

```json
{
  "id": 1,
  "employee_id": "E001",
  "leave_type": "annual",
  "start_date": "2026-10-12",
  "end_date": "2026-10-14",
  "period": "full",
  "days": 3.0,
  "reason": "家庭旅遊",
  "status": "pending",
  "created_at": "2026-10-12T01:00:00+00:00"
}
```

**失敗**：422 加上錯誤本文，資料不變；或 500 `DB_ERROR`，交易回滾，資料不變。

### API-04｜GET /api/leave-requests?employee_id=E001（FR-09）

選員工或送出成功後呼叫。沒有副作用。

- 成功：`200`，只回傳該員工的假單，依 `id` 由大到小（新到舊）。每筆欄位同 API-03 的成功回應。沒有假單時回 `[]`。
- 失敗：
  - 缺 `employee_id` 或為空 → `422 MISSING_FIELD`。
  - 不在名單 → `422 UNKNOWN_EMPLOYEE`。
  - 資料庫錯誤 → `500 DB_ERROR`。

## UI 與模組契約

### UI-01｜請假頁（US-01～US-03）

單頁 `index.html`，由 `app.js` 操作。

- **載入**：呼叫 API-02，填入員工下拉。第一個選項為「請選擇員工」（值為空），還沒選員工時列表顯示「請先選擇員工」。
- **表單**：
  - 假別下拉：`annual` 特休、`personal` 事假、`sick` 病假，第一項為空。
  - 開始日期、結束日期：`<input type="date">`。
  - 時段下拉：`full` 整天、`am` 上午、`pm` 下午。
  - 理由：`<textarea>`，標籤寫「選填，最多 100 字」。不加 `maxlength`：瀏覽器以 UTF-16 計數，與後端的 code point 計數不同（D-07 決策時確認）。
  - 前端**不加** `required` 或長度限制，所有判斷交給後端，畫面上看得到後端的錯誤（ADR-01）。
- **送出**：
  - 停用送出按鈕，呼叫 API-03。
  - `201`：顯示「已送出，狀態：待審核」，清空假別、日期、時段與理由（保留所選員工），重新呼叫 API-04。
  - `422`：顯示 `error.message`，保留表單（D-04）。
  - 500 或網路錯誤：顯示「系統暫時無法存檔，請稍後再試」，保留表單。
  - 不論結果都在最後恢復按鈕（FR-10）。
- **我的假單**：改選員工時呼叫 API-04。每筆顯示假別中文名、開始～結束、時段中文名、天數、理由、「待審核」。空清單時顯示「目前沒有假單」（AC-03.2）。所有使用者文字一律用 `textContent`，不用 `innerHTML`（NFR-01）。

### 模組與公開函式

- **`app.rules.count_days(start: date, end: date, period: str) -> float`**（FR-05）
  - 含首尾逐日計算週一至週五的天數 n。`full` 回傳 `n`，`am`、`pm` 回傳 `0.5 × n`。
  - 呼叫前提是已通過 FR-03、FR-04。
- **`app.rules.validate_leave(payload: object, employee_ids: set[str]) -> LeaveInput | LeaveError`**（FR-02～06）
  - 純函式，依上方驗證順序檢查。
  - 成功時回傳已清理的欄位（`reason` 已去除前後空白）與 `days`。
  - 失敗時回傳第一個錯誤的 `code`、`field`、`message`。
  - 不讀資料庫、不讀時鐘。
- **`app.db.connect(path) -> sqlite3.Connection`**
  - 開啟 `foreign_keys`，設定 `row_factory = sqlite3.Row`。
- **`app.db.init_db(path) -> None`**
  - 冪等地建表並寫入員工，自動建立上層目錄。
- **`app.db.list_employees(conn)`、`insert_leave(conn, data, created_at) -> dict`、`list_leaves(conn, employee_id) -> list[dict]`**
  - 一律使用 `?` 參數化 SQL，不用字串拼接（NFR-01）。
  - `insert_leave` 在 `with conn:` 交易內執行。
- **`app.main.create_app(db_path: str | None = None, now: Callable[[], datetime] | None = None) -> FastAPI`**
  - `db_path` 未給時讀 `LEAVEBOT_DB`，再沒有則用 `backend/data/leavebot.db`。
  - `now` 未給時用 `datetime.now(timezone.utc)`。
  - 建立 app 時呼叫 `init_db`。
  - 每個請求開一條連線，並在 `finally` 關閉。
  - 先登記所有 `/api` 路由，最後才 `app.mount("/", StaticFiles(directory=<static>, html=True))`。
  - 模組層提供 `app = create_app()`，給 uvicorn 使用。

### 驗證責任與注入

- **伺服器**負責全部業務規則。**客戶端**只做顯示與按鈕鎖定。
- **資料庫注入**：測試以 `create_app(db_path=tmp_path / "test.db", now=lambda: FIXED)` 建立 app，再用 `TestClient` 呼叫，不讀寫開發資料庫（NFR-03）。
- **時鐘**：主線規則不使用「今天」（D-02），所以不讀 `LEAVEBOT_TODAY`。時鐘只用來產生 `created_at`；測試注入固定值 `2026-10-12T01:00:00+00:00`，讓回應可以完整比對。
- **模組層 `app` 的隔離**（NFR-03）：`app.main` 在模組層執行 `app = create_app()`，一匯入就會初始化資料庫。所以 `backend/tests/conftest.py` 在任何 app 匯入之前，把 `LEAVEBOT_DB` 指到暫存目錄；新增測試不得繞過它。（2026-11-01 票 001 發現，見 LESSONS）
- **重啟持久性**（NFR-02）：測試以同一個 `db_path` 建立第二個 app，查得到先前的資料。

## 變更與未決

- **相容性**：第一版，沒有既有資料或 API，不需要遷移。
- **與票 000 的關係**：票 000 只需要 `create_app()` 加上 API-01 與靜態頁；資料庫與 API-02～04 屬於票 001。
- **待決**：無。員工名單（E001～E003）與「驗證失敗一律 422」已於 2026-11-01 由小組確認。
- **FR／NFR 設計落點**：

| 需求 | 落點 |
|---|---|
| FR-01 | `employees`、API-02、`UNKNOWN_EMPLOYEE` |
| FR-02 | `validate_leave` 第 2 步 |
| FR-03 | 第 4 步 |
| FR-04 | 第 5 步 |
| FR-05 | `count_days`、第 6 步 |
| FR-06 | 第 3 步 |
| FR-07 | API-03 忽略未知欄位、`status` CHECK |
| FR-08 | 先驗證後寫入、交易回滾 |
| FR-09 | API-04、ADR-02 |
| FR-10 | UI-01 按鈕鎖定、不去重 |
| NFR-01 | 參數化 SQL、`textContent` |
| NFR-02 | 檔案型 SQLite、重啟測試 |
| NFR-03 | `create_app` 注入 |
| NFR-04 | 錯誤碼表與 UI-01 |
| NFR-05 | 不需設計落點，待量測 |
