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
    
    /* 主背景 - 單色 */
    .main {
        background: #f5f7fa;
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
        background: #ffffff;
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
        background: #4a90e2;
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
        background: #357abd;
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
        background: #e9ecef;
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
        background: #e9ecef;
    }
    
    tbody tr:hover td {
        background: #dee2e6;
        transition: all 0.2s ease;
    }
    
    /* 警示行樣式 - 整列統一色 */
    .warning-row td {
        background: #fff3cd !important;
        border-left: 4px solid #ffc107 !important;
    }
    
    .alert-row td {
        background: #f8d7da !important;
        border-left: 4px solid #dc3545 !important;
        animation: pulse-alert 2s ease-in-out infinite;
    }
    
    @keyframes pulse-alert {
        0%, 100% { 
            background: #f8d7da !important;
        }
        50% { 
            background: #f5c2c7 !important;
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
        background: #4a90e2;
        color: white;
    }
    
    /* 進度條 */
    .stProgress > div > div {
        background: #4a90e2;
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



# ==================== API 函數 ====================

def fetch_twse_data(date_str):
    """大盤法人資料"""
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
    """個股收盤價 - OpenAPI t187ap14_L"""
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
    """個股三大法人買賣超"""
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
    """信用交易 - 融資融券"""
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
                    'margin_buy': parse_num(row[2]),
                    'margin_sell': parse_num(row[3]),
                    'margin_balance': parse_num(row[7]),
                    'short_sell': parse_num(row[8]),
                    'short_cover': parse_num(row[9]),
                    'short_balance': parse_num(row[13])
                }
        return None
    except:
        return None

def fetch_shareholding_distribution(stock_code):
    """集保股權分散表 - TDCC OpenAPI"""
    try:
        url = "https://www.tdcc.com.tw/opendata/getOD.ashx?id=1-5"
        response = requests.get(url, timeout=15)
        data = response.json()
        
        for item in data:
            if item.get('證券代號') == stock_code:
                def parse_int(s):
                    try:
                        return int(s.replace(',', ''))
                    except:
                        return 0
                
                return {
                    'date': item.get('資料日期'),
                    'total_holders': parse_int(item.get('持股人數', 0)),
                    'over_1000': parse_int(item.get('持股1,000張以上人數', 0)),
                    'under_10': parse_int(item.get('持股10張以下人數', 0)),
                    'over_1000_shares': parse_int(item.get('持股1,000張以上股數', 0)),
                    'under_10_shares': parse_int(item.get('持股10張以下股數', 0))
                }
        return None
    except:
        return None

def fetch_monthly_revenue(stock_code):
    """每月營收 - OpenAPI t187ap05_P"""
    try:
        url = "https://openapi.twse.com.tw/v1/opendata/t187ap05_P"
        response = requests.get(url, timeout=15)
        data = response.json()
        
        revenue_data = []
        for item in data:
            if item.get('公司代號') == stock_code:
                try:
                    revenue_data.append({
                        'month': item.get('資料年月'),
                        'revenue': float(item.get('當月營收', 0)),
                        'yoy': float(item.get('去年同期增減(%)', 0)),
                        'mom': float(item.get('上月比較增減(%)', 0))
                    })
                except:
                    pass
        
        return sorted(revenue_data, key=lambda x: x['month'], reverse=True)[:6]
    except:
        return []

def fetch_director_shareholding(stock_code):
    """董監持股 - OpenAPI t187ap12_L"""
    try:
        url = "https://openapi.twse.com.tw/v1/opendata/t187ap12_L"
        response = requests.get(url, timeout=15)
        data = response.json()
        
        for item in data:
            if item.get('公司代號') == stock_code:
                try:
                    return {
                        'directors_shares': float(item.get('董監持股', 0)),
                        'pledge_shares': float(item.get('質押股數', 0)),
                        'pledge_ratio': float(item.get('質押比例', 0))
                    }
                except:
                    pass
        return None
    except:
        return None



# ==================== 分析函數（按規格書實作）====================

def analyze_short_term_institutional(institutional, margin, volume):
    """短線法人多空角力分析"""
    signals = []
    score = 0
    
    if not institutional or not margin:
        return None
    
    # 法人籌碼集中度
    if volume > 0:
        concentration = (abs(institutional['foreign']) + abs(institutional['trust']) + abs(institutional['dealer'])) / volume * 100
        
        if concentration > 10:
            signals.append(f"✅ 法人籌碼集中度 {concentration:.1f}% (>10%)")
            score += 2
        else:
            signals.append(f"📊 法人籌碼集中度 {concentration:.1f}%")
    
    # 融資變化
    margin_change = margin['margin_buy'] - margin['margin_sell']
    
    if margin_change < -500 and institutional['total'] > 0:
        signals.append("✅ 融資大減 + 法人買超（籌碼乾淨）")
        score += 3
    elif margin_change < 0 and institutional['total'] > 0:
        signals.append("🟢 融資減少 + 法人買超")
        score += 1
    elif margin_change > 500 and institutional['total'] < 0:
        signals.append("❌ 融資暴增 + 法人賣超（散戶追高）")
        score -= 3
    
    # 借券賣出
    if margin['short_balance'] > margin['margin_balance'] * 0.3:
        signals.append("⚠️ 借券餘額偏高（空方力道強）")
        score -= 1
    
    return {
        'score': score,
        'signals': signals,
        'rating': '強多' if score >= 4 else '偏多' if score >= 2 else '中性' if score >= -1 else '偏空' if score >= -3 else '強空'
    }

def analyze_long_term_accumulation(shareholding):
    """中長線大戶吸籌分析"""
    if not shareholding:
        return None
    
    signals = []
    
    # 計算比例
    total = shareholding['total_holders']
    if total == 0:
        return None
    
    big_holder_ratio = (shareholding['over_1000'] / total) * 100
    retail_ratio = (shareholding['under_10'] / total) * 100
    
    if big_holder_ratio > 5:
        signals.append(f"✅ 千張大戶比例 {big_holder_ratio:.2f}% (高籌碼集中)")
        
    if retail_ratio < 40:
        signals.append(f"✅ 散戶比例 {retail_ratio:.2f}% (低散戶持股)")
    
    return {
        'big_holder_ratio': round(big_holder_ratio, 2),
        'retail_ratio': round(retail_ratio, 2),
        'big_holder_count': shareholding['over_1000'],
        'retail_count': shareholding['under_10'],
        'signals': signals,
        'date': shareholding['date']
    }

def check_revenue_quality(revenue_data):
    """基本面營收檢查"""
    if not revenue_data or len(revenue_data) < 2:
        return None
    
    signals = []
    latest_yoy = revenue_data[0]['yoy']
    
    # 連續兩個月 YoY > 20%
    if len(revenue_data) >= 2:
        if revenue_data[0]['yoy'] > 20 and revenue_data[1]['yoy'] > 20:
            signals.append(f"✅ 連續 2 月 YoY > 20% ({revenue_data[0]['yoy']:.1f}%, {revenue_data[1]['yoy']:.1f}%)")
            quality = 'excellent'
        elif latest_yoy > 20:
            signals.append(f"🟢 最新 YoY {latest_yoy:.1f}% (>20%)")
            quality = 'good'
        elif latest_yoy > 0:
            signals.append(f"📊 YoY {latest_yoy:.1f}% (正成長)")
            quality = 'normal'
        else:
            signals.append(f"⚠️ YoY {latest_yoy:.1f}% (衰退)")
            quality = 'poor'
    
    return {
        'quality': quality,
        'latest_yoy': latest_yoy,
        'signals': signals
    }

def check_director_risk(director_data):
    """董監風險檢查"""
    if not director_data:
        return None
    
    pledge_ratio = director_data['pledge_ratio']
    
    if pledge_ratio > 50:
        return {
            'level': 'high',
            'ratio': pledge_ratio,
            'message': f"🚨 高風險：董監質押率 {pledge_ratio:.1f}% (>50%)",
            'color': 'red'
        }
    elif pledge_ratio > 30:
        return {
            'level': 'medium',
            'ratio': pledge_ratio,
            'message': f"⚠️ 中度風險：董監質押率 {pledge_ratio:.1f}%",
            'color': 'orange'
        }
    else:
        return {
            'level': 'low',
            'ratio': pledge_ratio,
            'message': f"✅ 安全：董監質押率 {pledge_ratio:.1f}%",
            'color': 'green'
        }



# ==================== 圖表函數 ====================

def create_institutional_chart(history_data):
    """法人買賣超圖表"""
    if not history_data:
        return None
    
    df = pd.DataFrame(history_data)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(name='外資', x=df['date'], y=df['foreign'], marker_color='#4a90e2'))
    fig.add_trace(go.Bar(name='投信', x=df['date'], y=df['trust'], marker_color='#f5c518'))
    fig.add_trace(go.Bar(name='自營', x=df['date'], y=df['dealer'], marker_color='#00e882'))
    
    fig.update_layout(
        title='三大法人近期買賣超（張）',
        barmode='group',
        template='plotly_white',
        height=400,
        xaxis_title='日期',
        yaxis_title='張數',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig

def create_margin_chart(history_data):
    """融資融券變化圖"""
    if not history_data:
        return None
    
    df = pd.DataFrame(history_data)
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Scatter(name='融資餘額', x=df['date'], y=df['margin_balance'], 
                  line=dict(color='#28a745', width=2)),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Scatter(name='融券餘額', x=df['date'], y=df['short_balance'],
                  line=dict(color='#dc3545', width=2)),
        secondary_y=True
    )
    
    fig.update_layout(
        title='信用交易餘額變化',
        template='plotly_white',
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    fig.update_yaxes(title_text="融資餘額（張）", secondary_y=False)
    fig.update_yaxes(title_text="融券餘額（張）", secondary_y=True)
    
    return fig

def create_revenue_chart(revenue_data):
    """營收圖表"""
    if not revenue_data:
        return None
    
    df = pd.DataFrame(revenue_data)
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Bar(name='月營收', x=df['month'], y=df['revenue'], marker_color='#4a90e2'),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Scatter(name='YoY%', x=df['month'], y=df['yoy'],
                  line=dict(color='#dc3545', width=3), mode='lines+markers'),
        secondary_y=True
    )
    
    fig.update_layout(
        title='月營收與年增率',
        template='plotly_white',
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    fig.update_yaxes(title_text="營收（千元）", secondary_y=False)
    fig.update_yaxes(title_text="YoY %", secondary_y=True)
    
    return fig



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



# ==================== 個股分析模式（完整實作）====================

else:
    st.subheader("🔍 個股籌碼與基本面分析")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        stock_code = st.text_input("股票代號", value="2330", placeholder="例：2330").strip()
    
    with col2:
        query_date = st.date_input("查詢日期", value=datetime.now())
    
    with col3:
        st.write("")
        st.write("")
        analyze_btn = st.button("🔍 開始分析", type="primary", use_container_width=True)
    
    if analyze_btn and stock_code:
        date_str = query_date.strftime("%Y%m%d")
        
        with st.spinner('正在獲取資料...'):
            # 獲取所有資料
            price_data = fetch_stock_price(stock_code)
            institutional_data = fetch_institutional_trading(stock_code, date_str)
            margin_data = fetch_margin_trading(stock_code)
            shareholding_data = fetch_shareholding_distribution(stock_code)
            revenue_data = fetch_monthly_revenue(stock_code)
            director_data = fetch_director_shareholding(stock_code)
        
        if not price_data:
            st.error(f"❌ 查無股票代號 {stock_code}")
        else:
            # 基本資訊
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
            
            # 警示看板
            st.subheader("⚠️ 智慧警示系統")
            
            col_alert1, col_alert2, col_alert3 = st.columns(3)
            
            with col_alert1:
                # 短線警示
                if institutional_data and margin_data:
                    analysis = analyze_short_term_institutional(institutional_data, margin_data, price_data['volume'])
                    if analysis:
                        color = "#28a745" if analysis['score'] >= 2 else "#ffc107" if analysis['score'] >= -1 else "#dc3545"
                        st.markdown(f"""
                        <div class="metric-card" style="border-left: 4px solid {color};">
                            <div class="stat-label">[短線] 法人動向</div>
                            <div class="stat-value" style="color: {color};">{analysis['rating']}</div>
                        </div>
                        """, unsafe_allow_html=True)
            
            with col_alert2:
                # 長線警示
                if shareholding_data:
                    accumulation = analyze_long_term_accumulation(shareholding_data)
                    if accumulation:
                        st.markdown(f"""
                        <div class="metric-card" style="border-left: 4px solid #4a90e2;">
                            <div class="stat-label">[長線] 大戶籌碼</div>
                            <div class="stat-value" style="color: #4a90e2;">{accumulation['big_holder_ratio']}%</div>
                        </div>
                        """, unsafe_allow_html=True)
            
            with col_alert3:
                # 風險警示
                risk = check_director_risk(director_data)
                if risk:
                    risk_colors = {'high': '#dc3545', 'medium': '#ffc107', 'low': '#28a745'}
                    st.markdown(f"""
                    <div class="metric-card" style="border-left: 4px solid {risk_colors[risk['level']]};">
                        <div class="stat-label">[風險] 董監質押</div>
                        <div class="stat-value" style="color: {risk_colors[risk['level']]};">{risk['ratio']:.1f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # 分析頁籤
            tab1, tab2, tab3, tab4 = st.tabs([
                "📊 短線分析",
                "📈 中長線分析", 
                "💰 財務數據",
                "📉 圖表視覺化"
            ])
            
            with tab1:
                st.subheader("短線法人多空角力分析")
                
                if institutional_data and margin_data:
                    analysis = analyze_short_term_institutional(institutional_data, margin_data, price_data['volume'])
                    
                    if analysis:
                        col1, col2 = st.columns([1, 2])
                        
                        with col1:
                            rating_colors = {'強多': '#28a745', '偏多': '#90ee90', '中性': '#ffc107', '偏空': '#ff8c42', '強空': '#dc3545'}
                            st.markdown(f"""
                            <div style="background: {rating_colors.get(analysis['rating'], '#ffc107')}22; border-left: 4px solid {rating_colors.get(analysis['rating'], '#ffc107')}; padding: 1.5rem; border-radius: 8px; text-align: center;">
                                <h2 style="color: {rating_colors.get(analysis['rating'], '#ffc107')}; margin: 0;">{analysis['rating']}</h2>
                                <p style="color: #6c757d; margin-top: 0.5rem;">評分：{analysis['score']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            st.write("**市場訊號：**")
                            for signal in analysis['signals']:
                                st.write(signal)
                
                # 法人明細
                if institutional_data:
                    st.markdown("#### 三大法人買賣超明細")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("外資", f"{institutional_data['foreign']:,} 張")
                    with col2:
                        st.metric("投信", f"{institutional_data['trust']:,} 張")
                    with col3:
                        st.metric("自營", f"{institutional_data['dealer']:,} 張")
                    with col4:
                        st.metric("合計", f"{institutional_data['total']:,} 張")
                
                # 信用交易
                if margin_data:
                    st.markdown("#### 信用交易狀況")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        margin_change = margin_data['margin_buy'] - margin_data['margin_sell']
                        st.metric("融資變化", f"{margin_change:+,} 張", f"餘額 {margin_data['margin_balance']:,}")
                    
                    with col2:
                        short_change = margin_data['short_cover'] - margin_data['short_sell']
                        st.metric("融券變化", f"{short_change:+,} 張", f"餘額 {margin_data['short_balance']:,}")
                    
                    with col3:
                        if margin_data['margin_balance'] > 0:
                            sr_ratio = (margin_data['short_balance'] / margin_data['margin_balance']) * 100
                            st.metric("券資比", f"{sr_ratio:.2f}%")
            
            with tab2:
                st.subheader("中長線大戶吸籌分析")
                
                accumulation = analyze_long_term_accumulation(shareholding_data)
                
                if accumulation:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="stat-label">千張大戶比例</div>
                            <div class="stat-value" style="color: #4a90e2;">{accumulation['big_holder_ratio']}%</div>
                            <p style="color: #6c757d; margin-top: 0.5rem; font-size: 0.9rem;">
                                大戶人數：{accumulation['big_holder_count']:,} 人
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="stat-label">散戶比例</div>
                            <div class="stat-value" style="color: #ffc107;">{accumulation['retail_ratio']}%</div>
                            <p style="color: #6c757d; margin-top: 0.5rem; font-size: 0.9rem;">
                                散戶人數：{accumulation['retail_count']:,} 人
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    if accumulation['signals']:
                        st.write("**籌碼結構分析：**")
                        for signal in accumulation['signals']:
                            st.write(signal)
                    
                    st.caption(f"📅 資料日期：{accumulation['date']} (每週五更新)")
                else:
                    st.info("📊 集保股權資料每週五更新，請稍後查詢")
            
            with tab3:
                st.subheader("財務數據")
                
                if revenue_data:
                    # 營收品質
                    quality = check_revenue_quality(revenue_data)
                    
                    if quality:
                        quality_colors = {'excellent': '#28a745', 'good': '#90ee90', 'normal': '#ffc107', 'poor': '#dc3545'}
                        quality_labels = {'excellent': '優良', 'good': '良好', 'normal': '普通', 'poor': '待改善'}
                        
                        st.markdown(f"""
                        <div class="metric-card" style="border-left: 4px solid {quality_colors.get(quality['quality'], '#ffc107')};">
                            <div class="stat-label">營收品質</div>
                            <div class="stat-value" style="color: {quality_colors.get(quality['quality'], '#ffc107')};">
                                {quality_labels.get(quality['quality'], '普通')}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        for signal in quality['signals']:
                            st.write(signal)
                    
                    # 營收表格
                    st.markdown("#### 近期月營收")
                    df_revenue = pd.DataFrame(revenue_data)
                    df_revenue.columns = ['年月', '營收（千元）', 'YoY%', 'MoM%']
                    df_revenue['營收（千元）'] = df_revenue['營收（千元）'].apply(lambda x: f"{x:,.0f}")
                    st.dataframe(df_revenue, use_container_width=True, hide_index=True)
                else:
                    st.info("📊 查無營收資料")
                
                # 董監持股
                risk = check_director_risk(director_data)
                
                if risk:
                    st.markdown("#### 董監持股風險")
                    
                    if risk['level'] == 'high':
                        st.error(f"{risk['message']}\n\n⚠️ 董監事質押比例過高，大盤下跌時可能面臨斷頭風險")
                    elif risk['level'] == 'medium':
                        st.warning(risk['message'])
                    else:
                        st.success(risk['message'])
            
            with tab4:
                st.subheader("圖表視覺化")
                
                # 這裡可以加入歷史資料圖表
                st.info("💡 圖表功能需要歷史資料，目前顯示當日數據")
                
                # 營收圖表
                if revenue_data:
                    fig = create_revenue_chart(revenue_data)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)




st.markdown("---")
st.caption("📊 資料來源：證交所 OpenAPI、集保所 | ⚠️ 僅供參考，非投資建議")

