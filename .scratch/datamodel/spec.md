# Datamodel 基礎資料型別與儲存介面規格

## Problem Statement

現有系統將課程、學生、活動與教室資料以無欄位名稱的巢狀 `list` 存放於頂層全域變數中，並由各功能模組直接存取跨模組全域狀態與固定位置索引（magic index）。此設計同時引發多項問題：

1. **違反架構與 CI 規範**：透過頂層可變全域變數傳遞系統資料，直接違反專案規範「不得使用全域變數傳遞系統資料」以及自動化防護檢查（guardrails）。
2. **跨模組資料契約不一致導致執行期錯誤**：不同模組對學生課表欄位（二維陣列物件、模組變數名稱字串、或一維代碼清單）與活動時段欄位（字串與清單混用）各有不同假設，執行時會引發 `TypeError` 或 `UnboundLocalError`。
3. **共用可變參考造成資料污染**：多位學生共用同一份二維課表物件參考，修改單一學生資料會意外影響其他學生。
4. **缺乏欄位驗證與容錯載入機制**：不合法的資料可被直接寫入狀態，且載入過程缺乏統一的錯誤模型與單筆容錯機制，容易導致程式崩潰。

## Solution

建立獨立的 `datamodel` 基礎資料套件，以標準化、無全域狀態的資料模型作為整個選課與課表規劃系統（F1～F10）的共同介面：

1. **具自我驗證能力的強型別實體**：將課程（`Course`）、學生（`Student`）、教室（`Classroom`）與活動（`Activity`）封裝為 `@dataclass` 類別，在建構時一次收集所有欄位錯誤並拋出統一的 `ValidationError`，同時提供 `from_dict()` 與 `to_dict()` 序列化介面。
2. **單一真相來源與標準時間模型**：學生僅保存各自獨立的一維已選課程與活動代號清單，不再內嵌二維課表矩陣；所有實體 ID 統一為非空字串 `str`；活動直接採用標準庫 `datetime.date` 與 `datetime.time` 表示時間，並透過唯讀 `.slots` 屬性自動換算覆蓋節次供「活動 vs. 課程」比對，而「活動 vs. 活動」則直接使用 `date`、`start_time` 與 `end_time` 屬性比較。
3. **統一例外階層與邊界捕捉**：定義 `ScheduleError` 為基底的例外階層（`ValidationError`、`NotFoundError`、`DuplicateIdError`），讓核心資料驗證失敗時能帶出完整錯誤清單，並交由 CLI 或檔案載入邊界統一捕捉處理。
4. **套件內建 JSON 模擬資料與容錯載入**：將模擬資料以每種實體一個 JSON 檔案的形式隨套件封裝，透過 `load_seed_data()` 讀取並轉換為 `SeedData`（各實體為以字串 ID 為鍵的 `dict[str, Entity]`）；遇到單筆格式錯誤或重複 ID 時略過並記錄警告訊息，確保系統不會因單筆異常資料而終止。
5. **漸進式遷移**：在 `datamodel` 建置完成並接軌各模組前，暫時保留舊版全域資料模組，避免在遷移過渡期中斷既有程式。

## User Stories

