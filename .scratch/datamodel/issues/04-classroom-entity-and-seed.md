# 04: Classroom 實體與教室模擬資料

**What to build:** 完成 `Classroom` 資料實體與 5 間教室內建模擬資料，補齊教室設備清單欄位以支援後續教室配置篩選與驗證，並能與 JSON 格式安全互轉。

**Blocked by:** 01: 領域常數與例外階層基礎

**Status:** ready-for-agent

- [ ] 依 TDD 流程（`Red → Green → Refactor`）開發，將測試置於 `./tests/datamodel/` 目錄下（例如 `test_classroom.py`），並透過套件內部相對匯入使用例外模組。
- [ ] 實作 `@dataclass class Classroom`（以下為原型決議之型別形狀）：
  ```python
  @dataclass
  class Classroom:
      room_id: str
      capacity: int
      equipment: list[str]
  ```
- [ ] 在 `__post_init__` 檢核所有欄位並一次彙整全部錯誤至 `ValidationError(errors)`：`room_id` 去掉前後空白後為非空字串；`capacity` 為非 `bool` 之整數且 `>= 1`；`equipment` 須為清單且元素皆為非空字串、不得重複。
- [ ] 實作 `Classroom.from_dict()` 與 `Classroom.to_dict()`，對 `equipment` 執行防禦性複製，遇缺欄或無效資料時拋出 `ValidationError`。
- [ ] 建立從舊版 `model.classroom`（`"06206"`、`"03303"`、`"06302"`、`"02303"`、`"00101"`）轉換的 5 間教室 JSON 陣列模擬資料檔並填入合理的示範 `equipment` 清單，驗證全部 5 筆紀錄皆可通過 `Classroom.from_dict()` 載入。
- [ ] `./tests/datamodel/` 單元測試、`tests/common/test_spec_guardrails.py` 與 `uv run ruff check .` / `uv run ruff format --check .` 全數通過。
