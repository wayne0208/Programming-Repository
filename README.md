# Programming-Repository

Group 13: 蘇郁文、李旻頵、張冠鋐、蕭狀元、王界誠、朱紹來

作業快速連結：

- [團體作業要求規範](https://drive.google.com/file/d/1K0ZnRXzKH5roizgErwqOIfmzztW7cCAf/view)
- [系統設計需求規格書範例](https://drive.google.com/file/d/1_v00OjG6b8xjsW-s7X_ke3Ybd0fP_Vs3/view)

---

## 懶人包

### 作業打包

按一下根目錄的`打包作業.bat`，照提示輸入就會產出zip檔在根目錄  
前提要求是在`.\docs\personal_work\`下有對應學號的資料夾，並在這個資料夾放你的個人作業pdf  
傳完後記得刪除zip檔

### 資料索引

- **資料格式**：☞[資料格式說明文件](./src/datamodel/README.md)

---

## 開發規範

作業要求的規範，寫之前確認一下：

- 採用 TDD 開發（F7開始），簡單講就是要撰寫測試案例
- 不能用全域變數、`input()`，要用函式傳入傳出參數
- 錯誤捕捉，核心就是多用`try...except`

---

## 自動化 CI 工作流

簡單講只需要每次Push/PR後看一次報告就知道過沒過，沒過基本上就是不符合作業規範或有錯誤

### 1. Push / PR 工作流順序

任何分支 `push` 或發起 `pull_request` 皆會自動觸發 `.github/workflows/ci.yml`，所有檢查關卡皆為**硬性門檻**（任一失敗即不通過，但仍會跑完所有步驟產出完整報告），依序執行以下，看產出的報告寫什麼就好：

1. **安裝環境**：`uv sync --all-groups`
2. **靜態分析與排版**：`ruff check .`（`E/W/F/I/N/B`）➔ `ruff format --check .`
3. **編譯與打包**：`python -m compileall -q src tests` ➔ `uv build`
4. **執行測試**：
   - **提交者功能測試**：`pytest tests --ignore=tests/common`（由各功能負責人撰寫於 `tests/test_*.py`）
   - **通用規範測試**：`pytest tests/common`
5. **產生與發佈報告**：寫入 Job Summary、上傳 Artifact，並於 PR 自動留言更新。

### 2. TDD 開發流程

作業規範要求要求第 10 週起新增核心功能須採 TDD（`Requirement → Test → Red → Green → Refactor → Regression Test`）
也就是要自己撰寫測試案例：

1. **Requirement**：確認函式輸入、輸出、邊界與錯誤處理規格（見 `docs/SPEC.md`）。
2. **Test / Red**：先在 `tests/test_<功能>.py` 撰寫測試，執行 `uv run pytest` 確認測試失敗（不可先寫完功能才補測試）。
3. **Green**：在 `src/` 完成最低限度實作使測試通過（核心函式以參數傳遞資料、不呼叫 `input()`）。
4. **Refactor**：重構並整理風格（`uv run ruff check .`、`uv run ruff format .`）。
5. **Regression Test**：執行完整 `uv run pytest` 確認所有既有測試皆通過後再提交並留下 TDD 紀錄。

### 3. 通用規範規則（`tests/common/test_spec_guardrails.py`）

CI 會自動掃描 `src/**/*.py` 並檢查以下 5 項共通規範，都是作業規範要求的：

- **禁止全域變數傳遞資料**：不可使用 `global`、模組頂層僅允許全大寫常數、核心函式不得直接存取跨模組全域資料（如 `model.course`、`getattr(model, ...)`）。
- **核心函式不得依賴 `input()`**：僅允許 `main`、`cli_*`、`*_cli`、`menu*`、`cli.py`/`main.py` 或 `if __name__ == "__main__":` 處理人工輸入。
- **模組安全匯入**：`import` 時不可執行 `input()` 阻塞或拋出未捕獲例外。
- **禁止不當吞錯**：禁止裸 `except:` 與 `except ...: pass`。
- **數值輸入保護**：`int(input(...))` / `float(input(...))` 須以 `try/except ValueError` 保護，避免輸入非數字直接崩潰。

### 4. 測試報告怎麼看

這個報告只保留30天，要放進繳交報告的話可以順手存進`.\docs\artifacts\`下

- **Push & PR 總覽**：GitHub 頁籤 **Actions ➔ 點選當次執行 ➔ Summary** 查看各關卡狀態表與展開明細。
- **PR 自動留言**：PR 頁面會自動張貼並更新同一則測試報告留言，方便 Code Review。
- **報告封存下載**：於 Actions 執行頁下方 **Artifacts** 下載 `ci-test-report-*`（含 `ci-report.md`、JUnit XML 與 Ruff 日誌，保留 30 天），可供每週作業繳交附檔。
- **狀態說明**：所有關卡若出現 `❌ 失敗（阻斷）` 皆須修正才能通過 CI；若測試出現 **`💥 非預期例外中斷`** 代表測資觸發未捕獲例外導致程式崩潰，應優先於 **`❌ 斷言失敗`** 處理。

---

## 專案架構

1. **.github**  
    存放CI/CD設定

2. **docs**  
    文檔存放區，包括作業和架構，建議將作業推上來

3. **src**  
    原始碼存放區，大部分開發都在這裡，記得照功能(Package)分開

4. **tests**  
    CI/CD流程用的自動化測試程式碼，以及自己撰寫的測試案例

5. **.xxx**
    .xxx的大多都不用理會
