# 05: Activity 實體（含 .slots 推算）與活動模擬資料

**What to build:** 完成 `Activity` 資料實體與 10 項活動內建模擬資料，採用標準庫 `datetime.date` / `datetime.time` 表示日期與時間並自動推算唯讀 `.slots` 屬性，使「活動 vs. 課程」能共用節次表示法、同時為「活動 vs. 活動」保留精確日期時間比較能力。

**Blocked by:** 01: 領域常數與例外階層基礎

**Status:** ready-for-agent

- [ ] 依 TDD 流程（`Red → Green → Refactor`）開發，將測試置於 `./tests/datamodel/` 目錄下（例如 `test_activity.py`），並透過套件內部相對匯入使用常數與例外模組。
- [ ] 實作 `@dataclass class Activity`（以下為原型決議之型別形狀）：
  ```python
  @dataclass
  class Activity:
      activity_id: str
      name: str
      date: datetime.date
      start_time: datetime.time
      end_time: datetime.time
      category: str
      capacity: int
      registered: int
      required_equipment: list[str]
      room: str | None
  ```
- [ ] 在 `__post_init__` 檢核所有欄位並一次彙整全部錯誤至 `ValidationError(errors)`：`activity_id`、`name`、`category` 為去掉前後空白後非空字串；`room` 為 `None` 或非空字串；`date` 為 `datetime.date`（明確排除 `datetime.datetime`）；`start_time`、`end_time` 為 `datetime.time` 且 `end_time > start_time`；`capacity >= 1`、`registered >= 0`（非 `bool` 整數，不在此層拒絕 `registered > capacity`）；`required_equipment` 為無重複非空字串清單。
- [ ] 實作唯讀 `@property def slots(self) -> list[str]`：以 `str(self.date.isoweekday())` 與 `PERIOD_TIMES` 依 `PERIODS` 順序檢查開區間重疊（`max(self.start_time, p_start) < min(self.end_time, p_end)`），端點相接（如 `09:00` 結束與 `09:10` 開始）不算重疊、完全落在課間休息回傳 `[]`。
- [ ] 實作 `Activity.from_dict()`（解析 ISO `"YYYY-MM-DD"` 與 `"HH:MM"` 字串、格式錯誤或缺欄時拋出 `ValidationError`、複製 `required_equipment`）與 `Activity.to_dict()`（輸出 `.isoformat()` 字串並複製 `required_equipment`）。
- [ ] 建立從舊版 `model.activitys`（`A01`～`A10`）轉換的 10 項活動 JSON 陣列模擬資料檔：日期保留原月／日並加上 `2026-`（`YYYY-MM-DD`）、依原節次對照 `PERIOD_TIMES` 推算首節開始與末節結束時間、保留原第 5 欄為 `registered` 與第 6 欄為 `capacity`、補齊合理 `category` 與 `required_equipment`，並驗證全部 10 筆可通過 `Activity.from_dict()` 載入。
- [ ] `./tests/datamodel/` 單元測試、`tests/common/test_spec_guardrails.py` 與 `uv run ruff check .` / `uv run ruff format --check .` 全數通過。
