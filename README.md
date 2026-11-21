# Programming-Repository

Group 13: 蘇郁文、李旻頵、張冠鋐、蕭狀元、王界誠、朱紹來

作業快速連結：

- [團體作業要求規範](https://drive.google.com/file/d/1K0ZnRXzKH5roizgErwqOIfmzztW7cCAf/view)
- [系統設計需求規格書範例](https://drive.google.com/file/d/1_v00OjG6b8xjsW-s7X_ke3Ybd0fP_Vs3/view)

---

## 自動化 CI 與開發規範

簡單講只需要每次Push/PR後看一次報告就知道過沒過，沒過基本上就是不符合作業規範或有錯誤
然後作業規範有以下要求，寫之前可以確認一下：

- 採用 TDD 開發（F7開始）
- 不能用全域變數
- 不能使用`input()`
- 錯誤捕捉

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

## 簡易教學

### 科學上網

若在與Github的連線上感覺到卡頓、網速變慢的現象，可以使用科學上網解決，例如Cloudflare WARP：  
`winget install -e --id Cloudflare.Warp`

### 環境

預設是在Windows環境，所有指令皆在PowerShell執行

在特定位置使用的操作，可以在檔案總管開啟對應資料夾後，右鍵點選`在終端中開啟`  
，或者複製位置後在終端中輸入`cd`，接者貼上複製下來的位置

1. **VSCode**

    推薦使用VSCode作為IDE配合插件使用，安裝VSCode指令如下：  
    `winget install -e --id Microsoft.VisualStudioCode`  

    然後是插件部分，這裡推薦安裝以下插件：  
    - **Chinese (Traditional) Language Pack for Visual Studio Code**：漢化用
    - **Python**：幫忙寫Python，會連帶其他插件一起安裝
    - **Ruff**：協助維持統一的python寫法
    - **Markdown PDF**：一鍵將markdown檔案轉換成pdf
    - **markdownlint**：協助維持標準的markdown格式
    - **Mermaid Preview**：協助畫/預覽mermaid語法的流程圖
    - **vscode-pdf**：在vscode內部預覽pdf檔案
    - **Material Icon Theme**：美化圖示

    以下是安裝以上所有插件的指令，請完整複製：  

    ```powershell
    code --install-extension MS-CEINTL.vscode-language-pack-zh-hant --install-extension ms-python.python --install-extension charliermarsh.ruff --install-extension yzane.markdown-pdf --install-extension DavidAnson.vscode-markdownlint --install-extension PKief.material-icon-theme --install-extension vstirbu.vscode-mermaid-preview --install-extension tomoki1207.pdf
    ```  

    也可以手動在VSCode的GUI介面安裝

2. **Scoop（可選項）**

    一款簡潔的CLI軟體管理器，主要特色為不污染環境變數，也是我推薦的原因，以下是安裝指令：  
    `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force; irm get.scoop.it | iex`

3. **Git**

    使用Scoop安裝，若已經安裝過Git可以跳過此行命令：  
    `scoop install git`  
    若沒安裝Scoop，用以下指令代替：  
    `winget install -e --id Git.Git`

    然後是設定檔，請依照自身狀況輸入以下指令：  
    `git config --global user.name "你的英文暱稱"`  
    `git config --global user.email "你的電子郵件@example.com"`

    接者輸入以下指令，避免一些跨平台的換行問題：  
    `git config --global core.autocrlf true`

    在想放本專案的位置使用以下指令進行抓取，實際連結依網頁最新為準：  
    `git clone https://github.com/wayne0208/Programming-Repository.git`  
    Git的操作部分後續會提到

4. **Python**

    uv是一款高效的Python套件管理工具，使用uv來保證每人開發環境的一致  
    先使用Scoop安裝uv，使用以下指令：  
    `scoop install uv`  
    若沒安裝Scoop，用以下指令代替：  
    `winget install -e --id astral-sh.uv`

    接者在專案內部進行，使用以下指令後uv會自動在專案內部安裝專案對應的python版本，以及要求套件：  
    `uv sync`  
    若後續開發過程有套件缺失，再度使用該指令可解決

    記得在VSCode內選擇正確的環境作為解譯器，選擇`.venv`資料夾內的Python作為解譯器  
    按下`ctrl + shift + p`後輸入`Python: Select Interpreter`可以選擇  
    在聚焦py檔案視窗時，點選畫面右下角也可以選擇解譯器

5. **一些Git的操作**

    - 同步：開發前準備，拉取main主幹

        為了開發前保持最新版，使用以下指令拉取最新main主幹：  
        `git checkout main`  
        `git pull origin main`  
        使用完後記得建立分支再進行其他操作

    - 建立分支：避免main主幹混亂

        開發前使用以下指令建立分支，記得先同步，並依實際情況改變：  
        `git checkout -b feature/分支名`

    - 上傳前同步：確保在最新版，避免衝突

        使用以下指令把commit接在最新的main主幹後，只推薦在單人開發一個分支使用：  
        `git fetch origin`  
        `git rebase origin/main`  
        若是多人共同開發同一個分支，改用以下指令，依實際情況填寫：  
        `git pull origin feature/分支名`

    - 上傳：流程是先在本地端建立commit，等完整開發完後再push上去

        使用以下指令暫存所有變更：  
        `git add .`  
        使用以下指令將變更儲存成commit，依實際情況填寫：  
        `git commit -m "你做了什麼"`  
        使用以下指令將所有本地端的commit推送上去，依實際情況改變：  
        `git push -u origin feature/分支名`

    報錯可能是遇到conflict，手動解決後再執行下一步操作  
    以上Git的操作均可以在VSCode的GUI介面進行

### 專案架構

1. **.github**  
    存放CI/CD設定

2. **.venv**  
    執行`uv sync`後自動安裝的Python環境，不需要理會

3. **docs**  
    文檔存放區，包括作業和架構，建議將作業推上來

4. **src**  
    原始碼存放區，大部分開發都在這裡，記得照功能(Package)分開

5. **tests**  
    CI/CD流程用的自動化測試程式碼
