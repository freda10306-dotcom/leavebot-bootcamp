# LeaveBot — 第二天的空白學生專案

第一天在獨立資料夾體驗 Vibe Coding、比較結果並練習 PRD；第二天用這個 repo，學習如何用規格、通用 skills、測試與人工驗收穩定交付。

**今天做一條完整路徑：選員工 → 填請假單 → 驗證 → 存檔 → 我的假單顯示待審核。** 主管核准、額度與一句話 AI 解析是延伸。

## 從這裡開始

1. Fork 本 repo 的 `main`，clone 自己的 fork。只複製 main 即可；checkpoint 從講師 upstream 取得。
2. 準備 Git、Python 3.12、能正常登入的 Claude Code 或 Codex，以及瀏覽器。Archify 使用 Node（套件最低 18；課前用受支援版本試跑），應用程式主線不需要 Node 或 LLM API key。
3. 從 [課程資料入口](course/README.md) 依序找到當前階段；在 repo 根目錄開工具，讀 [上課流程](course/01-上課/02-WORKFLOW.md) 的開場提示。Claude Code 用 `/技能`，Codex 用 `$技能`。
4. 依工作流程逐步產出文件、票與程式，不先複製空模板占位。需要同組已完成決策時先讀文件。

Windows 使用 Codex 共用技能前，確認 `.agents/skills` 是指向 `../.claude/skills` 的連結；無法建立連結時請講師協助，不能只以設定檔存在當成工具已接通。

`course/` 分成 [01-上課](course/01-上課/01-SETUP.md) 與 [02-補充](course/02-補充/01-HARNESS.md)。上課依編號讀目前需要的檔案與提示卡；工具說明、保底快照、範例及維護紀錄在補充區。[通用技能清單](.claude/skills/README.md)可按需要查。

`main` 只有教材與工具設定；`docs/`、`issues/`、`backend/`、`pyproject.toml` 由學生產生。checkpoint 是另外的教學快照。

講義與講師教材在 [ai-vibe-coding-beginner](https://github.com/Zenobia000/SDD-agent-coding-beginner)。技能與 guard 的來源及授權見 [THIRD-PARTY-NOTICES](.claude/THIRD-PARTY-NOTICES.md)。

## 本組成果：啟動 LeaveBot

在 repo 根目錄執行（Windows PowerShell；macOS／Linux 把 `.venv\Scripts\python.exe` 換成 `.venv/bin/python`）：

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -c course/01-上課/05-constraints.txt -e ".[dev]"
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend
```

瀏覽器開 `http://127.0.0.1:8000/`。資料庫預設在 `backend/data/leavebot.db`（不進版控），可用環境變數 `LEAVEBOT_DB` 指定其他位置。環境版本、測試與驗收證據、未完成項見 [docs/DELIVERY.md](docs/DELIVERY.md)。
