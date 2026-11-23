# 03: Student 實體與學生模擬資料

**What to build:** 完成 `Student` 資料實體與 15 名學生內建模擬資料，將舊版共用可變二維課表改為每位學生獨立的一維已選課程與活動代號清單，確保單一真相來源與跨模組安全性。

**Blocked by:** 01: 領域常數與例外階層基礎

**Status:** ready-for-agent

- [ ] 依 TDD 流程（`Red → Green → Refactor`）開發，將測試置於 `./tests/datamodel/` 目錄下（例如 `test_student.py`），並透過套件內部相對匯入使用例外模組。
- [ ] 實作 `@dataclass class Student`（以下為原型決議之型別形狀）：
  ```python
  @dataclass
  class Student:
      student_id: str
      name: str
      department: str
      credit_limit: int
      enrolled_courses: list[str]
      enrolled_activities: list[str]
  ```
- [ ] 在 `__post_init__` 檢核所有欄位並一次彙整全部錯誤至 `ValidationError(errors)`：`student_id`、`name`、`department` 去掉前後空白後為非空字串（`student_id` 統一為非空字串，不限定前綴）；`credit_limit` 為非 `bool` 之正整數（`> 0`）；`enrolled_courses` 與 `enrolled_activities` 須為清單且元素皆為非空字串、不得重複。
- [ ] 實作 `Student.from_dict()` 與 `Student.to_dict()`，對兩個清單欄位執行防禦性複製以隔離外部 list 修改，遇缺欄或型別／格式錯誤時拋出 `ValidationError`。
- [ ] 建立從舊版 `model.students` 轉換的 15 名學生 JSON 陣列模擬資料檔：學號轉為字串（如 `"1150101"`），將原本 `7×12` 二維課表依掃描順序攤平並去重後拆分放入各自獨立的 `enrolled_courses`（如 `"CS..."`）與 `enrolled_activities`（例如 `"1150108"` 對應的 `"A06"`），並驗證全部 15 筆紀錄皆可通過 `Student.from_dict()` 載入。
- [ ] `./tests/datamodel/` 單元測試、`tests/common/test_spec_guardrails.py` 與 `uv run ruff check .` / `uv run ruff format --check .` 全數通過。
