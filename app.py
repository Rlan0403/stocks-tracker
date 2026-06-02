import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from datetime import datetime, timedelta
import json
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 頁面設定
st.set_page_config(
    page_title="台股籌碼分析系統",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS 樣式
st.markdown("""
<style>
    .main .block-container {max-width: 1200px; padding: 1rem 2rem;}
    @media (max-width: 768px) {.main .block-container {padding: 1rem;}}
    .main {background: #f5f7fa;}
    h1, h2, h3, h4 {color: #2c3e50 !important; font-weight: 700 !important;}
    h1 {font-size: 2rem !important; margin-bottom: 0.5rem !important;}
    @media (max-width: 768px) {h1 {font-size: 1.5rem !important;}}
    
    .metric-card {
        background: #ffffff;
        border: 1px solid #dee2e6;
        border-radius: 12px;
        padding: 1.2rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
        margin-bottom: 1rem;
    }
    
    .stat-label {font-size: 0.85rem; color: #6c757d; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.5rem; font-weight: 600;}
    .stat-value {font-size: 1.8rem; font-weight: 700; margin: 0;}
    @media (max-width: 768px) {.stat-value {font-size: 1.4rem;}}
    
    .stButton {width: 100%;}
    .stButton>button {
        background: #4a90e2; color: #ffffff; font-weight: 600; border: none;
        border-radius: 10px; padding: 0.75rem 1.5rem; width: 100%;
        box-shadow: 0 2px 8px rgba(74, 144, 226, 0.3); transition: all 0.3s ease;
    }
    .stButton>button:hover {background: #357abd; box-shadow: 0 4px 12px rgba(74, 144, 226, 0.4); transform: translateY(-2px);}
    
    table {width: 100%; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08); border-collapse: separate; border-spacing: 0;}
    thead th {background: #e9ecef; color: #2c3e50; font-weight: 700; padding: 1rem 0.75rem; text-align: center; border: none; font-size: 0.9rem;}
    @media (max-width: 768px) {thead th {padding: 0.75rem 0.5rem; font-size: 0.75rem;}}
    tbody td {background: #ffffff; color: #495057; padding: 0.9rem 0.75rem; text-align: center; border-bottom: 1px solid #f1f3f5; font-size: 0.9rem;}
    @media (max-width: 768px) {tbody td {padding: 0.7rem 0.5rem; font-size: 0.8rem;}}
    tbody tr:nth-child(even) td {background: #e9ecef;}
    tbody tr:hover td {background: #dee2e6; transition: all 0.2s ease;}
    
    .warning-row td {background: #fff3cd !important; border-left: 4px solid #ffc107 !important;}
    .alert-row td {background: #f8d7da !important; border-left: 4px solid #dc3545 !important;}
    
    .positive {color: #28a745 !important; font-weight: 700;}
    .negative {color: #dc3545 !important; font-weight: 700;}
    .neutral {color: #6c757d !important;}
    
    .badge {display: inline-block; padding: 0.35rem 0.75rem; border-radius: 12px; font-size: 0.8rem; font-weight: 700; white-space: nowrap;}
    .badge-normal {background: #e9ecef; color: #6c757d;}
    .badge-warning {background: #fff3cd; color: #856404; border: 1px solid #ffc107;}
    .badge-alert {background: #f8d7da; color: #721c24; border: 1px solid #dc3545;}
    
    .stAlert {background: #d1ecf1 !important; border-left: 4px solid #17a2b8 !important; color: #0c5460 !important; border-radius: 8px;}
    
    .stTabs [data-baseweb="tab-list"] {gap: 8px; background: #ffffff; padding: 0.5rem; border-radius: 12px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);}
    .stTabs [data-baseweb="tab"] {background: transparent; color: #6c757d; border-radius: 8px; padding: 0.75rem 1.5rem; font-weight: 600;}
    .stTabs [aria-selected="true"] {background: #4a90e2; color: white;}
    
    .stProgress > div > div {background: #4a90e2;}
    
    .stTextInput > div > div > input {background: #ffffff; border: 2px solid #dee2e6; border-radius: 8px; color: #495057; font-size: 1rem; padding: 0.75rem;}
    .stTextInput > div > div > input:focus {border-color: #4a90e2; box-shadow: 0 0 0 0.2rem rgba(74, 144, 226, 0.25);}
    
    .stRadio > div {background: #ffffff; padding: 0.5rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);}
    
    [data-testid="stMetricValue"] {color: #2c3e50; font-size: 1.8rem;}
    @media (max-width: 768px) {[data-testid="stMetricValue"] {font-size: 1.3rem;}}
</style>
""", unsafe_allow_html=True)

# 資料目錄
DATA_DIR = Path("data_storage")
DATA_DIR.mkdir(exist_ok=True)
HISTORY_FILE = DATA_DIR / "history.json"

# ==================== 工具函數 ====================

def format_number(n):
    """格式化數字"""
    if n is None or n == 0:
        return "0"
    abs_n = abs(n)
    sign = '-' if n < 0 else ''
    if abs_n >= 100000000:
        return f"{sign}{abs_n/100000000:.2f}億"
    elif abs_n >= 10000:
        return f"{sign}{abs_n/10000:.1f}萬"
    else:
        return f"{n:,.0f}"

def load_history():
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_history(data):
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ==================== Yahoo Finance API ====================

@st.cache_data(ttl=300)  # 快取 5 分鐘
def fetch_stock_data(stock_code, period="3mo"):
    """使用 Yahoo Finance 取得股票資料"""
    try:
        ticker_symbol = f"{stock_code}.TW"
        ticker = yf.Ticker(ticker_symbol)
        
        # 取得歷史資料
        hist = ticker.history(period=period)
        
        if hist.empty:
            # 嘗試 .TWO (上櫃)
            ticker_symbol = f"{stock_code}.TWO"
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period=period)
            
            if hist.empty:
                return None
        
        # 取得公司資訊
        try:
            info = ticker.info
        except:
            info = {}
        
        # 計算移動平均線
        hist['MA5'] = hist['Close'].rolling(window=5).mean()
        hist['MA20'] = hist['Close'].rolling(window=20).mean()
        hist['MA60'] = hist['Close'].rolling(window=60).mean()
        
        # 最新數據
        latest = hist.iloc[-1]
        prev = hist.iloc[-2] if len(hist) > 1 else latest
        
        change = latest['Close'] - prev['Close']
        change_pct = (change / prev['Close']) * 100 if prev['Close'] > 0 else 0
        
        return {
            'code': stock_code,
            'name': info.get('longName', info.get('shortName', stock_code)),
            'close': float(latest['Close']),
            'open': float(latest['Open']),
            'high': float(latest['High']),
            'low': float(latest['Low']),
            'volume': int(latest['Volume']) // 1000,  # 轉為張
            'change': float(change),
            'change_pct': float(change_pct),
            'prev_close': float(prev['Close']),
            'history': hist,
            'info': info,
            'ticker_symbol': ticker_symbol
        }
    except Exception as e:
        st.error(f"❌ 查詢錯誤: {str(e)}")
        return None

