# Flask 任務管理儀表板 (Task Management Dashboard)

這是一個使用 Python Flask 框架開發的現代化任務管理儀表板網頁應用程式。

## 🎯 專案特色

1. **結構切割 (Modular Structure)**：採用標準的專案分工，將核心應用程式放置在 `src/` 資料夾，並將單元測試放置在 `test/` 資料夾。
2. **現代化視覺設計 (Modern Aesthetics)**：
   - 使用深色調 (Dark Mode) 與漸層背景。
   - 採用毛玻璃擬態 (Glassmorphism) 卡片設計。
   - 豐富的滑鼠 Hover 反饋與流暢的動態微動畫（例如刪除時的向右滑出淡出）。
   - 使用輕量化的 Lucide Icons 向量圖示。
3. **RESTful API**：後端採用 Flask 提供標準的 CRUD 任務操作 API，前端則透過 Fetch API 進行非同步無刷新的資料更新與統計數據計算。
4. **部屬設定**：預設部屬並運行於 **Port 19191**。

---

## 🛠️ 目錄結構說明

```text
MyProject/
├── src/                     # 應用程式主程式碼
│   ├── __init__.py          # 套件初始化
│   ├── app.py               # Flask 核心程式與 API 端點定義
│   ├── templates/           # HTML 網頁範本
│   │   └── index.html
│   └── static/              # 靜態資源
│       ├── css/
│       │   └── style.css    # 現代化 CSS 樣式與動畫
│       └── js/
│           └── app.js       # 前端 API 串接與 DOM 操作
├── test/                    # 測試程式碼
│   ├── __init__.py          # 測試套件初始化
│   └── test_app.py          # pytest 測試案例（涵蓋首頁與 API 測試）
├── requirements.txt         # 依賴套件（Flask, pytest）
└── README.md                # 專案操作說明
```

---

## 🚀 快速開始

### 1. 安裝套件

如果您尚未安裝本專案的依賴套件，請在專案根目錄下執行以下指令：

```bash
# 使用 python3 或是您的 Python 直譯器路徑
python -m pip install -r requirements.txt
```

### 2. 啟動 Flask 伺服器

執行 `src/app.py` 啟動伺服器：

```bash
python src/app.py
```

啟動後，後端將在 `http://127.0.0.1:19191` 運行。

* 預設連接埠為：`19191`

### 3. 瀏覽網頁

開啟瀏覽器並訪問 [http://127.0.0.1:19191](http://127.0.0.1:19191)，即可使用此精美的任務管理儀表板！

---

## 🧪 執行單元測試

本專案使用 `pytest` 進行全自動單元測試。

在專案根目錄下，執行以下指令以執行所有測試：

```bash
python -m pytest
```

這將會自動偵測 `test/` 目錄下的測試案例，驗證所有 API 端點與頁面載入狀態。