1. As a F1～F10 功能模組開發者, I want 透過 `from datamodel import ...` 匯入所有資料類別、常數、例外、`SeedData` 與載入函式, so that 核心模組不會透過模組屬性存取跨模組資料而觸發靜態架構檢查違規。
2. As a F1～F10 功能模組開發者, I want 在記憶體中使用以字串 ID 為鍵的 `dict[str, Entity]` 存放課程、學生、教室與活動, so that 單筆查詢可達 $O(1)$ 複雜度且鍵值本身自然保證代號唯一性。
3. As a F1～F10 功能模組開發者, I want 核心函式只接收自己需要的資料集合參數，並在一般 CRUD／加退選操作全數驗證通過後才就地更新（搜尋與模擬則僅回傳新結果）, so that 各模組耦合度低且驗證失敗時不會破壞既有資料狀態。
4. As a F1～F10 功能模組開發者, I want 所有實體 ID（`code`、`student_id`、`room_id`、`activity_id`）統一採用非空字串 `str`, so that 系統能同時相容現有七位數字學號（如 `"1150101"`）與規格書中的字串學號（如 `"S001"`）。
5. As a 課程管理開發者（F1）, I want 透過 `Course` 資料類別建立課程並自動驗證代號、名稱、學分、必選修類別、教師、人數上限、已選人數、教室與上課時段, so that 不合法的課程物件在建構當下即被攔截。
6. As a 課程管理開發者（F1）, I want `Course` 在驗證時段清單時檢查每個時段是否符合 `"<星期>-<節次>"` 格式且無重複時段與空清單, so that 非法星期、非法節次或格式錯誤的字串不會流入後續衝堂計算。
7. As a 課程管理開發者（F1）, I want `Course` 的必選修欄位以領域常數 `COURSE_CATEGORIES`（`"必修"`、`"選修"`）驗證, so that 課程類別字串能保持一致且避免錯字。
8. As a 學生管理與選課開發者（F1、F2）, I want `Student` 僅保存各自獨立的 `enrolled_courses: list[str]` 與 `enrolled_activities: list[str]` 一維清單, so that 學生課表不再成為重複儲存源且不同學生之間不會因共用物件參考而互相污染。
9. As a 課表產生開發者（F3）, I want 直接依據 `Student.enrolled_courses` 與 `Student.enrolled_activities` 動態組合每週 `7×12` 二維課表, so that 課表呈現永遠與學生最新選課及活動狀態保持一致。
10. As a 活動與教室管理開發者（F4）, I want `Classroom` 包含 `room_id`、`capacity` 與 `equipment: list[str]` 欄位, so that 教室配置能依容量與設備需求進行篩選，且保留後續擴充空間。
11. As a 活動管理開發者（F4）, I want `Activity` 直接使用 `datetime.date`、`datetime.time` 保存日期與起訖時間，並包含非空字串 `category`、`capacity`、`registered`、`required_equipment` 與可為 `None` 的 `room`, so that 活動的日期先後與時間範圍能使用標準日期時間介面安全運算。
12. As a 活動與衝堂檢查開發者（F2、F4）, I want 在比對「活動 vs. 課程」時透過 `Activity.slots` 與 `Course.slots`（`list[str]` 的 `"<星期>-<節次>"`）進行節次比對, so that 活動與每週固定課程能共用同一套節次衝堂表示法。
13. As a 活動與衝堂檢查開發者（F2、F4）, I want 在比對「活動 vs. 活動」時直接使用 `Activity` 的 `date`、`start_time` 與 `end_time` 屬性比對（同日期且時間區間重疊），而不透過 `.slots`, so that 不同日期但同星期的活動不會被誤判衝突，且同日課間活動也能正確檢出衝突。
14. As a 活動時段推算使用者（F2、F4）, I want `Activity.slots` 嚴格以「開區間重疊（端點相接不算重疊）」比對 `PERIOD_TIMES` 節次時間表，且落在下課時間的活動回傳空清單 `[]`, so that 如 `09:00` 結束的活動不會誤判占用到 `09:10` 開始的下一節課，也不會阻礙下課時間活動的建立。
15. As a 系統開發者, I want 在實體建構失敗時於 `__post_init__` 一次檢查所有欄位並將全部錯誤彙整至 `ValidationError.errors`, so that 呼叫端與使用者能一次看見所有不合規的欄位而非逐一修正。
16. As a 系統開發者, I want 實體本身僅驗證「單筆欄位格式與型別不變量」，而不將跨實體參照或「已選／已報名人數 ≤ 容量上限」寫死在建構子中, so that 既有的超額模擬活動資料能成功載入系統，並將業務規則留給 F1～F4 各自把關。
17. As a 錯誤處理開發者, I want 使用統一的例外階層（`ScheduleError` 及其子類 `ValidationError`、`NotFoundError`、`DuplicateIdError`）, so that 操作失敗能透過標準 Python 例外向上傳遞並在 CLI 或資料載入邊界集中捕捉。
18. As a 衝堂檢查開發者（F2）, I want 區分「操作異常例外」與「業務查詢結果（如衝堂清單）」, so that 衝堂判斷函式可正常回傳衝突清單（空清單代表無衝突），不濫用例外控制一般邏輯流程。
19. As a F6 資料持久化開發者, I want 每個實體都提供 `to_dict()` 與 `from_dict()` 方法，並能自動完成 `datetime.date` / `datetime.time` 與 ISO 8601 字串的雙向轉換, so that JSON 序列化的讀寫邏輯集中在各實體自身而不外洩至業務模組。
20. As a F6 資料持久化開發者, I want `from_dict()` 在遇到缺漏欄位、型別不符或非法 ISO 日期時間字串時拋出一致的 `ValidationError`, so that 檔案載入層可以用單一的錯誤處理分支攔截各種損毀紀錄。
21. As a 系統整合者（`main.py`）與測試工程師, I want 呼叫 `load_seed_data()` 一次載入四類內建模擬資料並取得具明確欄位型別的 `SeedData` 獨立複本, so that 不同測試案例或選單工作階段之間不會互相污染初始資料狀態。
22. As a 資料載入邊界開發者, I want `load_seed_data()` 逐筆驗證讀取到的紀錄，在遭遇單筆格式錯誤或重複 ID 時略過該筆並附加說明至回傳的 `warnings` 清單，而不是中斷整個程式, so that 系統符合「單筆資料格式錯誤不得導致程式異常終止」的規格要求。
23. As a 系統開發者, I want 所有時間與領域常數（`DAYS`、`PERIODS`、`PERIOD_TIMES`、`COURSE_CATEGORIES`）集中定義於同一處並以全大寫命名, so that 節次對應時間與星期範圍在全系統維持單一定義且符合 CI 常數命名規範。
24. As a 測試工程師, I want 將模擬資料以每種實體一個 JSON 陣列檔案封裝於套件內部並透過 `importlib.resources` 載入, so that 套件打包與獨立測試在任何工作目錄下都能穩定讀取模擬資料。
25. As a 模擬資料維護者, I want 保留既有模擬資料的課程數量（20 門）、學生數量（15 名）、教室數量（5 間）與活動數量（10 項），並為教室補齊合理設備清單及為活動補齊類型與場地設備需求, so that 期中與後續功能模組可直接利用完整的模擬場景進行驗證。
26. As a 模擬資料維護者, I want 舊模擬活動的日期沿用原月／日並加上 `2026-` 前綴、起訖時間由原節次推算、且保留原人數數值作為 `registered` 與 `capacity`, so that 轉換後的資料忠實反映既有資料內容並可測試活動額滿場景。
27. As a 系統維護者, I want 在建置 `datamodel` 期間保留既有的全域資料模組不刪除, so that 尚未遷移的現有程式與測試仍能維持原本運作直到逐模組切換完成。

