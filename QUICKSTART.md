# 🎯 快速開始指南

## 📦 您下載的檔案包含

```
twse-tracker/
├── .streamlit/
│   └── config.toml          # Streamlit 設定檔
├── app.py                   # 主程式（核心檔案）
├── requirements.txt         # Python 套件依賴
├── README.md               # 完整說明文件
├── DEPLOYMENT.md           # 詳細部署教學
├── fetch_data.py           # 資料抓取腳本（選用）
├── .gitignore              # Git 忽略檔案
└── QUICKSTART.md           # 本檔案
```

---

## ⚡ 3 步驟上線（5 分鐘完成）

### 步驟 1️⃣：上傳到 GitHub

1. 登入 https://github.com
2. 點擊 "New repository"
3. 名稱：`twse-tracker`，設為 **Public**
4. 建立後，點擊 "uploading an existing file"
5. **拖曳所有檔案**到頁面（記得包含 `.streamlit` 資料夾）
6. 點擊 "Commit changes"

### 步驟 2️⃣：部署到 Streamlit Cloud

1. 前往 https://share.streamlit.io
2. 用 GitHub 帳號登入
3. 點擊 "New app"
4. 填寫：
   - Repository: `your-username/twse-tracker`
   - Branch: `main`
   - Main file: `app.py`
5. 點擊 "Deploy!"

### 步驟 3️⃣：完成！

- 等待 2-3 分鐘
- 您會獲得專屬網址：`https://your-app.streamlit.app`
- 現在可以開始使用了！🎉

---

## 💻 本機測試（選用）

如果想先在電腦上測試：

### Windows
```cmd
# 1. 安裝 Python (https://www.python.org/downloads/)
# 2. 開啟命令提示字元，切換到此資料夾
cd C:\path\to\twse-tracker

# 3. 安裝套件
pip install -r requirements.txt

# 4. 執行
streamlit run app.py
```

### Mac/Linux
```bash
cd /path/to/twse-tracker
pip3 install -r requirements.txt
streamlit run app.py
```

瀏覽器會自動開啟 http://localhost:8501

---

## 📝 VSCode 貼上步驟（如果您使用 VSCode）

1. 開啟 VSCode
2. File → Open Folder → 選擇 `twse-tracker` 資料夾
3. 確認看到以下檔案：
   - ✅ app.py
   - ✅ requirements.txt
   - ✅ .streamlit/config.toml
   - ✅ 其他檔案

4. 開啟終端機（Terminal → New Terminal）
5. 執行：
   ```bash
   pip install -r requirements.txt
   streamlit run app.py
   ```

---

## ⚠️ 重要提醒

### ❌ 不能用 Vercel
- Vercel 不支援 Python/Streamlit
- 請使用 **Streamlit Cloud**（免費）

### ✅ 可用的平台
- Streamlit Community Cloud（推薦，免費）
- Heroku
- Google Cloud Run
- Railway.app

### 📅 資料更新時間
- 盤後約 **18:00-20:00** 才有當日資料
- 週末及國定假日無資料

---

## 🆘 遇到問題？

### 問題 1：上傳到 GitHub 後找不到 .streamlit 資料夾
**解決**：確認您有上傳整個資料夾結構，包括隱藏的 `.streamlit` 目錄

### 問題 2：Streamlit Cloud 部署失敗
**解決**：
1. 檢查 Repository 是否為 Public
2. 確認 `requirements.txt` 已上傳
3. 查看錯誤日誌

### 問題 3：無法更新資料
**解決**：
1. 確認選擇的日期為交易日
2. 確認時間為盤後 18:00 之後
3. 等待數分鐘後重試

---

## 📚 進階學習

想要客製化或增加功能？

- **修改樣式**：編輯 `app.py` 中的 CSS
- **新增功能**：參考 Streamlit 官方文件 https://docs.streamlit.io
- **自動更新**：查看 `DEPLOYMENT.md` 的 GitHub Actions 設定

---

## ✨ 下一步

完成部署後，您可以：

1. 📱 分享連結給朋友
2. 🎨 客製化介面顏色和樣式
3. 📊 新增更多統計指標
4. 🤖 整合 Line Bot 或 Telegram Bot
5. 📈 加入技術分析指標

---

**祝您使用順利！有問題歡迎在 GitHub 開 Issue。** 💪
