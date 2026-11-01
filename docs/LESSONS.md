# LESSONS —— LeaveBot 的經驗紀錄

> 專案自己的記憶：AI 誤解了什麼、產出和講義不一樣時怎麼對齊、踩過什麼坑。agent 在每張票結束時補，人負責刪掉不重要的，並把重複出現的升級成 `AGENTS.md`「本專案決策」的規則。

## 目錄

- [偏差紀錄](#偏差紀錄)
- [規格誤解](#規格誤解)
- [踩過的坑](#踩過的坑)
- [已升級成規則](#已升級成規則)

## 偏差紀錄

### 2026-11-01／D2 卡 G｜拆票時上游規格不存在

- 規格說：卡 G 依 `docs/05-sds.md`、`docs/06-test-plan.md` 拆票（WORKFLOW 的順序是卡 A～F 之後才到 G）；實際做了：小組直接從卡 G 開始，repo 沒有 `docs/`，`Downloads` 底下也找不到 LeaveBot 規格。
- 發現方式：agent 讀檔時找不到兩份輸入，停止拆票並回報。
- 對齊方式與證據：小組選擇從卡 A 依序補做 `docs/01`～`06`（2026-11-01 完成），再回到卡 G。
- 後續文件：無；WORKFLOW 本身的順序是正確的。

### 2026-11-01／票 001｜測試匯入 app 時建立了開發資料庫

- 規格說：測試不讀寫開發資料庫（SRS NFR-03、AGENTS.md）；實際做了：`app.main` 在模組層執行 `app = create_app()`，測試一匯入就用預設路徑建立 `backend/data/leavebot.db`。health 測試也沒有傳入 `db_path`。
- 發現方式：TC-01 轉綠後，agent 主動檢查 `backend/data/`，發現檔案被建立。
- 對齊方式與證據：
  - 新增 `backend/tests/conftest.py`，在任何 app 匯入前，把 `LEAVEBOT_DB` 指到暫存目錄。
  - health 測試改為傳入 `tmp_path`。
  - 刪掉測試誤建的檔案（只有種子員工）。
  - 完整 pytest 之後 `backend/data/` 不再出現。
- 後續文件：已於 2026-11-01 卡 K 補進 SDS「驗證責任與注入」。

### 2026-11-01／卡 I｜非字串的欄位值回 500，不是 422

- 規格說：非字串的非空值視為不合法值，回 422 與該欄位的錯誤碼（SDS API-03 驗證順序第 2 步）。實際做了：`employee_id` 為陣列、`leave_type` 為物件時，回框架預設的 `500 Internal Server Error`，本文也不是統一錯誤格式。數字不受影響，因為數字可以做集合查詢。
- 發現方式：卡 I 對照 SDS 檢查驗證程式，用 curl 對執行中的伺服器重現；伺服器紀錄有 `TypeError: unhashable type: 'list'`／`'dict'`。
- 分類：實作錯誤，不是環境問題，也不是規格矛盾。
- 原因：`app/rules.py` 在檢查型別之前，就用 `value not in employee_ids`（第 53 行）和 `value not in LEAVE_TYPES`（第 55 行）做集合查詢，陣列和物件不能拿來查集合，於是拋出 `TypeError`。`main.py` 只接資料庫錯誤，所以變成 500。
- 對齊方式與證據：
  1. 經小組同意，在 TC-04 加兩個變體（陣列員工、物件假別）。修復前 `2 failed, 5 passed`，失敗訊息正是上面那兩個 `TypeError`。
  2. 修改 `validate_leave`：員工、假別、時段先檢查是不是字串，再做集合查詢。
  3. 修復後 TC-04 `7 passed`，完整 pytest `29 passed`。
  4. 重啟伺服器後重跑 curl：陣列員工、物件假別、陣列時段都回 422 與正確錯誤碼，E001 筆數不變。
- 後續文件：06 的 TC-04 表已加兩列。時段為陣列的情況只用 curl 驗證過，沒有寫成自動化測試。

### 2026-11-01／卡 J、票 002｜需求變更：理由上限 200 → 100 字

- 規格說：卡 J 把理由上限從 200 字改成 100 字。本組原本也是 200 字（D-01），與卡 J 的假設一致，不需要講師確認差異。
- 發現方式：子代理只讀分析，列出受影響的 AC、FR、API、畫面、TC 與程式位置；小組依建議確認 7 項決策。
- 對齊方式與證據：
  - 依「規格 → 案例 → 測試 → 程式」的順序做：
    1. 新增 D-07，更新 01～06 與 AGENTS.md。
    2. 新增 101 字測試，看到舊實作的紅燈（`assert 201 == 422`）。
    3. 依 06 v0.2 修訂兩條 TC-08 測試，並刪除 201 字那條。
    4. 改程式，得到綠燈。
  - 結果：完整 pytest `29 passed`；人工確認標籤與錯誤訊息。
  - 錯誤訊息改由 `REASON_MAX_CHARS` 產生，下次調整上限只需改一處。
- 後續文件：06 v0.2 已回填。刪除 201 字測試是依 D-07 修訂測試規格，不是放寬條件：「剛好超過上限」的邊界由 101 字承接。

## 規格誤解

目前沒有。

## 踩過的坑

- **Archify 線段重疊**：Archify 第一次產生 `diagrams/submit-leave.html` 時，`finalize` 回報 `composition/ambiguous-corridor`，「送出 → 驗證」與「拒絕 → 顯示錯誤」兩條線共用通道。只指定線段方向又被判為不可行。把「頁面顯示錯誤」節點移到拒絕路徑那一排後通過。
- **Archify 預設圖例不合用**：預設的 zh-TW 圖例把 backend 標成「Agent 邏輯」、database 標成「脈絡／追蹤」，不符合 LeaveBot。要在 `meta.legend.entries` 自訂文字。自動檢查不會抓到這個問題，要靠目視檢查。
- **Playwright 不能開 `file://`**：MCP 的 Playwright 擋掉 `file://`。要先用 `.venv\Scripts\python.exe -m http.server` 在本機起服務，再用 `http://127.0.0.1:<port>/` 開圖。

- **pytest 出現 `StarletteDeprecationWarning`**（票 000，2026-11-01）：用 constraints 裡的 starlette 1.10.0 加 httpx 0.28.1 時，`TestClient` 會提示改裝 `httpx2`。這只是警告，測試照常通過。STACK 的套件白名單是 `httpx`，所以不換套件。

- **一寫就綠的測試要做改壞檢查**（票 001）：TC-03、09、10、11 一寫就綠，因為前面的 TC 已經實作了該行為。暫時把實作改壞（例如排序改成 ASC），確認測試會轉紅後再還原，證據記在 06 的執行紀錄。
- **系統的 `python` 不是真的 Python**（票 001）：在這台 Windows 上，`python` 是 Microsoft Store 的捷徑，會啟動 REPL 然後直接結束，結束碼還是 0，所以腳本看起來「成功」但其實什麼都沒做。一律用 `.venv\Scripts\python.exe`。

## 已升級成規則

目前沒有。