## Implementation Decisions

### 1. Package 公開匯出介面、模組切分與匯入契約

- 建立 `datamodel` 套件作為系統基礎資料層，套件內依職責切分模組：四個實體類別各自存放於獨立模組（**一個實體類別一個檔案**），另有常數模組、例外模組與載入模組；套件內部彼此引用常數或例外時一律使用**相對匯入**（例如 `from .errors import ...`、`from .constants import ...`）。
- 套件根層定義 `__all__`，統一對外匯出：
  - 四個實體類別：`Course`、`Student`、`Classroom`、`Activity`
  - 領域常數：`DAYS`、`PERIODS`、`PERIOD_TIMES`、`COURSE_CATEGORIES`
  - 例外階層：`ScheduleError`、`ValidationError`、`NotFoundError`、`DuplicateIdError`
  - 模擬資料載入介面：`SeedData`、`load_seed_data`
- **強制外部匯入方式**：套件外部所有模組一律透過 `from datamodel import ...` 直接匯入所需符號；禁止寫成 `import datamodel` 後於核心函式內以 `datamodel.Course` 存取屬性，以滿足專案 AST 防護測試對跨模組全域存取的檢查規則。

### 2. 領域常數契約

- `DAYS: str = "1234567"`（代表星期一至星期日）
- `PERIODS: str = "123456789abc"`（依序代表第 1～9、a、b、c 共 12 節）
- `COURSE_CATEGORIES: tuple[str, ...] = ("必修", "選修")`
- `PERIOD_TIMES: dict[str, tuple[datetime.time, datetime.time]]`：將 `PERIODS` 中的 12 個節次依序對應至每日 08:10 起每小時一節、每節 50 分鐘的時段區間：
  - `"1"`：`08:10`–`09:00`、`"2"`：`09:10`–`10:00`、`"3"`：`10:10`–`11:00`、`"4"`：`11:10`–`12:00`
  - `"5"`：`12:10`–`13:00`、`"6"`：`13:10`–`14:00`、`"7"`：`14:10`–`15:00`、`"8"`：`15:10`–`16:00`
  - `"9"`：`16:10`–`17:00`、`"a"`：`17:10`–`18:00`、`"b"`：`18:10`–`19:00`、`"c"`：`19:10`–`20:00`

