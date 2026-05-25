import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import json
from pathlib import Path

# 頁面設定
st.set_page_config(
    page_title="台股籌碼分析系統",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 優化配色方案 - 護眼舒適
st.markdown("""
<style>
    /* 主背景 */
    .main {
        background: linear-gradient(135deg, #1a1d29 0%, #2d3142 100%);
    }
    
    /* 卡片背景 */
    .metric-card {
        background: linear-gradient(135deg, #2d3142 0%, #3a3f5c 100%);
        border: 1px solid rgba(139, 166, 204, 0.2);
        border-radius: 12px;
        padding: 1.2rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    }
    
    /* 按鈕樣式 */
    .stButton>button {
        background: linear-gradient(135deg, #4a90e2, #5dade2);
        color: #ffffff;
        font-weight: 600;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 1.8rem;
        box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #5dade2, #4a90e2);
        box-shadow: 0 6px 16px rgba(74, 144, 226, 0.4);
        transform: translateY(-2px);
    }
    
    /* 表格樣式 */
    .dataframe {
        background: #2d3142 !important;
        border-radius: 10px !important;
        overflow: hidden;
    }
    
    .dataframe thead th {
        background: linear-gradient(135deg, #3a3f5c, #4a5170) !important;
        color: #e8eaf6 !important;
        font-weight: 600 !important;
        padding: 1rem !important;
        border: none !important;
        text-align: center !important;
    }
    
    .dataframe tbody td {
        background: #2d3142 !important;
        color: #c5cae9 !important;
        padding: 0.9rem !important;
        border-bottom: 1px solid rgba(139, 166, 204, 0.1) !important;
        text-align: center !important;
    }
    
    .dataframe tbody tr:nth-child(even) td {
        background: #3a3f5c !important;
    }
    
    .dataframe tbody tr:hover td {
        background: #4a5170 !important;
        transition: all 0.2s ease;
    }
    
    /* 警示行樣式 */
    .warning-row {
        background: linear-gradient(90deg, rgba(255, 193, 7, 0.15), transparent) !important;
        border-left: 4px solid #ffc107 !important;
    }
    
    .alert-row {
        background: linear-gradient(90deg, rgba(244, 67, 54, 0.2), transparent) !important;
        border-left: 4px solid #f44336 !important;
        animation: pulse-alert 2s ease-in-out infinite;
    }
    
    @keyframes pulse-alert {
        0%, 100% { 
            background: linear-gradient(90deg, rgba(244, 67, 54, 0.2), transparent) !important;
        }
        50% { 
            background: linear-gradient(90deg, rgba(244, 67, 54, 0.3), transparent) !important;
        }
    }
    
    /* 標籤顏色 */
    .positive {
        color: #66bb6a !important;
        font-weight: 600;
    }
    
    .negative {
        color: #ef5350 !important;
        font-weight: 600;
    }
    
    .neutral {
        color: #8ba6cc !important;
    }
    
    /* 統計卡片 */
    .stat-value {
        font-size: 2rem;
        font-weight: 700;
        margin: 0.5rem 0;
    }
    
    .stat-label {
        font-size: 0.9rem;
        color: #8ba6cc;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* 資訊框 */
    .stAlert {
        background: rgba(74, 144, 226, 0.1) !important;
        border-left: 4px solid #4a90e2 !important;
        color: #b3d9ff !important;
        border-radius: 8px;
    }
    
    /* Tab 樣式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: #2d3142;
        padding: 0.5rem;
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: #8ba6cc;
        border-radius: 8px;
        padding: 0.8rem 1.5rem;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #4a90e2, #5dade2);
        color: white;
    }
    
    /* 進度條 */
    .stProgress > div > div {
        background: linear-gradient(90deg, #4a90e2, #5dade2);
    }
    
    /* 標題 */
    h1, h2, h3 {
        color: #e8eaf6 !important;
    }
    
    /* 表格內的徽章 */
    .badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    .badge-normal {
        background: rgba(139, 166, 204, 0.2);
        color: #8ba6cc;
    }
    
    .badge-warning {
        background: rgba(255, 193, 7, 0.2);
        color: #ffc107;
        border: 1px solid rgba(255, 193, 7, 0.3);
    }
    
    .badge-alert {
        background: rgba(244, 67, 54, 0.2);
        color: #f44336;
        border: 1px solid rgba(244, 67, 54, 0.4);
        animation: badge-pulse 2s ease-in-out infinite;
    }
    
    @keyframes badge-pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
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
        if current.weekday() < 5:
            trading_days.append(current.strftime("%Y%m%d"))
        current -= timedelta(days=1)
    
    return trading_days

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

def calculate_streak(code, date_key, history_type):
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
    history = load_history()
    key = f"{code}_{history_type}"
    
    if key not in history:
        return []
    
    dates = sorted(history[key]['dates'], reverse=True)[:streak_count]
    return [datetime.strptime(d, "%Y%m%d").strftime("%Y/%m/%d") for d in dates]

def format_number(n):
    abs_n = abs(n)
    sign = '-' if n < 0 else ''
    
    if abs_n >= 100000000:
        return f"{sign}{abs_n/100000000:.2f}億"
    elif abs_n >= 10000:
        return f"{sign}{abs_n/10000:.1f}萬"
    else:
        return f"{n:,}"

def style_number(n):
    """數字加上顏色樣式"""
    if n > 0:
        return f'<span class="positive">+{format_number(n)}</span>'
    elif n < 0:
        return f'<span class="negative">{format_number(n)}</span>'
    else:
        return f'<span class="neutral">0</span>'

def fetch_twse_data(date_str):
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
    
    if 'auto_loaded' not in st.session_state:
        st.session_state['auto_loaded'] = False
    
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
    
    # 自動載入
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
        
        if all_data:
            latest_date = sorted(all_data.keys(), reverse=True)[0]
            latest_stocks = all_data[latest_date]
            
            buy_stocks = [s for s in latest_stocks if s['total'] > 0]
            sell_stocks = [s for s in latest_stocks if s['total'] < 0]
            
            buy_top10 = sorted(buy_stocks, key=lambda x: x['total'], reverse=True)[:10]
            sell_top10 = sorted(sell_stocks, key=lambda x: x['total'])[:10]
            
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
    
    # 更新今日
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
            st.markdown(f"""
            <div class="metric-card">
                <div class="stat-label">查詢日期</div>
                <div class="stat-value" style="color: #5dade2;">{date_key[:4]}/{date_key[4:6]}/{date_key[6:8]}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            max_buy = max([s['streak'] for s in buy_data], default=0)
            color = "#f44336" if max_buy >= 5 else "#ffc107" if max_buy >= 3 else "#5dade2"
            st.markdown(f"""
            <div class="metric-card">
                <div class="stat-label">最高連買</div>
                <div class="stat-value" style="color: {color};">{max_buy} 天</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            warn_count = len([s for s in buy_data if 3 <= s['streak'] < 5])
            st.markdown(f"""
            <div class="metric-card">
                <div class="stat-label">黃色注意</div>
                <div class="stat-value" style="color: #ffc107;">{warn_count} 檔</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            alert_count = len([s for s in buy_data if s['streak'] >= 5])
            st.markdown(f"""
            <div class="metric-card">
                <div class="stat-label">紅色警示</div>
                <div class="stat-value" style="color: #f44336;">{alert_count} 檔</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 連續買超提示
        streak_3_plus = [s for s in buy_data if s['streak'] >= 3]
        if streak_3_plus:
            st.warning(f"⚠️ 發現 {len(streak_3_plus)} 檔連續買超 3 天以上的股票")
            for stock in streak_3_plus:
                dates = get_streak_dates(stock['code'], 'buy', stock['streak'])
                st.info(f"📌 **{stock['code']} {stock['name']}** - 連買 **{stock['streak']}** 天  \n連續日期：{' → '.join(dates)}")
        
        # 表格顯示
        tab1, tab2 = st.tabs(["▲ 買超 TOP 10", "▼ 賣超 TOP 10"])
        
        with tab1:
            st.subheader("▲ 三大法人合計買超 TOP 10")
            
            if buy_data:
                # 建立表格資料
                df_data = []
                for i, stock in enumerate(buy_data, 1):
                    # 連續天數徽章
                    if stock['streak'] >= 5:
                        badge = f'<span class="badge badge-alert">{stock["streak"]} 天</span>'
                    elif stock['streak'] >= 3:
                        badge = f'<span class="badge badge-warning">{stock["streak"]} 天</span>'
                    else:
                        badge = f'<span class="badge badge-normal">{stock["streak"]} 天</span>'
                    
                    df_data.append({
                        '排名': f'{i:02d}',
                        '代號': stock['code'],
                        '名稱': stock['name'],
                        '外資 (合計)': style_number(stock['foreign']),
                        '投信 (合計)': style_number(stock['trust']),
                        '自營 (合計)': style_number(stock['dealer']),
                        '合計 (張)': style_number(stock['total']),
                        '連買天數': badge
                    })
                
                df = pd.DataFrame(df_data)
                
                # 顯示表格
                st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)
                
                st.caption("💡 註：外資、投信、自營皆為當日合計數值，不包含分點明細")
            else:
                st.info("本日無買超資料")
        
        with tab2:
            st.subheader("▼ 三大法人合計賣超 TOP 10")
            
            if sell_data:
                df_data = []
                for i, stock in enumerate(sell_data, 1):
                    if stock['streak'] >= 5:
                        badge = f'<span class="badge badge-alert">{stock["streak"]} 天</span>'
                    elif stock['streak'] >= 3:
                        badge = f'<span class="badge badge-warning">{stock["streak"]} 天</span>'
                    else:
                        badge = f'<span class="badge badge-normal">{stock["streak"]} 天</span>'
                    
                    df_data.append({
                        '排名': f'{i:02d}',
                        '代號': stock['code'],
                        '名稱': stock['name'],
                        '外資 (合計)': style_number(stock['foreign']),
                        '投信 (合計)': style_number(stock['trust']),
                        '自營 (合計)': style_number(stock['dealer']),
                        '合計 (張)': style_number(stock['total']),
                        '連賣天數': badge
                    })
                
                df = pd.DataFrame(df_data)
                st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)
                
                st.caption("💡 註：外資、投信、自營皆為當日合計數值，不包含分點明細")
            else:
                st.info("本日無賣超資料")
    
    else:
        st.info("👆 點擊「載入歷史資料」開始分析")

# ==================== 個股分析模式 ====================

else:
    st.subheader("🔍 個股分析")
    st.info("個股分析功能開發中...")

st.markdown("---")
st.caption("📊 資料來源：證交所 T86（三大法人合計數） | ⚠️ 僅供參考，非投資建議")
