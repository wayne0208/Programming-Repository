# 06: load_seed_data 載入器與套件根層匯出整合

**What to build:** 完成 `SeedData` 與容錯模擬資料載入器 `load_seed_data()`，並於 `datamodel` 套件根層統一對外匯出所有公開符號，讓各功能模組得以直接透過 `from datamodel import ...` 安全取得獨立的資料集合複本。

**Blocked by:** 02: Course 實體與課程模擬資料, 03: Student 實體與學生模擬資料, 04: Classroom 實體與教室模擬資料, 05: Activity 實體（含 .slots 推算）與活動模擬資料

**Status:** ready-for-agent

- [ ] 依 TDD 流程（`Red → Green → Refactor`）開發，將整合與載入測試置於 `./tests/datamodel/` 目錄下（例如 `test_loader_and_exports.py`）。
- [ ] 實作 `@dataclass class SeedData`（`courses: dict[str, Course]`、`students: dict[str, Student]`、`classrooms: dict[str, Classroom]`、`activities: dict[str, Activity]`）與 `load_seed_data() -> tuple[SeedData, list[str]]`，使用 `importlib.resources` 讀取四份套件內建 JSON 檔案。
- [ ] 確保 `load_seed_data()` 逐筆驗證紀錄：遇到單筆格式／驗證錯誤（`ValidationError`）、JSON 損毀、檔案缺失或重複 ID（保留第一筆合法紀錄）時略過異常資料不崩潰，將來源與原因記錄至 `warnings: list[str]`，且每次呼叫皆回傳彼此獨立的 `SeedData` 複本。
- [ ] 於 `datamodel` 套件根層設定 `__all__` 並匯出 `Course`、`Student`、`Classroom`、`Activity`、`SeedData`、`load_seed_data`、`DAYS`、`PERIODS`、`PERIOD_TIMES`、`COURSE_CATEGORIES`、`ScheduleError`、`ValidationError`、`NotFoundError`、`DuplicateIdError`，確保僅透過 `from datamodel import ...` 即可使用所有公開介面。
- [ ] 端到端驗證預設模擬資料載入回傳 20 門課程、15 名學生、5 間教室、10 項活動且 `warnings == []`，舊版 `src/model.py` 維持不變且可運行，並通過完整 `uv run pytest`（含 `./tests/datamodel/` 與 `tests/common/test_spec_guardrails.py`）與 `uv run ruff check .` / `uv run ruff format --check .`。