### 3. 例外階層契約

- `ScheduleError(Exception)`：所有排課領域例外的共同基底類別。
- `ValidationError(ScheduleError)`：攜帶 `errors: list[str]` 屬性（當傳入單一字串或錯誤清單時皆正規化為非空 `list[str]`），同時以可讀摘要組合訊息作為例外描述，用於一次回報全部欄位驗證錯誤。
- `NotFoundError(ScheduleError)`：查詢不到指定實體時使用。
- `DuplicateIdError(ScheduleError)`：新增資料遇到重複主鍵 ID 時使用。
- CLI 互動邊界與檔案載入邊界負責捕捉 `ScheduleError` 及其子類別；業務判斷函式（如衝堂列表查詢）則透過正常回傳值回傳空清單或結果集合。

### 4. 實體資料模型與類別介面（原型契約形狀）

四個實體採用 `@dataclass` 實作，每個類別各自獨立定義於專屬模組中且互不匯入，只以字串 ID 參照彼此；以下為決議後的介面契約形狀：

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

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Course: ...
    def to_dict(self) -> dict[str, Any]: ...
```

```python
@dataclass
class Student:
    student_id: str
    name: str
    department: str
    credit_limit: int
    enrolled_courses: list[str]
    enrolled_activities: list[str]

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Student: ...
    def to_dict(self) -> dict[str, Any]: ...
```

```python
@dataclass
class Classroom:
    room_id: str
    capacity: int
    equipment: list[str]

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Classroom: ...
    def to_dict(self) -> dict[str, Any]: ...
```

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

    @property
    def slots(self) -> list[str]: ...

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Activity: ...
    def to_dict(self) -> dict[str, Any]: ...
```

### 5. 欄位驗證與序列化規則

- **多錯誤收集**：每個類別的 `__post_init__` 必須檢查完所有欄位規則並將違規訊息收集於 `errors: list[str]`，只要清單非空即拋出 `ValidationError(errors)`，不得於第一個錯誤就提前中止。
- **共通規則**：
  - 識別碼、名稱與類型欄位（`code`、`name`、`student_id`、`department`、`room_id`、`activity_id`、`teacher`、`category`，以及 `room` 當非 `None` 時）須為去掉前後空白後非空的 `str`；不強制限制課程代號或學號的前綴格式。
  - 所有 `list[str]` 欄位（`slots`、`enrolled_courses`、`enrolled_activities`、`equipment`、`required_equipment`）須為 `list`，元素皆為去掉前後空白後非空的字串，且清單內不得包含重複元素。
  - 整數驗證須明確排除 `bool`（因 Python 中 `isinstance(True, int)` 為 `True`）。
- **各實體專屬欄位不變量**：
  - `Course`：`credits` 為正整數（`> 0`）；`capacity >= 1`；`enrolled >= 0`；`category` 須屬於 `COURSE_CATEGORIES`；`slots` 不可為空清單，且每個時段字串長度須為 3、格式符合 `"<day>-<period>"`（`slot[0] in DAYS`、`slot[1] == "-"`、`slot[2] in PERIODS`）。
  - `Student`：`credit_limit` 為正整數（`> 0`）。
  - `Classroom`：`capacity >= 1`。
  - `Activity`：`date` 須為 `datetime.date`（排除 `datetime.datetime` 或非日期型別）；`start_time` 與 `end_time` 須為 `datetime.time` 且 `end_time > start_time`（隱含禁止跨日）；`capacity >= 1`；`registered >= 0`；`category` 須為非空字串（同共通規則）；`room` 允許 `None` 或非空字串。
- **刻意排除於建構子之外的規則**：`Course.enrolled <= Course.capacity`、`Activity.registered <= Activity.capacity` 與跨實體參照完整性（如教室是否存在、已選課程代碼是否存在），皆由 F1～F4 業務函式檢查，不在實體 `__post_init__` 強制限制。
- **`from_dict()` / `to_dict()` 契約**：
  - `from_dict()` 檢查輸入是否為 `Mapping`、是否缺少必要欄位、以及欄位值型別與 ISO 8601 格式（`date.fromisoformat()`、`time.fromisoformat()`）是否正確；任一解析失敗或欄位檢核失敗一律拋出 `ValidationError`。
  - `from_dict()` 應複製傳入的清單欄位，避免外部保留的 `list` 參考影響物件內部狀態。
  - `to_dict()` 回傳可直接由標準 `json` 模組序列化的 `dict`（將 `Activity.date`、`start_time`、`end_time` 轉為 `.isoformat()` 字串），且需複製內部 `list` 欄位。

