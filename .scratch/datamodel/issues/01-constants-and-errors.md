# 01: 領域常數與例外階層基礎

**What to build:** 建立 `datamodel` 套件的基礎領域常數與統一例外階層，讓後續四個實體模組與各功能模組都能依同一組時間節次、類別常數及結構化錯誤模型進行平行開發，並符合自動靜態規範檢查。

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] 依 TDD 流程（`Red → Green → Refactor`）開發，並將所有測試檔案置於 `./tests/datamodel/` 目錄下（例如 `test_constants_and_errors.py`）。
- [ ] 建立 `datamodel` 套件基礎與領域常數：`DAYS = "1234567"`、`PERIODS = "123456789abc"`、`COURSE_CATEGORIES = ("必修", "選修")`，以及 `PERIOD_TIMES: dict[str, tuple[datetime.time, datetime.time]]`（依序對應第 `"1"`～`"9"`、`"a"`、`"b"`、`"c"` 節，自 `08:10–09:00` 起每小時一節、每節 50 分鐘至 `19:10–20:00`）。
- [ ] 建立統一例外階層：基底 `ScheduleError(Exception)`，以及子類別 `ValidationError(ScheduleError)`、`NotFoundError(ScheduleError)`、`DuplicateIdError(ScheduleError)`。
- [ ] `ValidationError` 具備 `errors: list[str]` 屬性，能將傳入的單一錯誤字串或錯誤字串序列正規化為非空 `list[str]`，並格式化成可讀的例外訊息摘要。
- [ ] `./tests/datamodel/` 單元測試、`tests/common/test_spec_guardrails.py`（安全匯入、無可變頂層全域變數與例外規範檢查），以及 `uv run ruff check .` / `uv run ruff format --check .` 全數通過。
