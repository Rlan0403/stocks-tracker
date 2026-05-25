# 📁 檔案說明總覽

## 核心檔案（必須）

### 1. `app.py` ⭐
**主程式檔案**
- 完整的 Streamlit 應用程式
- 包含所有功能：資料抓取、歷史追蹤、視覺化、警示系統
- 這是整個應用的核心

**功能特色：**
- ✅ 自動從證交所 API 獲取資料
- ✅ 計算連續買賣超天數
- ✅ 黃色（3天）、紅色（5天）警示
- ✅ 資料視覺化表格
- ✅ 統計儀表板
- ✅ 歷史紀錄管理（JSON 格式）

### 2. `requirements.txt` ⭐
**Python 套件依賴清單**
```
streamlit>=1.28.0    # 前端框架
pandas>=2.0.0        # 資料處理
openpyxl>=3.1.0      # Excel 支援
requests>=2.31.0     # API 請求
```

### 3. `.streamlit/config.toml` ⭐
**Streamlit 設定檔**
- 自訂主題配色（深色系）
- 伺服器設定
- 瀏覽器行為設定

---

## 文件檔案（建議閱讀）

### 4. `README.md`
**完整專案說明**
- 功能介紹
- 快速開始指南
- 專案結構
- 使用說明
- 常見問題

### 5. `QUICKSTART.md` 🚀
**3 步驟快速上線指南**
- 最簡單的部署教學
- 5 分鐘完成部署
- 適合新手

### 6. `DEPLOYMENT.md`
**詳細部署教學**
- Streamlit Cloud 部署完整流程
- 本機執行方法
- 自動更新設定
- 問題排除

---

## 輔助檔案（選用）

### 7. `fetch_data.py`
**獨立資料抓取腳本**
- 可單獨執行
- 用於定時抓取資料
- 儲存為 JSON 檔案
- 適合進階使用者

**使用方式：**
```bash
python fetch_data.py
```

### 8. `test_environment.py`
**環境測試工具**
- 檢查 Python 版本
- 檢查套件安裝
- 檢查檔案完整性
- 測試 API 連線

**使用方式：**
```bash
python test_environment.py
```

### 9. `.gitignore`
**Git 忽略清單**
- 排除不需要版本控制的檔案
- Python 快取檔案
- 資料檔案（視需求調整）

---

## 🎯 您需要做什麼

### 最小部署（3 個檔案）
只需要這 3 個檔案就能運行：
1. ✅ `app.py`
2. ✅ `requirements.txt`
3. ✅ `.streamlit/config.toml`

### 推薦部署（所有檔案）
建議上傳所有檔案，包括文件：
- 更完整的專案結構
- 方便未來維護
- 文件幫助理解

---

## 📤 上傳到 GitHub 的步驟

### 方法 1：網頁上傳（最簡單）

1. 登入 GitHub
2. 建立新 Repository（Public）
3. 拖曳**所有檔案**到頁面
4. 記得包含 `.streamlit` 資料夾
5. Commit

### 方法 2：VSCode

1. 開啟資料夾
2. Source Control → Initialize Repository
3. Commit all changes
4. Publish to GitHub

### 方法 3：Git 指令

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/your-username/twse-tracker.git
git push -u origin main
```

---

## 🚀 部署後的網址範例

成功部署後，您會得到：
```
https://your-app-name.streamlit.app
```

可以：
- 分享給朋友
- 加入書籤
- 設定手機桌面捷徑

---

## 💡 客製化建議

想要修改外觀或功能？

**修改顏色：**
編輯 `app.py` 的 CSS 區塊：
```python
st.markdown("""
<style>
    /* 修改這裡的顏色 */
    --cyan: #00d4ff;    /* 主題色 */
    --bg: #07090f;      /* 背景色 */
</style>
""", unsafe_allow_html=True)
```

**新增功能：**
參考 Streamlit 文件：
- https://docs.streamlit.io

**整合資料庫：**
如需永久儲存，考慮：
- Google Sheets API
- SQLite
- Firebase

---

## ✅ 檔案完整性檢查

請確認您有以下檔案：

```
✅ app.py                    (14 KB)
✅ requirements.txt          (65 bytes)
✅ .streamlit/config.toml    (270 bytes)
✅ README.md                 (3.5 KB)
✅ QUICKSTART.md             (4.2 KB)
✅ DEPLOYMENT.md             (5.6 KB)
✅ fetch_data.py             (4.3 KB)
✅ test_environment.py       (2.8 KB)
✅ .gitignore                (407 bytes)
✅ FILES.md                  (本檔案)
```

總大小：約 35 KB

---

**準備好了嗎？開始部署吧！** 🎉