### 6. `Activity.slots` 時段推算與時間比較屬性區分

- **`Activity.slots` 推算規則**：
  - 由 `self.date.isoweekday()` 取得星期幾（`1`～`7`，轉為字串 `day`）。
  - 依 `PERIODS` 順序逐一比對 `PERIOD_TIMES[period]` 的 `(p_start, p_end)`：
    - 若 `max(self.start_time, p_start) < min(self.end_time, p_end)` 成立，即視為重疊，產生 `f"{day}-{period}"` 加入結果清單。
    - 端點剛好相接（例如活動於 `09:00` 結束或於 `09:10` 開始）不視為重疊。
    - 若活動完全落在課間休息時段而未與任何節次重疊，`slots` 回傳空清單 `[]`。
- **時間比較屬性區分**：
  - **活動對課程（Activity vs. Course）**：課程為每週固定星期幾與節次的常態性排程（無特定日期），比對時統一使用 `Activity.slots` 與 `Course.slots`（兩者皆為 `list[str]` 的 `"<星期>-<節次>"`）檢查節次重疊。
  - **活動對活動（Activity vs. Activity）**：活動為具特定日期的單次事件，比對時直接使用 `Activity.date`、`Activity.start_time` 與 `Activity.end_time` 屬性判斷（`a.date == b.date` 且 `max(a.start_time, b.start_time) < min(a.end_time, b.end_time)`），**不**透過 `.slots` 比對。

### 7. 記憶體集合、跨模組傳遞原則與 `load_seed_data()` 契約

- **跨模組參數傳遞粒度**：各功能模組的核心函式只接收該函式實際需要的資料集合參數（例如 `courses`、`students`），不傳遞整包系統狀態，亦不得透過全域變數存取系統資料。
- **資料異動策略**：一般 CRUD 與加退選操作須在所有驗證全數通過後才就地更新（in-place update）傳入的資料集合，若驗證失敗則保證原集合完全不變；搜尋與動態事件模擬（F7、F8、F10）則不得修改傳入的原集合，一律在資料副本上操作並回傳新結果。
- **檔案儲存格式**：四類模擬資料以四個獨立的 JSON 檔案封裝於 `datamodel` 套件內，每個 JSON 檔案的頂層結構皆為紀錄物件的陣列（`list[dict]`），由 `importlib.resources` 讀取，確保套件打包後與任何執行路徑皆可存取。
- **`load_seed_data()` 契約（原型契約形狀）**：每次呼叫皆建立並回傳全新資料結構（不共享全域狀態），簽章固定回傳 `(SeedData, list[str])`：

```python
@dataclass
class SeedData:
    courses: dict[str, Course]
    students: dict[str, Student]
    classrooms: dict[str, Classroom]
    activities: dict[str, Activity]

def load_seed_data() -> tuple[SeedData, list[str]]: ...
```

- **單筆容錯與重複 ID 處理**：逐筆解析 JSON 紀錄並呼叫對應實體的 `from_dict()`；若檔案缺失、JSON 損毀、單筆格式／驗證失敗（捕獲 `ValidationError`）、或出現重複 ID，則略過該筆（不覆蓋已存在紀錄）並將清楚說明來源與原因的訊息加入 `warnings`，保證程式不因異常資料而崩潰。
- **舊模擬資料轉換規則**：
  - 所有實體 ID 轉為字串（例如學號 `1150101` 轉為 `"1150101"`）。
  - 學生原本的 `7×12` 二維課表矩陣攤平並依出現順序去重，課程代碼（如 `"CS..."`）放入 `enrolled_courses`，活動代碼（如 `"A06"`）放入 `enrolled_activities`，確保 15 名學生各自擁有獨立清單。
  - 活動日期保留原本月／日並冠上 `2026-`（`YYYY-MM-DD`）；`start_time` 與 `end_time` 依原模擬資料之起迄節次對應 `PERIOD_TIMES` 首節開始時間與末節結束時間；原本第 5 欄保留為 `registered`、第 6 欄保留為 `capacity`。
  - 教室 `equipment` 與活動 `category`、`required_equipment` 於模擬資料中補齊合理的示範值。