@st.cache_data(ttl=300)
def fetch_multiple_stocks(stock_codes):
    """批次取得多支股票資料（用於大盤追蹤）"""
    results = []
    for code in stock_codes:
        try:
            data = fetch_stock_data(code, period="1mo")
            if data:
                # 計算近 5 日漲跌
                hist = data['history']
                if len(hist) >= 5:
                    five_day_change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-5]) / hist['Close'].iloc[-5]) * 100
                else:
                    five_day_change = 0
                
                results.append({
                    'code': code,
                    'name': data['name'],
                    'close': data['close'],
                    'change': data['change'],
                    'change_pct': data['change_pct'],
                    'volume': data['volume'],
                    'five_day_change': five_day_change
                })
        except:
            continue
    return results

# ==================== 主程式 ====================

# 標題
col_title, col_mode = st.columns([3, 1])

with col_title:
    st.title("📈 台股籌碼分析系統")
    st.caption("✨ 使用 Yahoo Finance API，任何環境都能即時查詢")

with col_mode:
    st.write("")
    mode = st.radio(
        "模式",
        ["個股分析", "熱門股追蹤"],
        horizontal=True,
        label_visibility="collapsed"
    )

st.markdown("---")

# ==================== 個股分析 ====================

if mode == "個股分析":
    st.subheader("🔍 個股查詢與分析")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        stock_code = st.text_input(
            "股票代號",
            value="2330",
            placeholder="例：2330"
        ).strip()
    
    with col2:
        period = st.selectbox(
            "查詢期間",
            ["1個月", "3個月", "6個月", "1年", "2年"],
            index=1
        )
    
    with col3:
        st.write("")
        st.write("")
        analyze_btn = st.button("🔍 開始查詢", type="primary", use_container_width=True)
    
    period_map = {
        "1個月": "1mo",
        "3個月": "3mo",
        "6個月": "6mo",
        "1年": "1y",
        "2年": "2y"
    }
    
    if analyze_btn and stock_code:
        with st.spinner('正在查詢中...'):
            data = fetch_stock_data(stock_code, period_map[period])
        
        if not data:
            st.error(f"❌ 查無股票代號 {stock_code}")
            st.info("💡 請確認：\n- 股票代號正確（如：2330）\n- 為台灣上市/上櫃股票")
        else:
            # 股票名稱
            st.markdown(f"### {data['name']} ({stock_code})")
            
            # 基本資訊卡片
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                delta_color = "normal" if data['change'] >= 0 else "inverse"
                st.metric(
                    "收盤價",
                    f"${data['close']:.2f}",
                    f"{data['change']:+.2f} ({data['change_pct']:+.2f}%)",
                    delta_color=delta_color
                )
            
            with col2:
                st.metric("成交量", f"{data['volume']:,} 張")
            
            with col3:
                st.metric("最高", f"${data['high']:.2f}")
            
            with col4:
                st.metric("最低", f"${data['low']:.2f}")
            
            st.markdown("---")
            
            # 分析頁籤
            tab1, tab2, tab3, tab4 = st.tabs([
                "📈 K線圖", 
                "📊 成交量", 
                "📋 歷史數據", 
                "📄 公司資訊"
            ])
            
            hist = data['history']
            
            with tab1:
                st.subheader("K線圖與移動平均線")
                
                fig = go.Figure()
                
                # K 線
                fig.add_trace(go.Candlestick(
                    x=hist.index,
                    open=hist['Open'],
                    high=hist['High'],
                    low=hist['Low'],
                    close=hist['Close'],
                    name='K線',
                    increasing_line_color='#dc3545',
                    decreasing_line_color='#28a745'
                ))
                
                # 移動平均線
                fig.add_trace(go.Scatter(
                    x=hist.index, y=hist['MA5'],
                    name='MA5', line=dict(color='#ffc107', width=1.5)
                ))
                
                fig.add_trace(go.Scatter(
                    x=hist.index, y=hist['MA20'],
                    name='MA20', line=dict(color='#4a90e2', width=1.5)
                ))
                
                fig.add_trace(go.Scatter(
                    x=hist.index, y=hist['MA60'],
                    name='MA60', line=dict(color='#9c27b0', width=1.5)
                ))
                
                fig.update_layout(
                    yaxis_title='價格 (TWD)',
                    xaxis_title='日期',
                    template='plotly_white',
                    height=500,
                    xaxis_rangeslider_visible=False,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # 技術指標摘要
                st.subheader("技術指標")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    ma5 = hist['MA5'].iloc[-1]
                    if not pd.isna(ma5):
                        ma5_signal = "📈 站上" if data['close'] > ma5 else "📉 跌破"
                        st.metric("MA5 (5日均線)", f"${ma5:.2f}", ma5_signal)
                
                with col2:
                    ma20 = hist['MA20'].iloc[-1]
                    if not pd.isna(ma20):
                        ma20_signal = "📈 站上" if data['close'] > ma20 else "📉 跌破"
                        st.metric("MA20 (月線)", f"${ma20:.2f}", ma20_signal)
                
                with col3:
                    ma60 = hist['MA60'].iloc[-1]
                    if not pd.isna(ma60):
                        ma60_signal = "📈 站上" if data['close'] > ma60 else "📉 跌破"
                        st.metric("MA60 (季線)", f"${ma60:.2f}", ma60_signal)
            
            with tab2:
                st.subheader("成交量分析")
                
                fig_vol = go.Figure()
                
                colors = ['#dc3545' if hist['Close'].iloc[i] > hist['Open'].iloc[i] else '#28a745' 
                         for i in range(len(hist))]
                
                fig_vol.add_trace(go.Bar(
                    x=hist.index,
                    y=hist['Volume'] / 1000,
                    name='成交量',
                    marker_color=colors
                ))
                
                # 20 日平均量
                vol_ma20 = hist['Volume'].rolling(window=20).mean() / 1000
                fig_vol.add_trace(go.Scatter(
                    x=hist.index,
                    y=vol_ma20,
                    name='20日均量',
                    line=dict(color='#4a90e2', width=2)
                ))
                
                fig_vol.update_layout(
                    yaxis_title='成交量 (千張)',
                    xaxis_title='日期',
                    template='plotly_white',
                    height=400,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                
                st.plotly_chart(fig_vol, use_container_width=True)
                
                # 量能指標
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    avg_vol = hist['Volume'].mean() / 1000
                    st.metric("平均成交量", f"{avg_vol:,.0f} 張")
                
                with col2:
                    today_vol = data['volume']
                    ratio = (today_vol / avg_vol * 100) if avg_vol > 0 else 0
                    st.metric("今日量能比", f"{ratio:.0f}%")
                
                with col3:
                    max_vol = hist['Volume'].max() / 1000
                    st.metric("期間最大量", f"{max_vol:,.0f} 張")
            
            with tab3:
                st.subheader("歷史交易數據")
                
                df_display = hist.copy()
                df_display['漲跌'] = df_display['Close'] - df_display['Open']
                df_display['漲跌幅%'] = ((df_display['Close'] - df_display['Open']) / df_display['Open']) * 100
                df_display['成交量(張)'] = (df_display['Volume'] / 1000).astype(int)
                
                df_display = df_display[['Open', 'High', 'Low', 'Close', '漲跌', '漲跌幅%', '成交量(張)']]
                df_display.columns = ['開盤', '最高', '最低', '收盤', '漲跌', '漲跌幅%', '成交量(張)']
                df_display = df_display.round(2)
                
                st.dataframe(
                    df_display.sort_index(ascending=False),
                    use_container_width=True,
                    height=500
                )
                
                # 下載 CSV
                csv = df_display.to_csv(encoding='utf-8-sig')
                st.download_button(
                    label="📥 下載歷史數據 (CSV)",
                    data=csv,
                    file_name=f"{stock_code}_{period}_history.csv",
                    mime="text/csv"
                )
            
            with tab4:
                st.subheader("公司資訊")
                
                info = data['info']
                
                if info:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**📊 基本資訊**")
                        st.write(f"**產業：** {info.get('industry', 'N/A')}")
                        st.write(f"**部門：** {info.get('sector', 'N/A')}")
                        st.write(f"**員工數：** {info.get('fullTimeEmployees', 'N/A'):,}" if info.get('fullTimeEmployees') else "**員工數：** N/A")
                        st.write(f"**總部：** {info.get('city', '')} {info.get('country', '')}")
                    
                    with col2:
                        st.markdown("**💰 財務指標**")
                        if info.get('marketCap'):
                            mc = info['marketCap']
                            if mc >= 1e12:
                                st.write(f"**市值：** {mc/1e12:.2f} 兆")
                            elif mc >= 1e8:
                                st.write(f"**市值：** {mc/1e8:.2f} 億")
                            else:
                                st.write(f"**市值：** {mc:,}")
                        
                        if info.get('trailingPE'):
                            st.write(f"**本益比 (PE)：** {info['trailingPE']:.2f}")
                        
                        if info.get('priceToBook'):
                            st.write(f"**股價淨值比 (PB)：** {info['priceToBook']:.2f}")
                        
                        if info.get('dividendYield'):
                            st.write(f"**股息殖利率：** {info['dividendYield']*100:.2f}%")
                        
                        if info.get('beta'):
                            st.write(f"**Beta 值：** {info['beta']:.2f}")
                    
                    # 52 週高低點
                    st.markdown("**📈 52 週區間**")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if info.get('fiftyTwoWeekHigh'):
                            st.metric("52週最高", f"${info['fiftyTwoWeekHigh']:.2f}")
                    
                    with col2:
                        if info.get('fiftyTwoWeekLow'):
                            st.metric("52週最低", f"${info['fiftyTwoWeekLow']:.2f}")
                    
                    with col3:
                        if info.get('fiftyTwoWeekHigh') and info.get('fiftyTwoWeekLow'):
                            high = info['fiftyTwoWeekHigh']
                            low = info['fiftyTwoWeekLow']
                            position = ((data['close'] - low) / (high - low)) * 100
                            st.metric("位置", f"{position:.0f}%")
                    
                    # 公司簡介
                    if info.get('longBusinessSummary'):
                        with st.expander("📝 公司簡介"):
                            st.write(info['longBusinessSummary'])
                else:
                    st.info("該股票的詳細公司資訊暫時無法取得")
            
            # 進階功能說明
            with st.expander("ℹ️ 想要更多功能？"):
                st.markdown("""
                #### 🔓 完整版功能（需本地運行）
                
                以下功能需要在**本地電腦**運行才能使用（因為證交所 API 有 IP 限制）：
                
                - 📊 **三大法人買賣超**（外資、投信、自營）
                - 💳 **信用交易**（融資、融券）
                - 🏦 **集保股權分散**（千張大戶、散戶）
                - 📅 **月營收 YoY/MoM**
                - 👥 **董監持股與質押率**
                - ⚠️ **智慧警示系統**
                
                #### 🚀 如何在本地運行
                
                ```bash
                # 1. Clone 專案
                git clone https://github.com/Rlan0403/stocks-tracker.git
                cd stocks-tracker
                
                # 2. 安裝套件
                pip install -r requirements.txt
                
                # 3. 運行
                streamlit run app.py
                ```
                
                #### 📱 目前 Cloud 版本提供
                
                ✅ 即時股價、漲跌幅
                ✅ K 線圖 + 移動平均線（MA5、MA20、MA60）
                ✅ 成交量分析
                ✅ 完整歷史數據（可下載 CSV）
                ✅ 公司基本資訊與財務指標
                ✅ 52 週高低點
                
                **手機隨時可查！** 📱
                """)

# ==================== 熱門股追蹤 ====================

else:
    st.subheader("📊 熱門股即時追蹤")
    
    st.info("💡 追蹤台股熱門股票的即時表現，每 5 分鐘自動更新")
    
    # 預設追蹤清單
    default_stocks = {
        "權值股": ["2330", "2454", "2317", "2308", "2412", "2382", "2891", "2881", "1303", "1301"],
        "ETF": ["0050", "0056", "00878", "006208", "00929", "00919"],
        "金融": ["2891", "2881", "2882", "2884", "2880", "2885", "2886", "2887", "2890"],
        "AI概念": ["2330", "2454", "3661", "2376", "3017", "6669", "3231", "2382"],
    }
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        category = st.selectbox(
            "選擇類別",
            list(default_stocks.keys()) + ["自訂"]
        )
    
    with col2:
        st.write("")
        st.write("")
        refresh_btn = st.button("🔄 更新資料", type="primary", use_container_width=True)
    
    if category == "自訂":
        custom_codes = st.text_input(
            "輸入股票代號（以逗號分隔）",
            value="2330,2454,2317",
            placeholder="例：2330,2454,2317"
        )
        stock_codes = [c.strip() for c in custom_codes.split(",") if c.strip()]
    else:
        stock_codes = default_stocks[category]
    
    if refresh_btn or 'stock_data' not in st.session_state or st.session_state.get('last_category') != category:
        with st.spinner(f'正在查詢 {len(stock_codes)} 支股票...'):
            progress_bar = st.progress(0)
            results = []
            
            for i, code in enumerate(stock_codes):
                data = fetch_stock_data(code, period="1mo")
                if data:
                    hist = data['history']
                    if len(hist) >= 5:
                        five_day_change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-5]) / hist['Close'].iloc[-5]) * 100
                    else:
                        five_day_change = 0
                    
                    if len(hist) >= 20:
                        twenty_day_change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-20]) / hist['Close'].iloc[-20]) * 100
                    else:
                        twenty_day_change = 0
                    
                    results.append({
                        'code': code,
                        'name': data['name'],
                        'close': data['close'],
                        'change': data['change'],
                        'change_pct': data['change_pct'],
                        'volume': data['volume'],
                        'five_day': five_day_change,
                        'twenty_day': twenty_day_change
                    })
                
                progress_bar.progress((i + 1) / len(stock_codes))
            
            progress_bar.empty()
            st.session_state['stock_data'] = results
            st.session_state['last_category'] = category
            st.session_state['last_update'] = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    
    # 顯示資料
    if 'stock_data' in st.session_state and st.session_state['stock_data']:
        results = st.session_state['stock_data']
        
        # 統計卡片
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="stat-label">追蹤檔數</div>
                <div class="stat-value" style="color: #4a90e2;">{len(results)} 檔</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            up_count = len([r for r in results if r['change'] > 0])
            st.markdown(f"""
            <div class="metric-card">
                <div class="stat-label">上漲</div>
                <div class="stat-value" style="color: #dc3545;">{up_count} 檔</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            down_count = len([r for r in results if r['change'] < 0])
            st.markdown(f"""
            <div class="metric-card">
                <div class="stat-label">下跌</div>
                <div class="stat-value" style="color: #28a745;">{down_count} 檔</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            avg_change = sum([r['change_pct'] for r in results]) / len(results) if results else 0
            color = "#dc3545" if avg_change > 0 else "#28a745"
            st.markdown(f"""
            <div class="metric-card">
                <div class="stat-label">平均漲跌</div>
                <div class="stat-value" style="color: {color};">{avg_change:+.2f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.caption(f"📅 最後更新：{st.session_state.get('last_update', 'N/A')}")
        
        st.markdown("---")
        
        # 表格顯示
        tab1, tab2 = st.tabs(["📈 漲幅排行", "📉 跌幅排行"])
        
        with tab1:
            st.subheader("漲幅 TOP")
            sorted_up = sorted(results, key=lambda x: x['change_pct'], reverse=True)
            
            html = '<table><thead><tr><th>排名</th><th>代號</th><th>名稱</th><th>收盤</th><th>漲跌</th><th>漲跌幅</th><th>5日</th><th>20日</th><th>成交量</th></tr></thead><tbody>'
            
            for i, r in enumerate(sorted_up, 1):
                change_class = 'positive' if r['change'] > 0 else 'negative' if r['change'] < 0 else 'neutral'
                change_sign = '+' if r['change'] > 0 else ''
                
                five_day_class = 'positive' if r['five_day'] > 0 else 'negative' if r['five_day'] < 0 else 'neutral'
                twenty_day_class = 'positive' if r['twenty_day'] > 0 else 'negative' if r['twenty_day'] < 0 else 'neutral'
                
                html += f'<tr>'
                html += f'<td>{i:02d}</td>'
                html += f'<td><strong>{r["code"]}</strong></td>'
                html += f'<td>{r["name"]}</td>'
                html += f'<td>${r["close"]:.2f}</td>'
                html += f'<td><span class="{change_class}">{change_sign}{r["change"]:.2f}</span></td>'
                html += f'<td><span class="{change_class}">{change_sign}{r["change_pct"]:.2f}%</span></td>'
                html += f'<td><span class="{five_day_class}">{r["five_day"]:+.2f}%</span></td>'
                html += f'<td><span class="{twenty_day_class}">{r["twenty_day"]:+.2f}%</span></td>'
                html += f'<td>{r["volume"]:,}</td>'
                html += f'</tr>'
            
            html += '</tbody></table>'
            st.markdown(html, unsafe_allow_html=True)
        
        with tab2:
            st.subheader("跌幅 TOP")
            sorted_down = sorted(results, key=lambda x: x['change_pct'])
            
            html = '<table><thead><tr><th>排名</th><th>代號</th><th>名稱</th><th>收盤</th><th>漲跌</th><th>漲跌幅</th><th>5日</th><th>20日</th><th>成交量</th></tr></thead><tbody>'
            
            for i, r in enumerate(sorted_down, 1):
                change_class = 'positive' if r['change'] > 0 else 'negative' if r['change'] < 0 else 'neutral'
                change_sign = '+' if r['change'] > 0 else ''
                
                five_day_class = 'positive' if r['five_day'] > 0 else 'negative' if r['five_day'] < 0 else 'neutral'
                twenty_day_class = 'positive' if r['twenty_day'] > 0 else 'negative' if r['twenty_day'] < 0 else 'neutral'
                
                html += f'<tr>'
                html += f'<td>{i:02d}</td>'
                html += f'<td><strong>{r["code"]}</strong></td>'
                html += f'<td>{r["name"]}</td>'
                html += f'<td>${r["close"]:.2f}</td>'
                html += f'<td><span class="{change_class}">{change_sign}{r["change"]:.2f}</span></td>'
                html += f'<td><span class="{change_class}">{change_sign}{r["change_pct"]:.2f}%</span></td>'
                html += f'<td><span class="{five_day_class}">{r["five_day"]:+.2f}%</span></td>'
                html += f'<td><span class="{twenty_day_class}">{r["twenty_day"]:+.2f}%</span></td>'
                html += f'<td>{r["volume"]:,}</td>'
                html += f'</tr>'
            
            html += '</tbody></table>'
            st.markdown(html, unsafe_allow_html=True)

# 頁尾
st.markdown("---")
st.caption("📊 資料來源：Yahoo Finance | ⚠️ 僅供參考，非投資建議 | ⏱️ 資料可能有 15-20 分鐘延遲")
