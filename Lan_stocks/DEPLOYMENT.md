# 🚀 部署教學：將台股追蹤系統上線

## 📝 前言

此系統是 **Python Streamlit 應用程式**，需要部署到支援 Python 的平台。
**Vercel 不支援 Python**，因此我們使用 **Streamlit Community Cloud**（免費）。

---

## 方法 1：部署到 Streamlit Cloud（推薦）✨

### 步驟 1：準備 GitHub Repository

1. **登入 GitHub**
   - 前往 https://github.com
   - 登入您的帳號

2. **建立新的 Repository**
   - 點擊右上角 "+" → "New repository"
   - Repository name: `twse-tracker`（或任何您喜歡的名稱）
   - 設為 Public（公開）
   - ✅ 勾選 "Add a README file"
   - 點擊 "Create repository"

### 步驟 2：上傳程式碼

#### 選項 A：使用 GitHub 網頁介面（最簡單）

1. **進入您的 Repository**
   - 點擊 "Add file" → "Upload files"

2. **上傳以下檔案**（從您電腦拖曳到頁面）：
   ```
   app.py
   requirements.txt
   README.md
   .gitignore
   fetch_data.py（選用）
   ```

3. **建立 .streamlit 資料夾**
   - 點擊 "Add file" → "Create new file"
   - 檔名輸入：`.streamlit/config.toml`
   - 貼上 config.toml 的內容
   - 點擊 "Commit new file"

4. **完成上傳**
   - 所有檔案上傳後，您的 Repository 應該看起來像這樣：
   ```
   your-repo/
   ├── .streamlit/
   │   └── config.toml
   ├── app.py
   ├── requirements.txt
   ├── README.md
   ├── .gitignore
   └── fetch_data.py
   ```

#### 選項 B：使用 Git 指令（進階使用者）

```bash
# 1. Clone 您的 Repository
git clone https://github.com/your-username/twse-tracker.git
cd twse-tracker

# 2. 複製所有檔案到此資料夾

# 3. 提交到 GitHub
git add .
git commit -m "Initial commit: Add TWSE tracker app"
git push origin main
```

### 步驟 3：部署到 Streamlit Cloud

1. **前往 Streamlit Cloud**
   - 訪問 https://streamlit.io/cloud
   - 點擊 "Sign up" 或 "Sign in"
   - 選擇 "Continue with GitHub"

2. **授權 GitHub**
   - 允許 Streamlit 訪問您的 GitHub repositories

3. **建立新應用**
   - 點擊 "New app" 按鈕
   - 選擇：
     * Repository: `your-username/twse-tracker`
     * Branch: `main`
     * Main file path: `app.py`
   - 點擊 "Deploy!"

4. **等待部署**
   - 首次部署約需 2-3 分鐘
   - 您會看到建置日誌

5. **完成！**
   - 部署成功後，您會獲得一個專屬網址
   - 例如：`https://your-app.streamlit.app`
   - 可以分享給任何人使用！

### 步驟 4：設定自訂網址（選用）

1. 在 Streamlit Cloud 設定中
2. 前往 "Settings" → "General"
3. 修改 App URL
4. 儲存即可

---

## 方法 2：本機執行（開發測試用）

### Windows 使用者

1. **安裝 Python**
   - 下載：https://www.python.org/downloads/
   - 安裝時勾選 "Add Python to PATH"

2. **開啟命令提示字元 (CMD)**
   ```cmd
   cd C:\path\to\twse-tracker
   pip install -r requirements.txt
   streamlit run app.py
   ```

3. **開啟瀏覽器**
   - 自動開啟 http://localhost:8501

### Mac/Linux 使用者

```bash
cd /path/to/twse-tracker
pip3 install -r requirements.txt
streamlit run app.py
```

---

## 🔧 進階：自動更新資料

### 使用 GitHub Actions（自動排程）

在 Repository 中建立 `.github/workflows/update-data.yml`：

```yaml
name: Update TWSE Data

on:
  schedule:
    # 每個交易日 18:30 自動執行
    - cron: '30 10 * * 1-5'  # UTC 時間
  workflow_dispatch:  # 允許手動觸發

jobs:
  fetch-data:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install requests
      
      - name: Fetch data
        run: |
          python fetch_data.py
      
      - name: Commit data
        run: |
          git config --global user.name 'GitHub Actions'
          git config --global user.email 'actions@github.com'
          git add data_storage/*.json
          git commit -m "Auto update: $(date)" || exit 0
          git push
```

---

## ❓ 常見問題排除

### Q1: 部署後顯示 "Oh no!" 錯誤
**A:** 檢查以下項目：
- `requirements.txt` 是否正確上傳
- `app.py` 語法是否有誤
- 查看 Streamlit Cloud 的錯誤日誌

### Q2: 無法連線到證交所 API
**A:** 可能原因：
- 選擇的日期為非交易日
- 時間尚未到盤後 18:00
- 證交所網站暫時無法連線

### Q3: 歷史資料沒有保存
**A:** Streamlit Cloud 每次重啟會清空檔案。解決方案：
- 使用 Streamlit 的 `st.session_state` 暫存
- 或整合 Google Sheets / SQLite 資料庫

### Q4: 想要客製化樣式
**A:** 修改 `app.py` 中的 CSS：
```python
st.markdown("""
<style>
    /* 在這裡加入您的 CSS */
</style>
""", unsafe_allow_html=True)
```

---

## 📞 取得協助

- Streamlit 官方文件：https://docs.streamlit.io
- Streamlit 社群：https://discuss.streamlit.io
- GitHub Issues：在您的 repo 建立 issue

---

## ✅ 檢查清單

部署前確認：

- [ ] 所有檔案已上傳到 GitHub
- [ ] Repository 設為 Public
- [ ] `requirements.txt` 包含所有套件
- [ ] `app.py` 可以本機執行
- [ ] 已註冊 Streamlit Cloud 帳號
- [ ] GitHub 帳號已授權給 Streamlit

部署後確認：

- [ ] 應用程式成功啟動
- [ ] 可以選擇日期
- [ ] 可以更新資料
- [ ] 資料表格正確顯示
- [ ] 警示顏色正常運作

---

**祝您部署順利！** 🎉