## Testing Decisions

- **什麼是好的測試**：所有測試僅透過 `datamodel` 套件對外匯出的公開介面（外部可觀察行為、建構結果、回傳字典與 `SeedData`、唯讀 `.slots` 輸出、`ValidationError.errors` 內容與警告清單）進行驗證，不耦合或斷言任何私有輔助函式或內部實作細節。
- **單一測試接縫（Testing Seam）**：整個功能以 `datamodel` 套件根層的公開匯出介面作為唯一測試接縫：
  - 實體建構與序列化：`Course`、`Student`、`Classroom`、`Activity`（含 `.from_dict()`、`.to_dict()` 與 `Activity.slots`）
  - 模擬資料載入：`SeedData`、`load_seed_data()`
  - 公開常數與例外型別：`DAYS`、`PERIODS`、`PERIOD_TIMES`、`COURSE_CATEGORIES`、`ScheduleError`、`ValidationError`、`NotFoundError`、`DuplicateIdError`
- **待測試範圍**：
  - 四個實體的正常建構、完整 `from_dict()` / `to_dict()` 往返一致性（round-trip），以及單次建構同時觸發多個欄位錯誤時 `ValidationError.errors` 能否完整回報所有錯誤。
  - 邊界案例：非 `bool` 整數檢查、空字串 `category`、空清單與重複元素檢查、非法時段格式（長度不足、分隔符錯誤、星期或節次越界）、非法 ISO 日期時間格式、`end_time <= start_time` 與不可變複製保護（傳入或回傳之 list 修改不影響內部資料）。
  - `Activity.slots` 計算：單節、跨多節、部分重疊、端點相接不重疊（例如 `09:00` 結束與 `09:10` 開始）以及完全落在下課時間回傳 `[]`。
  - `load_seed_data()` 行為：預設模擬資料可無警告載入 20 門課程、15 名學生、5 間教室與 10 項活動，且每次呼叫回傳彼此獨立的 `SeedData` 副本；模擬單筆缺欄／壞格式紀錄、重複 ID 紀錄或損毀 JSON 時，能略過異常筆數、保留合法資料並產出明確 `warnings`。
  - 通用架構防護測試（`tests/common/test_spec_guardrails.py`）：確認套件符合無可變全域變數、無頂層或核心函式 `input()` 呼叫、安全匯入與例外處理等自動化 CI 門檻。
- **開發方式與測試位置**：採用 TDD（`Requirement → Test / Red → Green → Refactor → Regression Test`）流程開發，所有 `datamodel` 相關測試案例統一放置於 `./tests/datamodel/` 目錄下（平行開發各實體時依模組分檔，整合階段統一透過套件根層公開介面驗證）。
- **既有測試參考（Prior Art）**：沿用專案現有的 `pytest` 架構與風格，比照 `tests/common/test_spec_guardrails.py` 的參數化與靜態防護標準，並以純函式／純資料介面單元測試取代舊版依賴 `builtins.input` mock 與全域狀態的測試風格。

## Out of Scope

- **舊版程式之刪除或重構**：保留既有的全域資料模組與現有 F1、F2、F3 功能模組及既有舊版測試不予修改或刪除，待後續各模組遷移計畫分階段切換。
- **F1～F10 功能函式簽章與業務邏輯**：包含 CRUD 函式介面、選課衝堂檢查（含 F2 / F4 中「活動 vs. 活動」與「活動 vs. 課程」的比對函式實作）、加退選對 `enrolled` / `registered` 的同步與上限檢核、跨實體參照完整性檢查、動態課表矩陣產生、教室配置邏輯、F6 使用者自訂匯出／匯入路徑及 CLI 選單整合。
- **F9 校園建築物欄位擴充**：`Classroom` 所屬校園建築物節點欄位或對應規則待進入 F9 規劃時再行擴充。

## Further Notes

- 後續擴充追蹤：F2～F10 未來可能新增或調整之資料模型待辦已整併於 GitHub Issue [#6](https://github.com/wayne0208/Programming-Repository/issues/6)（`[datamodel] 未來擴充待辦（F2～F10）`，標籤 `needs-triage`）。
