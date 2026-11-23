# 02: Course 實體與課程模擬資料

**What to build:** 完成 `Course` 資料實體與 20 門課程內建模擬資料，使系統能以具欄位驗證與 JSON 雙向轉換能力的強型別物件承載課程資訊，並能完整反序列化既有課程測資。

**Blocked by:** 01: 領域常數與例外階層基礎

**Status:** ready-for-agent

- [ ] 依 TDD 流程（`Red → Green → Refactor`）開發，將測試置於 `./tests/datamodel/` 目錄下（例如 `test_course.py`），並透過套件內部相對匯入使用常數與例外模組。
- [ ] 實作 `@dataclass class Course`（以下為原型決議之型別形狀）：
  ```python
  @dataclass
  class Course:
      code: str
      name: str
      credits: int
      category: str
      teacher: str
      capacity: int
      enrolled: int
      room: str
      slots: list[str]
  ```
- [ ] 在 `__post_init__` 檢核所有欄位並一次彙整全部錯誤至單一 `ValidationError(errors)`：`code`、`name`、`teacher`、`room`、`category` 去掉前後空白後為非空字串；`category` 須屬於 `COURSE_CATEGORIES`；`credits` 為非 `bool` 之正整數（`> 0`）；`capacity >= 1`、`enrolled >= 0`（不在此層拒絕 `enrolled > capacity`）；`slots` 為非空且無重複元素的清單，每筆須為長度 3 且符合 `"<day>-<period>"`（`DAYS` 與 `PERIODS` 範圍）。
- [ ] 實作 `Course.from_dict()`（非 `Mapping`、缺欄、型別或格式不符時拋出 `ValidationError`，並複製 `slots` 清單）與 `Course.to_dict()`（回傳可 JSON 序列化字典且複製內部 `slots` 清單）。
- [ ] 建立從舊版 `model.course`（`CS001`～`CS020`）轉換的 20 門課程 JSON 陣列模擬資料檔，並驗證全部 20 筆紀錄皆可無錯誤通過 `Course.from_dict()` 載入。
- [ ] `./tests/datamodel/` 單元測試、`tests/common/test_spec_guardrails.py` 與 `uv run ruff check .` / `uv run ruff format --check .` 全數通過。
