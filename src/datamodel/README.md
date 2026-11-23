# DataModel

## 簡介

### 有什麼

- **4 個資料實體**：`Course`、`Student`、`Classroom`、`Activity`都是`@dataclass`。建構時會自動驗證所有欄位並一次回報全部錯誤（`ValidationError`）。
- **模擬資料**：原 `model.py` 的資料（20 門課、15 名學生、5 間教室、10 項活動）已轉為 JSON 檔放在`src/datamodel/seed/`，透過 `load_seed_data()` 載入，照理講載入資料應該只出現在測試案例與未來主程式入口。
- **僅定義資料結構**：對資料的操作直接用`dict`與`dataclass`的操作方式。
- **常數與例外**：`DAYS`、`PERIODS`、`PERIOD_TIMES`、`COURSE_CATEGORIES`；`ScheduleError` 及其子類別 `ValidationError`、`NotFoundError`、`DuplicateIdError`。
- **尚未實作的擴充**：F2～F10 後續可能新增的資料模型（如結構化 `Conflict`、活動取消狀態、篩選／評分／效能統計模型、校園地圖與教室建築物、動態事件模型）追蹤於 Issue [#6](https://github.com/wayne0208/Programming-Repository/issues/6)。

### 怎麼用

使用`from datamodel import xxx`導入需要用到的資料（使用 `import datamodel` 後讀 `datamodel.xxx`，會觸發 CI Guardrail的全域變數報錯）。  
以下是一個 `pytest` 測試案例示範導入`datamodel`及`load_seed_data()`：

```python
import pytest 

# 只導入需要用到的實體
from datamodel import Course, ValidationError, load_seed_data


def test_load_and_use_seed_data() -> None:
    seed, warnings = load_seed_data()   # 載入模擬資料
    assert warnings == []
    assert seed.courses["CS001"].name == "程式設計"
    assert seed.activities["A01"].slots == ["2-7"]

    new_course = Course(
        code="CS021",
        name="演算法",
        credits=3,
        category="必修",
        teacher="王教授",
        capacity=50,
        enrolled=0,
        room="06206",
        slots=["1-3", "1-4"],
    )
    seed.courses[new_course.code] = new_course
    assert "CS021" in seed.courses
```

以下示範實現刪除課程的功能函式如何只接收所需的集合參數並操作實體：

```python
# 只導入需要用到的實體
from datamodel import Course, NotFoundError, Student, ValidationError

# 函式只接受需要的資料
def drop_course(
    students: dict[str, Student],   # 包裝成dict來方便操作
    courses: dict[str, Course],
    student_id: str,
    course_code: str,
) -> None:
    student = students.get(student_id)
    if student is None:
        raise NotFoundError(f"找不到學生: {student_id}")

    course = courses.get(course_code)
    if course is None:
        raise NotFoundError(f"找不到課程: {course_code}")

    if course_code not in student.enrolled_courses:
        raise ValidationError(f"學生 {student_id} 未選修 {course_code}")

    student.enrolled_courses.remove(course_code)
    course.enrolled -= 1
```

**如何操作這些實體：** `datamodel` 僅負責資料型別、欄位驗證、序列化與模擬資料載入，不含 CRUD 函式；各功能模組（F1～F10）直接操作傳入的 `dict[str, Entity]`：

- **查詢**：`courses.get(code)` 依 ID 查詢，或走訪 `courses.values()` 條件篩選。
- **新增**：檢查 `code in courses`（重複時拋出 `DuplicateIdError`），再寫入 `courses[course.code] = course`。
- **修改**：以新欄位重建實體覆寫 `courses[code] = updated`（重新觸發 `__post_init__` 驗證）。
- **刪除**：不存在時拋出 `NotFoundError`，通過業務檢核後執行 `del courses[code]`。

**常用約定：**

- **傳參方式**：功能函式只傳入實際需要的 `dict[str, Entity]` 參數（如 `courses`、`students`）。
- **寫入與查詢分工**：業務檢查（如衝堂清單）直接回傳結果；寫入驗證全過才就地更新集合。
- **時間比對**：活動對課程比對 `.slots`；活動對活動直接比對 `date` 與 `start_time` / `end_time`。

---

## 函式介紹

### `errors.py`

統一例外階層（所有排課領域例外皆繼承 `ScheduleError`）：

<!-- markdownlint-disable MD033 -->
| 類別 | 屬性 / 簽章 | 用途與行為 |
| :--- | :--- | :--- |
| `ScheduleError(Exception)` | — | 所有領域例外的基底類別；CLI 選單與檔案載入邊界可用 `except ScheduleError` 統一攔截。 |
| `ValidationError(ScheduleError)` | `__init__(errors: str \| Sequence[str])`<br>`.errors: list[str]` | 欄位或格式驗證失敗時拋出。單一字串或序列皆正規化為非空 `list[str]`（空輸入預設 `["驗證失敗"]`），`str(exc)` 以 `"; "` 串接全部錯誤。 |
| `NotFoundError(ScheduleError)` | — | 依 ID 查詢或操作目標不存在時拋出。 |
| `DuplicateIdError(ScheduleError)` | — | 新增資料遇到重複主鍵 ID 時拋出。 |

> **使用原則**：操作無法完成（格式錯誤、找不到對象、ID 重複）才 `raise` 例外；一般業務查詢結果（例如衝堂檢查清單）應正常回傳資料或空清單。

### `constants.py`

| 常數 | 型別與值 | 說明 |
| :--- | :--- | :--- |
| `DAYS` | `"1234567"` | 合法星期字元（星期一～日）。 |
| `PERIODS` | `"123456789abc"` | 合法節次順序（共 12 節）。 |
| `COURSE_CATEGORIES` | `("必修", "選修")` | 課程 `category` 允許值。 |
| `PERIOD_TIMES` | `dict[str, tuple[time, time]]` | 節次對應時間區間：`"1"` 為 `08:10–09:00`，每節間隔一小時、時長 50 分鐘，至 `"c"` 為 `19:10–20:00`。 |

### `loader.py`

- **`@dataclass class SeedData`**
  - 欄位：`courses: dict[str, Course]`、`students: dict[str, Student]`、`classrooms: dict[str, Classroom]`、`activities: dict[str, Activity]`。
- **`load_seed_data() -> tuple[SeedData, list[str]]`**
  - 透過 `importlib.resources` 讀取 `src/datamodel/seed/` 下的 `courses.json`、`students.json`、`classrooms.json`、`activities.json`。
  - **每次呼叫回傳全新獨立副本**，不共享狀態。
  - **單筆容錯**：逐筆驗證並組裝集合；遇到缺檔（`OSError`）、UTF-8 解碼失敗、JSON 損毀、頂層非陣列、單筆 `ValidationError` 或重複 ID（保留第一筆合法紀錄）時略過異常項目，將原因記錄至 `warnings` 而不中斷程式。
  - **不執行跨表檢查**：僅驗證單筆欄位合法性，不檢查課程教室或學生已選課號是否存在。

### `course.py`

**`@dataclass class Course`**

| 欄位 | 型別 | 驗證規則 |
| :--- | :--- | :--- |
| `code` | `str` | 去掉前後空白後非空字串（主鍵）。 |
| `name` | `str` | 去掉前後空白後非空字串。 |
| `credits` | `int` | 非 `bool` 整數，`>= 1`。 |
| `category` | `str` | 須屬於 `COURSE_CATEGORIES`（`"必修"` 或 `"選修"`）。 |
| `teacher` | `str` | 去掉前後空白後非空字串。 |
| `capacity` | `int` | 非 `bool` 整數，`>= 1`。 |
| `enrolled` | `int` | 非 `bool` 整數，`>= 0`（**不**檢查 `enrolled <= capacity`，保留給 F1/F2 檢核）。 |
| `room` | `str` | 去掉前後空白後非空字串。 |
| `slots` | `list[str]` | 非空 `list`、無重複值；每筆須為長度 3 且符合 `"<day>-<period>"`（`DAYS` 與 `PERIODS`）。 |

- **`Course.from_dict(data: Mapping[str, Any]) -> Course`**：一次檢查缺欄與欄位值錯誤並拋出 `ValidationError`；會複製 `slots` 清單。
- **`course.to_dict() -> dict[str, Any]`**：回傳可直接 JSON 序列化的 `dict`（含複製後的 `slots`）。

### `student.py`

**`@dataclass class Student`**

| 欄位 | 型別 | 驗證規則 |
| :--- | :--- | :--- |
| `student_id` | `str` | 去掉前後空白後非空字串（主鍵，不限定字元前綴）。 |
| `name` | `str` | 去掉前後空白後非空字串。 |
| `department` | `str` | 去掉前後空白後非空字串。 |
| `credit_limit` | `int` | 非 `bool` 整數，`>= 1`。 |
| `enrolled_courses` | `list[str]` | `list`（允許 `[]`），元素皆為非空字串且不重複。 |
| `enrolled_activities` | `list[str]` | `list`（允許 `[]`），元素皆為非空字串且不重複。 |

> 學生不再保存二維課表矩陣，個人課表由 F3 依上述兩組代號清單動態產生。

- **`Student.from_dict(data: Mapping[str, Any]) -> Student`**：一次回報缺欄與無效欄位錯誤，防禦性複製兩個清單。
- **`student.to_dict() -> dict[str, Any]`**：回傳含複製清單的 JSON 相容 `dict`。

### `classroom.py`

**`@dataclass class Classroom`**

| 欄位 | 型別 | 驗證規則 |
| :--- | :--- | :--- |
| `room_id` | `str` | 去掉前後空白後非空字串（主鍵）。 |
| `capacity` | `int` | 非 `bool` 整數，`>= 1`。 |
| `equipment` | `list[str]` | `list`（允許 `[]`），元素皆為非空字串且不重複。 |

- **`Classroom.from_dict(data: Mapping[str, Any]) -> Classroom`**：一次回報缺欄與無效欄位錯誤，防禦性複製 `equipment`。
- **`classroom.to_dict() -> dict[str, Any]`**：回傳含複製 `equipment` 的 JSON 相容 `dict`。
- *待擴充（Issue [#6](https://github.com/wayne0208/Programming-Repository/issues/6)）*：F9 所需的教室所屬建築物欄位或代碼推算規則尚未實作。

### `activity.py`

**`@dataclass class Activity`**

| 欄位 | 型別 | 驗證規則 |
| :--- | :--- | :--- |
| `activity_id` | `str` | 去掉前後空白後非空字串（主鍵）。 |
| `name` | `str` | 去掉前後空白後非空字串。 |
| `date` | `datetime.date` | 須為 `date` 且**不可為 `datetime`**。 |
| `start_time` | `datetime.time` | 不含時區的 `time`（`tzinfo is None`）。 |
| `end_time` | `datetime.time` | 不含時區的 `time`，且必須 `end_time > start_time`（不允許跨日）。 |
| `category` | `str` | 去掉前後空白後非空字串。 |
| `capacity` | `int` | 非 `bool` 整數，`>= 1`。 |
| `registered` | `int` | 非 `bool` 整數，`>= 0`（**不**檢查 `registered <= capacity`，保留給 F4 檢核；既有模擬資料含初始超額情境）。 |
| `required_equipment` | `list[str]` | `list`（允許 `[]`），元素皆為非空字串且不重複。 |
| `room` | `str \| None` | `None`（尚未配置教室）或去掉前後空白後非空字串。 |

- **`activity.slots -> list[str]`（唯讀屬性）**：
  - 依 `date.isoweekday()` 取得星期幾，並按 `PERIODS` 順序檢查 `PERIOD_TIMES` 開區間重疊（`max(start_time, p_start) < min(end_time, p_end)`）。
  - 端點剛好相接（如 `09:00` 結束與 `09:10` 開始）不算重疊；完全落在課間休息回傳 `[]`。
  - **僅用於「活動 vs. 課程」比對**；「活動 vs. 活動」請直接比較 `date`、`start_time`、`end_time`。
- **`Activity.from_dict(data: Mapping[str, Any]) -> Activity`**：`date` 須為 `"YYYY-MM-DD"` ISO 字串，`start_time` / `end_time` 須為 `"HH:MM"` 或 `"HH:MM:SS"` ISO 字串；一次回報缺欄、解析與欄位錯誤，並複製 `required_equipment`。
- **`activity.to_dict() -> dict[str, Any]`**：將 `date`、`start_time`、`end_time` 透過 `.isoformat()` 轉回字串並複製 `required_equipment`。
- *待擴充（Issue [#6](https://github.com/wayne0208/Programming-Repository/issues/6)）*：F4「活動取消」若採保留紀錄並標記狀態而非直接移除，需於此處補上狀態欄位。

---

## 額外注意

### 模擬資料有問題很正常

原本的`model.py`有一些邏輯錯誤的地方：

- courses.json 裡 CS003（國文）的教室是 "06306"，但 classrooms.json 的 5 間教室沒有 "06306"（原 model.py 本來就寫成 "06306"，應是 "06302" 筆誤）。之後 F1/F4 若做「教室是否存在」檢查會先撞到這筆。
- activities.json 全部 10 筆活動目前都是 registered > capacity（依先前決定照原 model.py 保留）。資料結構與載入都正常，但之後跑 F4「活動報名人數不得超過上限」（SPEC.md L87）與正常報名測試時，這 10 筆預設都是超額狀態，屆時 F4 負責人可視測試需要再調數字或對調。

因為不是我寫的我不確定是筆誤還是刻意設計，故轉成json檔後還是保留的
