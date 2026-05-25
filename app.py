import streamlit as st
import pandas as pd
import requests
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

# 自訂 CSS
st.markdown("""
<style>
    .main {background-color: #07090f;}
    .stButton>button {
        background: linear-gradient(135deg, #0099cc, #00d4ff);
        color: #07090f;
        font-weight: bold;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
    }
    .metric-card {
        background: #0d1220;
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 10px;
        padding: 1rem;
    }
    .warning-row {
        background-color: rgba(245,197,24,0.15) !important;
        border-left: 3px solid #f5c518 !important;
    }
    .alert-row {
        background-color: rgba(255,77,77,0.2) !important;
        border-left: 3px solid #ff4d4d !important;
    }
    .expander-header {
        background: #0d1220;
        padding: 0.5rem;
        border-radius: 5px;
    }
    div[data-testid="stExpander"] {
        background: #0d1220;
        border: 1px solid rgba(0,212,255,0.2);
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# 資料目錄
DATA_DIR = Path("data_storage")
DATA_DIR.mkdir(exist_ok=True)
HISTORY_FILE = DATA_DIR / "history.json"

# ==================== 工具函數 ====================

def get_trading_days(end_date, num_days=10):
    """取得過去 N 個交易日"""
    trading_days = []
    current = end_date
    
    while len(trading_days) < num_days:
        # 排除週末
        if current.weekday() < 5:  # 0-4 是週一到週五
            trading_days.append(current.strftime("%Y%m%d"))
        current -= timedelta(days=1)
    
    return trading_days

def load_history():
    """載入歷史買賣超紀錄"""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_history(data):
    """儲存歷史紀錄"""
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def calculate_streak(code, date_key, history_type):
    """計算連續買超/賣超天數"""
    history = load_history()
    key = f"{code}_{history_type}"
    
    if key not in history:
        return 1
    
    dates = sorted(history[key]['dates'], reverse=True)
    if date_key not in dates:
        return 1
    
    idx = dates.index(date_key)
    streak = 1
    
    for i in range(idx + 1, len(dates)):
        d1 = datetime.strptime(dates[i-1], "%Y%m%d")
        d2 = datetime.strptime(dates[i], "%Y%m%d")
        if (d1 - d2).days <= 3:
            streak += 1
        else:
            break
    
    return streak

def get_streak_dates(code, history_type, streak_count):
    """取得連續買賣的日期清單"""
    history = load_history()
    key = f"{code}_{history_type}"
    
    if key not in history:
        return []
    
    dates = sorted(history[key]['dates'], reverse=True)[:streak_count]
    return [datetime.strptime(d, "%Y%m%d").strftime("%Y/%m/%d") for d in dates]

def format_number(n):
    """格式化數字"""
    abs_n = abs(n)
    sign = '-' if n < 0 else ''
    
    if abs_n >= 100000000:
        return f"{sign}{abs_n/100000000:.2f}億"
    elif abs_n >= 10000:
        return f"{sign}{abs_n/10000:.1f}萬"
    else:
        return f"{n:,}"

# ==================== API 函數 ====================

def fetch_twse_data(date_str):
    """獲取三大法人資料"""
    try:
        url = f"https://www.twse.com.tw/fund/T86?response=json&date={date_str}&selectType=ALL"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('stat') != 'OK' or not data.get('data'):
            return None, "非交易日或資料尚未更新"
        
        stocks = []
        for row in data['data']:
            if not row[0] or len(row[0].strip()) < 4:
                continue
            
            def parse_num(s):
                try:
                    return int(s.replace(',', ''))
                except:
                    return 0
            
            stocks.append({
                'code': row[0].strip(),
                'name': row[1].strip(),
                'foreign': parse_num(row[4]),
                'trust': parse_num(row[7]),
                'dealer': parse_num(row[10]) + parse_num(row[13]),
                'total': parse_num(row[14])
            })
        
        return stocks, None
    except Exception as e:
        return None, f"錯誤：{str(e)}"

def fetch_stock_price(stock_code):
    """獲取個股收盤資料"""
    try:
        url = "https://openapi.twse.com.tw/v1/opendata/t187ap14_L"
        response = requests.get(url, timeout=15)
        data = response.json()
        
        for item in data:
            if item.get('Code') == stock_code:
                return {
                    'code': item.get('Code'),
                    'name': item.get('Name'),
                    'close': float(item.get('Close', 0)),
                    'change': float(item.get('Change', 0)),
                    'volume': int(item.get('TradeVolume', 0))
                }
        return None
    except:
        return None

def fetch_institutional_trading(stock_code, date_str):
    """獲取三大法人買賣超"""
    try:
        url = f"https://www.twse.com.tw/fund/T86?response=json&date={date_str}&selectType=ALL"
        response = requests.get(url, timeout=15)
        data = response.json()
        
        if data.get('stat') != 'OK':
            return None
        
        for row in data.get('data', []):
            if row[0].strip() == stock_code:
                def parse_num(s):
                    try:
                        return int(s.replace(',', ''))
                    except:
                        return 0
                
                return {
                    'foreign': parse_num(row[4]),
                    'trust': parse_num(row[7]),
                    'dealer': parse_num(row[10]) + parse_num(row[13]),
                    'total': parse_num(row[14])
                }
        return None
    except:
        return None

def fetch_margin_trading(stock_code):
    """獲取信用交易資料"""
    try:
        url = "https://www.twse.com.tw/exchangeReport/MI_MARGN?response=json"
        response = requests.get(url, timeout=15)
        data = response.json()
        
        if data.get('stat') != 'OK':
            return None
        
        for row in data.get('data', []):
            if row[0].strip() == stock_code:
                def parse_num(s):
                    try:
                        return int(s.replace(',', ''))
                    except:
                        return 0
                
                return {
                    'margin_balance': parse_num(row[7]),
                    'short_balance': parse_num(row[13])
                }
        return None
    except:
        return None

# ==================== 主程式 ====================

# 標題和模式切換
col_title, col_mode = st.columns([3, 1])

with col_title:
    st.title("📈 台股籌碼分析系統")

with col_mode:
    st.write("")
    mode = st.radio(
        "模式",
        ["大盤追蹤", "個股分析"],
        horizontal=True,
        label_visibility="collapsed"
    )

st.markdown("---")

# ==================== 大盤追蹤模式 ====================

if mode == "大盤追蹤":
    st.subheader("📊 大盤法人動向追蹤")
    
    # 初始化 session_state
    if 'auto_loaded' not in st.session_state:
        st.session_state['auto_loaded'] = False
    
    # 控制列
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.info("💡 系統會自動載入過去 10 個交易日資料，計算連續買賣超趨勢")
    
    with col2:
        if st.button("📥 載入歷史資料", use_container_width=True):
            st.session_state['auto_loaded'] = True
            st.session_state['load_history'] = True
    
    with col3:
        if st.button("🔄 更新今日", type="primary", use_container_width=True):
            st.session_state['update_today'] = True
    
    # 自動載入歷史資料（首次進入）
    if not st.session_state['auto_loaded']:
        st.session_state['auto_loaded'] = True
        st.session_state['load_history'] = True
    
    # 載入歷史資料
    if st.session_state.get('load_history'):
        trading_days = get_trading_days(datetime.now(), 10)
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        all_data = {}
        for i, date_str in enumerate(trading_days):
            status_text.text(f"正在載入 {date_str[:4]}/{date_str[4:6]}/{date_str[6:8]} 的資料...")
            
            stocks, error = fetch_twse_data(date_str)
            if stocks:
                all_data[date_str] = stocks
            
            progress_bar.progress((i + 1) / len(trading_days))
        
        progress_bar.empty()
        status_text.empty()
        
        # 更新歷史紀錄
        for date_str, stocks in all_data.items():
            buy_stocks = [s for s in stocks if s['total'] > 0]
            sell_stocks = [s for s in stocks if s['total'] < 0]
            
            buy_top10 = sorted(buy_stocks, key=lambda x: x['total'], reverse=True)[:10]
            sell_top10 = sorted(sell_stocks, key=lambda x: x['total'])[:10]
            
            history = load_history()
            
            for stock in buy_top10:
                key = f"{stock['code']}_buy"
                if key not in history:
                    history[key] = {'name': stock['name'], 'dates': []}
                if date_str not in history[key]['dates']:
                    history[key]['dates'].append(date_str)
                    history[key]['dates'] = sorted(history[key]['dates'])[-60:]
            
            for stock in sell_top10:
                key = f"{stock['code']}_sell"
                if key not in history:
                    history[key] = {'name': stock['name'], 'dates': []}
                if date_str not in history[key]['dates']:
                    history[key]['dates'].append(date_str)
                    history[key]['dates'] = sorted(history[key]['dates'])[-60:]
            
            save_history(history)
        
        # 儲存最新一天的資料
        if all_data:
            latest_date = sorted(all_data.keys(), reverse=True)[0]
            latest_stocks = all_data[latest_date]
            
            buy_stocks = [s for s in latest_stocks if s['total'] > 0]
            sell_stocks = [s for s in latest_stocks if s['total'] < 0]
            
            buy_top10 = sorted(buy_stocks, key=lambda x: x['total'], reverse=True)[:10]
            sell_top10 = sorted(sell_stocks, key=lambda x: x['total'])[:10]
            
            # 計算連續天數
            for stock in buy_top10:
                stock['streak'] = calculate_streak(stock['code'], latest_date, 'buy')
            
            for stock in sell_top10:
                stock['streak'] = calculate_streak(stock['code'], latest_date, 'sell')
            
            st.session_state['buy_data'] = buy_top10
            st.session_state['sell_data'] = sell_top10
            st.session_state['date_key'] = latest_date
            st.session_state['data_loaded'] = True
        
        st.session_state['load_history'] = False
        st.success(f"✅ 已載入 {len(all_data)} 個交易日的資料")
        st.rerun()
    
    # 更新今日資料
    if st.session_state.get('update_today'):
        today = datetime.now().strftime("%Y%m%d")
        
        with st.spinner('正在更新今日資料...'):
            stocks, error = fetch_twse_data(today)
        
        if error:
            st.error(f"❌ {error}")
        else:
            buy_stocks = [s for s in stocks if s['total'] > 0]
            sell_stocks = [s for s in stocks if s['total'] < 0]
            
            buy_top10 = sorted(buy_stocks, key=lambda x: x['total'], reverse=True)[:10]
            sell_top10 = sorted(sell_stocks, key=lambda x: x['total'])[:10]
            
            # 更新歷史並計算連續天數
            history = load_history()
            
            for stock in buy_top10:
                key = f"{stock['code']}_buy"
                if key not in history:
                    history[key] = {'name': stock['name'], 'dates': []}
                if today not in history[key]['dates']:
                    history[key]['dates'].append(today)
                    history[key]['dates'] = sorted(history[key]['dates'])[-60:]
                stock['streak'] = calculate_streak(stock['code'], today, 'buy')
            
            for stock in sell_top10:
                key = f"{stock['code']}_sell"
                if key not in history:
                    history[key] = {'name': stock['name'], 'dates': []}
                if today not in history[key]['dates']:
                    history[key]['dates'].append(today)
                    history[key]['dates'] = sorted(history[key]['dates'])[-60:]
                stock['streak'] = calculate_streak(stock['code'], today, 'sell')
            
            save_history(history)
            
            st.session_state['buy_data'] = buy_top10
            st.session_state['sell_data'] = sell_top10
            st.session_state['date_key'] = today
            st.session_state['data_loaded'] = True
            st.success(f"✅ 今日資料更新成功")
        
        st.session_state['update_today'] = False
        st.rerun()
    
    # 顯示資料
    if st.session_state.get('data_loaded'):
        buy_data = st.session_state.get('buy_data', [])
        sell_data = st.session_state.get('sell_data', [])
        date_key = st.session_state.get('date_key', '')
        
        # 統計資訊
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("查詢日期", f"{date_key[:4]}/{date_key[4:6]}/{date_key[6:8]}")
        
        with col2:
            max_buy = max([s['streak'] for s in buy_data], default=0)
            st.metric("最高連買", f"{max_buy} 天")
        
        with col3:
            warn_count = len([s for s in buy_data if 3 <= s['streak'] < 5])
            st.metric("黃色注意", f"{warn_count} 檔")
        
        with col4:
            alert_count = len([s for s in buy_data if s['streak'] >= 5])
            st.metric("紅色警示", f"{alert_count} 檔")
        
        st.markdown("---")
        
        # 連續3天以上買超的股票提示
        streak_3_plus = [s for s in buy_data if s['streak'] >= 3]
        if streak_3_plus:
            st.warning(f"⚠️ 發現 {len(streak_3_plus)} 檔連續買超 3 天以上的股票")
            
            for stock in streak_3_plus:
                dates = get_streak_dates(stock['code'], 'buy', stock['streak'])
                with st.expander(f"📌 {stock['code']} {stock['name']} - 連買 {stock['streak']} 天"):
                    st.write(f"**連續買超日期：**")
                    st.write(" → ".join(dates))
                    st.write(f"**最新買超：** {format_number(stock['total'])} 張")
        
        # 買賣超表格
        tab1, tab2 = st.tabs(["▲ 買超 TOP 10", "▼ 賣超 TOP 10"])
        
        with tab1:
            st.subheader("▲ 三大法人合計買超 TOP 10")
            
            if buy_data:
                for i, stock in enumerate(buy_data, 1):
                    row_class = ""
                    badge_color = "#445566"
                    
                    if stock['streak'] >= 5:
                        row_class = "alert-row"
                        badge_color = "#ff4d4d"
                    elif stock['streak'] >= 3:
                        row_class = "warning-row"
                        badge_color = "#f5c518"
                    
                    with st.expander(
                        f"**{i:02d}. {stock['code']} {stock['name']}** | "
                        f"合計 {format_number(stock['total'])} 張 | "
                        f"連買 **{stock['streak']}** 天"
                    ):
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("外資", f"{format_number(stock['foreign'])} 張")
                        with col2:
                            st.metric("投信", f"{format_number(stock['trust'])} 張")
                        with col3:
                            st.metric("自營", f"{format_number(stock['dealer'])} 張")
                        with col4:
                            st.metric("連續天數", f"{stock['streak']} 天")
                        
                        if stock['streak'] >= 3:
                            dates = get_streak_dates(stock['code'], 'buy', stock['streak'])
                            st.info(f"📅 連續買超日期：{' → '.join(dates)}")
            else:
                st.info("本日無買超資料")
        
        with tab2:
            st.subheader("▼ 三大法人合計賣超 TOP 10")
            
            if sell_data:
                for i, stock in enumerate(sell_data, 1):
                    with st.expander(
                        f"**{i:02d}. {stock['code']} {stock['name']}** | "
                        f"合計 {format_number(stock['total'])} 張 | "
                        f"連賣 **{stock['streak']}** 天"
                    ):
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("外資", f"{format_number(stock['foreign'])} 張")
                        with col2:
                            st.metric("投信", f"{format_number(stock['trust'])} 張")
                        with col3:
                            st.metric("自營", f"{format_number(stock['dealer'])} 張")
                        with col4:
                            st.metric("連續天數", f"{stock['streak']} 天")
                        
                        if stock['streak'] >= 3:
                            dates = get_streak_dates(stock['code'], 'sell', stock['streak'])
                            st.info(f"📅 連續賣超日期：{' → '.join(dates)}")
            else:
                st.info("本日無賣超資料")
    
    else:
        st.info("👆 點擊「載入歷史資料」開始分析")

# ==================== 個股分析模式 ====================

else:
    st.subheader("🔍 個股多維度分析")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        stock_code = st.text_input(
            "輸入股票代號",
            value="2330",
            placeholder="例：2330"
        ).strip()
    
    with col2:
        query_date = st.date_input("查詢日期", value=datetime.now())
    
    with col3:
        st.write("")
        st.write("")
        analyze_btn = st.button("🔍 開始分析", type="primary", use_container_width=True)
    
    if analyze_btn and stock_code:
        date_str = query_date.strftime("%Y%m%d")
        
        with st.spinner('正在獲取資料...'):
            price_data = fetch_stock_price(stock_code)
            institutional_data = fetch_institutional_trading(stock_code, date_str)
            margin_data = fetch_margin_trading(stock_code)
        
        if not price_data:
            st.error(f"❌ 查無股票代號 {stock_code} 的資料")
        else:
            st.markdown(f"### {price_data['name']} ({stock_code})")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("收盤價", f"${price_data['close']:.2f}", f"{price_data['change']:+.2f}")
            
            with col2:
                st.metric("成交量", f"{price_data['volume']:,} 張")
            
            with col3:
                if institutional_data:
                    st.metric("法人買賣超", f"{institutional_data['total']:,} 張")
            
            with col4:
                if margin_data:
                    st.metric("融資餘額", f"{margin_data['margin_balance']:,} 張")
            
            st.markdown("---")
            
            tab1, tab2 = st.tabs(["📊 法人動向", "💳 信用交易"])
            
            with tab1:
                if institutional_data:
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("外資", f"{institutional_data['foreign']:,} 張")
                    with col2:
                        st.metric("投信", f"{institutional_data['trust']:,} 張")
                    with col3:
                        st.metric("自營", f"{institutional_data['dealer']:,} 張")
                    with col4:
                        st.metric("合計", f"{institutional_data['total']:,} 張")
                else:
                    st.info("📊 查無法人資料")
            
            with tab2:
                if margin_data:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("融資餘額", f"{margin_data['margin_balance']:,} 張")
                    with col2:
                        st.metric("融券餘額", f"{margin_data['short_balance']:,} 張")
                else:
                    st.info("📊 查無信用交易資料")

# 頁尾
st.markdown("---")
st.caption("📊 資料來源：證交所 T86 | ⚠️ 僅供參考，非投資建議")
