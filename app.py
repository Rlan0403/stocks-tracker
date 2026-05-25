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

# 優化配色 - 響應式設計
st.markdown("""
<style>
    /* 響應式容器 */
    .main .block-container {
        max-width: 1200px;
        padding: 1rem 2rem;
    }
    
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1rem;
        }
    }
    
    /* 主背景 - 淺灰白色 */
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
    }
    
    /* 標題 - 深色字體 */
    h1, h2, h3, h4 {
        color: #2c3e50 !important;
        font-weight: 700 !important;
    }
    
    h1 {
        font-size: 2rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    @media (max-width: 768px) {
        h1 {
            font-size: 1.5rem !important;
        }
    }
    
    /* 統計卡片 */
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border: 1px solid #dee2e6;
        border-radius: 12px;
        padding: 1.2rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
        margin-bottom: 1rem;
    }
    
    .stat-label {
        font-size: 0.85rem;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }
    
    .stat-value {
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
    }
    
    @media (max-width: 768px) {
        .stat-value {
            font-size: 1.4rem;
        }
    }
    
    /* 按鈕樣式 - 平均寬度 */
    .stButton {
        width: 100%;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #4a90e2, #357abd);
        color: #ffffff;
        font-weight: 600;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 1.5rem;
        width: 100%;
        box-shadow: 0 2px 8px rgba(74, 144, 226, 0.3);
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #357abd, #2868a8);
        box-shadow: 0 4px 12px rgba(74, 144, 226, 0.4);
        transform: translateY(-2px);
    }
    
    /* 表格樣式 - 淺色背景 */
    table {
        width: 100%;
        background: #ffffff;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        border-collapse: separate;
        border-spacing: 0;
    }
    
    thead th {
        background: linear-gradient(135deg, #e9ecef, #dee2e6);
        color: #2c3e50;
        font-weight: 700;
        padding: 1rem 0.75rem;
        text-align: center;
        border: none;
        font-size: 0.9rem;
    }
    
    @media (max-width: 768px) {
        thead th {
            padding: 0.75rem 0.5rem;
            font-size: 0.75rem;
        }
    }
    
    tbody td {
        background: #ffffff;
        color: #495057;
        padding: 0.9rem 0.75rem;
        text-align: center;
        border-bottom: 1px solid #f1f3f5;
        font-size: 0.9rem;
    }
    
    @media (max-width: 768px) {
        tbody td {
            padding: 0.7rem 0.5rem;
            font-size: 0.8rem;
        }
    }
    
    tbody tr:nth-child(even) td {
        background: #f8f9fa;
    }
    
    tbody tr:hover td {
        background: #e9ecef;
        transition: all 0.2s ease;
    }
    
    /* 警示行樣式 */
    .warning-row td {
        background: linear-gradient(90deg, rgba(255, 193, 7, 0.2), #ffffff) !important;
        border-left: 4px solid #ffc107 !important;
    }
    
    .alert-row td {
        background: linear-gradient(90deg, rgba(220, 53, 69, 0.2), #ffffff) !important;
        border-left: 4px solid #dc3545 !important;
        animation: pulse-alert 2s ease-in-out infinite;
    }
    
    @keyframes pulse-alert {
        0%, 100% { 
            background: linear-gradient(90deg, rgba(220, 53, 69, 0.2), #ffffff) !important;
        }
        50% { 
            background: linear-gradient(90deg, rgba(220, 53, 69, 0.3), #ffffff) !important;
        }
    }
    
    /* 數字顏色 */
    .positive {
        color: #28a745 !important;
        font-weight: 700;
    }
    
    .negative {
        color: #dc3545 !important;
        font-weight: 700;
    }
    
    .neutral {
        color: #6c757d !important;
    }
    
    /* 徽章 */
    .badge {
        display: inline-block;
        padding: 0.35rem 0.75rem;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 700;
        white-space: nowrap;
    }
    
    @media (max-width: 768px) {
        .badge {
            padding: 0.25rem 0.5rem;
            font-size: 0.7rem;
        }
    }
    
    .badge-normal {
        background: #e9ecef;
        color: #6c757d;
    }
    
    .badge-warning {
        background: #fff3cd;
        color: #856404;
        border: 1px solid #ffc107;
    }
    
    .badge-alert {
        background: #f8d7da;
        color: #721c24;
        border: 1px solid #dc3545;
        animation: badge-pulse 2s ease-in-out infinite;
    }
    
    @keyframes badge-pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    /* 資訊框 */
    .stAlert {
        background: #d1ecf1 !important;
        border-left: 4px solid #17a2b8 !important;
        color: #0c5460 !important;
        border-radius: 8px;
    }
    
    /* Tab 樣式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: #ffffff;
        padding: 0.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: #6c757d;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
    }
    
    @media (max-width: 768px) {
        .stTabs [data-baseweb="tab"] {
            padding: 0.6rem 1rem;
            font-size: 0.85rem;
        }
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #4a90e2, #357abd);
        color: white;
    }
    
    /* 進度條 */
    .stProgress > div > div {
        background: linear-gradient(90deg, #4a90e2, #357abd);
    }
    
    /* 輸入框 */
    .stTextInput > div > div > input {
        background: #ffffff;
        border: 2px solid #dee2e6;
        border-radius: 8px;
        color: #495057;
        font-size: 1rem;
        padding: 0.75rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #4a90e2;
        box-shadow: 0 0 0 0.2rem rgba(74, 144, 226, 0.25);
    }
    
    /* 日期選擇器 */
    .stDateInput > div > div > input {
        background: #ffffff;
        border: 2px solid #dee2e6;
        border-radius: 8px;
    }
    
    /* Radio 按鈕組 */
    .stRadio > div {
        background: #ffffff;
        padding: 0.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
    }
    
    .stRadio > div > label > div[data-testid="stMarkdownContainer"] > p {
        color: #2c3e50;
        font-weight: 600;
    }
    
    /* 表格容器 */
    .table-container {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        margin: 1rem 0;
    }
    
    /* 響應式表格 */
    @media (max-width: 768px) {
        table {
            font-size: 0.75rem;
        }
        
        .table-container {
            margin: 0.5rem -1rem;
            padding: 0 1rem;
        }
    }
    
    /* Metric 組件樣式 */
    [data-testid="stMetricValue"] {
        color: #2c3e50;
        font-size: 1.8rem;
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 1rem;
    }
    
    @media (max-width: 768px) {
        [data-testid="stMetricValue"] {
            font-size: 1.3rem;
        }
        
        [data-testid="stMetricDelta"] {
            font-size: 0.85rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# 資料目錄
DATA_DIR = Path("data_storage")
DATA_DIR.mkdir(exist_ok=True)
HISTORY_FILE = DATA_DIR / "history.json"

# ==================== 工具函數 ====================

def get_trading_days(end_date, num_days=10):
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
    return [datetime.strptime(d, "%Y%m%d").strftime("%m/%d") for d in dates]

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

def fetch_stock_price(stock_code):
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
    
    if 'auto_loaded' not in st.session_state:
        st.session_state['auto_loaded'] = False
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 載入歷史資料", use_container_width=True):
            st.session_state['auto_loaded'] = True
            st.session_state['load_history'] = True
    
    with col2:
        if st.button("🔄 更新今日", type="primary", use_container_width=True):
            st.session_state['update_today'] = True
    
    with col3:
        st.info("過去10日資料")
    
    # 自動載入
    if not st.session_state['auto_loaded']:
        st.session_state['auto_loaded'] = True
        st.session_state['load_history'] = True
    
    # 載入歷史
    if st.session_state.get('load_history'):
        trading_days = get_trading_days(datetime.now(), 10)
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        all_data = {}
        for i, date_str in enumerate(trading_days):
            status_text.text(f"載入 {date_str[:4]}/{date_str[4:6]}/{date_str[6:8]}")
            
            stocks, error = fetch_twse_data(date_str)
            if stocks:
                all_data[date_str] = stocks
            
            progress_bar.progress((i + 1) / len(trading_days))
        
        progress_bar.empty()
        status_text.empty()
        
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
        st.success(f"✅ 已載入 {len(all_data)} 個交易日")
        st.rerun()
    
    # 更新今日
    if st.session_state.get('update_today'):
        today = datetime.now().strftime("%Y%m%d")
        
        with st.spinner('更新中...'):
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
            st.success("✅ 更新成功")
        
        st.session_state['update_today'] = False
        st.rerun()
    
    # 顯示資料
    if st.session_state.get('data_loaded'):
        buy_data = st.session_state.get('buy_data', [])
        sell_data = st.session_state.get('sell_data', [])
        date_key = st.session_state.get('date_key', '')
        
        # 統計卡片
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="stat-label">查詢日期</div>
                <div class="stat-value" style="color: #4a90e2;">{date_key[:4]}/{date_key[4:6]}/{date_key[6:8]}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            max_buy = max([s['streak'] for s in buy_data], default=0)
            color = "#dc3545" if max_buy >= 5 else "#ffc107" if max_buy >= 3 else "#4a90e2"
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
                <div class="stat-value" style="color: #dc3545;">{alert_count} 檔</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 連續買超提示
        streak_3_plus = [s for s in buy_data if s['streak'] >= 3]
        if streak_3_plus:
            st.warning(f"⚠️ 發現 {len(streak_3_plus)} 檔連續買超 ≥3 天")
            for stock in streak_3_plus:
                dates = get_streak_dates(stock['code'], 'buy', stock['streak'])
                st.info(f"📌 **{stock['code']} {stock['name']}** 連買 **{stock['streak']}** 天 ({' → '.join(dates)})")
        
        # 表格
        tab1, tab2 = st.tabs(["▲ 買超 TOP 10", "▼ 賣超 TOP 10"])
        
        with tab1:
            st.subheader("三大法人合計買超 TOP 10")
            
            if buy_data:
                html = '<div class="table-container"><table>'
                html += '<thead><tr><th>排名</th><th>代號</th><th>名稱</th><th>外資</th><th>投信</th><th>自營</th><th>合計</th><th>連買</th></tr></thead>'
                html += '<tbody>'
                
                for i, stock in enumerate(buy_data, 1):
                    row_class = ''
                    if stock['streak'] >= 5:
                        row_class = 'alert-row'
                        badge = f'<span class="badge badge-alert">{stock["streak"]}天</span>'
                    elif stock['streak'] >= 3:
                        row_class = 'warning-row'
                        badge = f'<span class="badge badge-warning">{stock["streak"]}天</span>'
                    else:
                        badge = f'<span class="badge badge-normal">{stock["streak"]}天</span>'
                    
                    html += f'<tr class="{row_class}">'
                    html += f'<td>{i:02d}</td>'
                    html += f'<td><strong>{stock["code"]}</strong></td>'
                    html += f'<td>{stock["name"]}</td>'
                    html += f'<td>{style_number(stock["foreign"])}</td>'
                    html += f'<td>{style_number(stock["trust"])}</td>'
                    html += f'<td>{style_number(stock["dealer"])}</td>'
                    html += f'<td>{style_number(stock["total"])}</td>'
                    html += f'<td>{badge}</td>'
                    html += '</tr>'
                
                html += '</tbody></table></div>'
                st.markdown(html, unsafe_allow_html=True)
                st.caption("💡 外資、投信、自營為當日合計數")
            else:
                st.info("本日無買超資料")
        
        with tab2:
            st.subheader("三大法人合計賣超 TOP 10")
            
            if sell_data:
                html = '<div class="table-container"><table>'
                html += '<thead><tr><th>排名</th><th>代號</th><th>名稱</th><th>外資</th><th>投信</th><th>自營</th><th>合計</th><th>連賣</th></tr></thead>'
                html += '<tbody>'
                
                for i, stock in enumerate(sell_data, 1):
                    row_class = ''
                    if stock['streak'] >= 5:
                        row_class = 'alert-row'
                        badge = f'<span class="badge badge-alert">{stock["streak"]}天</span>'
                    elif stock['streak'] >= 3:
                        row_class = 'warning-row'
                        badge = f'<span class="badge badge-warning">{stock["streak"]}天</span>'
                    else:
                        badge = f'<span class="badge badge-normal">{stock["streak"]}天</span>'
                    
                    html += f'<tr class="{row_class}">'
                    html += f'<td>{i:02d}</td>'
                    html += f'<td><strong>{stock["code"]}</strong></td>'
                    html += f'<td>{stock["name"]}</td>'
                    html += f'<td>{style_number(stock["foreign"])}</td>'
                    html += f'<td>{style_number(stock["trust"])}</td>'
                    html += f'<td>{style_number(stock["dealer"])}</td>'
                    html += f'<td>{style_number(stock["total"])}</td>'
                    html += f'<td>{badge}</td>'
                    html += '</tr>'
                
                html += '</tbody></table></div>'
                st.markdown(html, unsafe_allow_html=True)
                st.caption("💡 外資、投信、自營為當日合計數")
            else:
                st.info("本日無賣超資料")
    
    else:
        st.info("👆 系統會自動載入資料")

# ==================== 個股分析模式 ====================

else:
    st.subheader("🔍 個股分析")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        stock_code = st.text_input(
            "股票代號",
            value="2330",
            placeholder="例：2330"
        ).strip()
    
    with col2:
        query_date = st.date_input("查詢日期", value=datetime.now())
    
    with col3:
        st.write("")
        st.write("")
        analyze_btn = st.button("🔍 分析", type="primary", use_container_width=True)
    
    if analyze_btn and stock_code:
        date_str = query_date.strftime("%Y%m%d")
        
        with st.spinner('查詢中...'):
            price_data = fetch_stock_price(stock_code)
            institutional_data = fetch_institutional_trading(stock_code, date_str)
            margin_data = fetch_margin_trading(stock_code)
        
        if not price_data:
            st.error(f"❌ 查無 {stock_code}")
        else:
            st.markdown(f"### {price_data['name']} ({stock_code})")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("收盤價", f"${price_data['close']:.2f}", f"{price_data['change']:+.2f}")
            
            with col2:
                st.metric("成交量", f"{price_data['volume']:,} 張")
            
            with col3:
                if institutional_data:
                    st.metric("法人", f"{institutional_data['total']:,} 張")
            
            with col4:
                if margin_data:
                    st.metric("融資", f"{margin_data['margin_balance']:,} 張")
            
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
                    st.info("查無法人資料")
            
            with tab2:
                if margin_data:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("融資餘額", f"{margin_data['margin_balance']:,} 張")
                    with col2:
                        st.metric("融券餘額", f"{margin_data['short_balance']:,} 張")
                else:
                    st.info("查無信用交易資料")

st.markdown("---")
st.caption("📊 資料來源：證交所 | ⚠️ 僅供參考，非投資建議")
