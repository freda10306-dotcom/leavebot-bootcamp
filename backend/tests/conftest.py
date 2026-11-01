"""全測試共用：在任何 app 模組被匯入前，把 LEAVEBOT_DB 指到暫存位置。

app.main 在模組層執行 `app = create_app()`；若不先設定，匯入時會建立
backend/data/leavebot.db，違反 NFR-03（測試不讀寫開發資料庫）。
"""

import os
import tempfile
from pathlib import Path

_SESSION_DIR = tempfile.mkdtemp(prefix="leavebot-tests-")
os.environ["LEAVEBOT_DB"] = str(Path(_SESSION_DIR) / "import-guard.db")
