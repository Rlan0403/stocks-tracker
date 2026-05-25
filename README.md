# 📈 台股三大法人追蹤系統

即時追蹤台股三大法人買賣超動態，自動偵測連續買超/賣超警示。

## ✨ 功能特色

- 📊 **即時資料**：自動從證交所 API 獲取最新三大法人買賣超資料
- 🎯 **TOP 10 排行**：顯示買超/賣超前 10 名個股
- 🟡 **智慧警示**：連續買超 3 天顯示黃色注意，5 天顯示紅色警示
- 💾 **歷史追蹤**：自動記錄歷史資料，計算連續天數
- 📱 **響應式設計**：支援桌面與行動裝置

## 🚀 快速開始

### 方法 1：部署到 Streamlit Cloud（推薦）

1. **Fork 此專案到您的 GitHub**
   
2. **前往 Streamlit Cloud**
   - 訪問 https://streamlit.io/cloud
   - 使用 GitHub 帳號登入
   
3. **建立新應用**
   - 點擊 "New app"
   - 選擇您的 GitHub repository
   - Main file path: `app.py`
   - 點擊 "Deploy"

4. **完成！**
   - 等待 1-2 分鐘部署完成
   - 您會獲得一個專屬網址，例如：`https://your-app.streamlit.app`

### 方法 2：本機執行

1. **Clone 專案**
```bash
git clone https://github.com/your-username/twse-tracker.git
cd twse-tracker
```

2. **安裝套件**
```bash
pip install -r requirements.txt
```

3. **執行應用**
```bash
streamlit run app.py
```

4. **開啟瀏覽器**
   - 自動開啟 http://localhost:8501

## 📦 專案結構

```
twse-tracker/
│
├── app.py                 # 主程式
├── requirements.txt       # Python 套件依賴
├── README.md             # 說明文件
├── .streamlit/
│   └── config.toml       # Streamlit 設定
└── data_storage/         # 資料儲存目錄（自動建立）
    └── history.json      # 歷史紀錄
```

## 🎨 使用說明

1. **選擇日期**：在側邊欄選擇要查詢的交易日
2. **更新資料**：點擊「🔄 更新資料」按鈕
3. **查看結果**：
   - 買超 TOP 10：綠色 Tab
   - 賣超 TOP 10：紅色 Tab
4. **警示判讀**：
   - 🟢 正常（1-2天）
   - 🟡 注意（連續 3-4 天）
   - 🔴 警示（連續 5 天以上）

## ⚠️ 注意事項

- 📅 **交易日限制**：僅交易日有資料，週末及國定假日無法查詢
- ⏰ **更新時間**：盤後約 18:00-20:00 才會有當日資料
- 🌐 **網路連線**：需連線至證交所 API
- 💾 **資料儲存**：歷史紀錄儲存在本地 `data_storage/` 目錄

## 🔧 技術棧

- **前端框架**：Streamlit 1.28+
- **資料處理**：Pandas 2.0+
- **資料來源**：證交所 T86 API
- **資料儲存**：JSON 本地檔案

## 📊 資料來源

- [證交所三大法人買賣超日報](https://www.twse.com.tw/fund/T86)

## ❓ 常見問題

### Q: 為什麼無法更新資料？
A: 請確認：
1. 選擇的日期為交易日（非週末或假日）
2. 時間為盤後 18:00 之後
3. 網路連線正常

### Q: 可以部署到 Vercel 嗎？
A: 不建議。Vercel 主要支援 Node.js/靜態網站，不支援 Python Streamlit 應用。請使用 Streamlit Cloud、Heroku 或其他支援 Python 的平台。

### Q: 資料會永久保存嗎？
A: 歷史紀錄儲存在本地 `data_storage/history.json`，僅保留最近 60 天的資料。

### Q: 如何新增更多功能？
A: 您可以修改 `app.py`，例如：
- 增加更多統計指標
- 整合其他資料來源
- 新增圖表視覺化

## 📝 授權

MIT License

## 🤝 貢獻

歡迎提交 Issue 或 Pull Request！

---

**免責聲明**：本系統僅供參考，不構成任何投資建議。投資有風險，請謹慎決策。
