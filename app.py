import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from datetime import datetime, timedelta
import json
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from concurrent.futures import ThreadPoolExecutor, as_completed

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

# ==================== 股票名稱對照表 ====================
# 涵蓋常用台股的中文名稱
STOCK_NAMES = {
    # 權值股
    "2330": "台積電", "2317": "鴻海", "2454": "聯發科", "2308": "台達電",
    "2382": "廣達", "2412": "中華電", "2891": "中信金", "2881": "富邦金",
    "2882": "國泰金", "2884": "玉山金", "2886": "兆豐金", "2885": "元大金",
    "2890": "永豐金", "2887": "台新金", "2880": "華南金", "2883": "開發金",
    "2888": "新光金", "2889": "國票金", "2892": "第一金",
    "1303": "南亞", "1301": "台塑", "1326": "台化", "6505": "台塑化",
    "2002": "中鋼", "2105": "正新", "2207": "和泰車", "2912": "統一超",
    "1216": "統一", "9910": "豐泰", "1101": "台泥", "1102": "亞泥",
    "2603": "長榮", "2609": "陽明", "2615": "萬海", "2618": "長榮航",
    "2610": "華航", "2801": "彰銀", "5871": "中租-KY", "5876": "上海商銀",
    
    # ETF
    "0050": "元大台灣50", "0056": "元大高股息", "00878": "國泰永續高股息",
    "006208": "富邦台50", "00929": "復華台灣科技優息", "00919": "群益台灣精選高息",
    "00713": "元大台灣高息低波", "00701": "國泰股利精選30", "00692": "富邦公司治理",
    "00733": "富邦臺灣中小", "0051": "元大中型100", "0052": "富邦科技",
    "0053": "元大電子", "0055": "元大MSCI金融", "0057": "富邦摩台",
    "00631L": "元大台灣50正2", "00632R": "元大台灣50反1",
    "00633L": "富邦上証正2", "00634R": "富邦上証反1",
    "00637L": "元大滬深300正2", "00638R": "元大滬深300反1",
    "00657": "國泰日經225", "00660": "元大歐洲50",
    "00661": "元大日經225", "00662": "富邦NASDAQ", "00663L": "國泰臺灣加權正2",
    "00664R": "國泰臺灣加權反1", "00668": "國泰美國道瓊",
    "00670L": "富邦NASDAQ正2", "00671R": "富邦NASDAQ反1",
    "00675L": "富邦臺灣加權正2", "00676R": "富邦臺灣加權反1",
    "00678": "群益NBI生技", "00680L": "元大美債20正2", "00681R": "元大美債20反1",
    "00682U": "元大美元指數", "00683L": "元大日經正2", "00684R": "元大日經反1",
    "00690": "兆豐藍籌30", "00691R": "兆豐臺灣藍籌反1", "00692": "富邦公司治理100",
    "00693U": "兆豐美國公債", "00694B": "富邦美債1-3", "00695B": "富邦美債7-10",
    "00696B": "富邦美債20年", "00697B": "元大美債7-10", "00702": "國泰標普低波高息",
    "00708L": "元大標普500正2", "00709": "富邦歐洲", "00710B": "復華彭博非投等債",
    "00711B": "復華彭博非投等債", "00712": "復華富時不動產",
    "00714": "群益道瓊美國地產", "00715L": "期街口布蘭特正2",
    "00717": "富邦美國特別股", "00720B": "元大投資級公司債", "00721B": "元大中國債3-5",
    "00722B": "群益投資級金融債", "00723B": "群益投資級科技債", "00724B": "群益10年IG金融債",
    "00725B": "國泰投資級公司債", "00726B": "國泰5年期以上IG債",
    "00727B": "國泰1-5Y IG債", "00731": "復華富時高息低波",
    "00734B": "台新JPM新興債", "00735": "國泰臺韓科技",
    "00736": "國泰新興市場", "00737": "國泰AI+Robo",
    "00738U": "元大期貨白銀", "00739": "元大MSCI A股",
    "00740B": "富邦全球投等債", "00741B": "富邦全球投等債(20+)",
    "00742": "新光內需收益", "00743": "國泰中國A50",
    "00752": "中信中國50", "00753L": "中信中國50正2",
    "00757": "統一FANG+", "00762": "元大全球AI",
    "00763U": "期街口黃豆", "00770": "國泰北美科技",
    "00771": "元大US高息特別股", "00772B": "中信高評級公司債",
    "00773B": "中信優先金融債", "00774B": "新光15年IG金融債",
    "00775B": "新光15年IG債", "00777B": "凱基AAA-AA公司債",
    "00778B": "凱基金融債20+", "00779B": "凱基美債25+",
    "00780B": "國泰投資級公司債", "00781B": "凱基綠能債",
    "00782B": "群益A級公司債", "00783B": "群益AAA-AA公司債",
    "00784B": "富邦中國投等債", "00785B": "富邦金融投等債",
    "00786B": "富邦A級公司債", "00787B": "復華10+金融債",
    "00788B": "中信美國公債20年", "00789B": "中信銀行資本債",
    "00790B": "復華富時不動產", "00791B": "復華全球高收益債",
    "00792B": "群益25年美債", "00793B": "群益5年IG債",
    "00794B": "群益AAA-A公司債", "00795B": "中信美國公債20年",
    "00796B": "群益7+中國政策債", "00797B": "凱基IG精選15+",
    "00798B": "凱基新興債10+", "00799B": "新光美元A優先金融債",
    "00800B": "新光綠能優先債", "00801B": "中信美國公債20年",
    "00802B": "群益AAA-AA公司債", "00803B": "群益優選15+IG債",
    "00804B": "富邦投資級美元金融債", "00805B": "富邦投資級公司債",
    "00806B": "復華富時10年期投資等級",
    
    # 半導體
    "3034": "聯詠", "3008": "大立光", "3711": "日月光投控", "2303": "聯電",
    "2379": "瑞昱", "3661": "世芯-KY", "6669": "緯穎", "3017": "奇鋐",
    "2376": "技嘉", "2474": "可成", "2356": "英業達", "2353": "宏碁",
    "2357": "華碩", "3231": "緯創", "2360": "致茂", "3045": "台灣大",
    "4904": "遠傳", "8454": "富邦媒", "2049": "上銀", "3105": "穩懋",
    "6488": "環球晶", "4938": "和碩", "3035": "智原", "2344": "華邦電",
    "2408": "南亞科", "2329": "華泰", "2342": "茂矽", "2351": "順德",
    "2363": "矽統", "3443": "創意", "8261": "富鼎", "6770": "力積電",
    "3037": "欣興", "3533": "嘉澤", "2458": "義隆", "5483": "中美晶",
    "8016": "矽創", "2360": "致茂", "6271": "同欣電", "8069": "元太",
    "6515": "穎崴", "6531": "愛普", "3413": "京鼎", "6781": "AES-KY",
    
    # 生技
    "1707": "葡萄王", "4119": "旭富", "4174": "浩鼎", "4123": "晟德",
    "4128": "中天", "4142": "國光生", "6446": "藥華藥", "4174": "浩鼎",
    
    # 食品
    "1227": "佳格", "1213": "大成", "1210": "大成", "1232": "大統益",
    "2727": "王品", "2731": "雄獅", "2926": "誠品生活",
    
    # 紡織
    "1402": "遠東新", "1409": "新纖", "1434": "福懋", "1440": "南紡",
    "1441": "大東", "1444": "力鵬",
    
    # 鋼鐵
    "2002": "中鋼", "2006": "東和鋼鐵", "2008": "高興昌", "2014": "中鴻",
    "2015": "豐興", "2024": "志聯", "2027": "大成鋼", "2028": "威致",
    "2031": "新光鋼", "2032": "新鋼", "2033": "佳大", "2034": "允強",
    "2038": "海光", "2049": "上銀",
    
    # 觀光
    "2701": "萬企", "2702": "華園", "2704": "國賓", "2705": "六福",
    "2706": "第一店", "2722": "夏都", "2727": "王品", "2731": "雄獅",
    "2739": "寒舍",
    
    # 航運
    "2603": "長榮", "2605": "新興", "2606": "裕民", "2607": "榮運",
    "2608": "嘉里大榮", "2609": "陽明", "2610": "華航", "2611": "志信",
    "2612": "中航", "2613": "中櫃", "2614": "東森", "2615": "萬海",
    "2617": "台航", "2618": "長榮航",
    
    # 其他
    "9105": "泰金寶-DR", "9904": "寶成", "9907": "統一實", "9914": "美利達",
    "9917": "中保科", "9921": "巨大", "9933": "中鼎", "9938": "百和",
    "9939": "宏全", "9941": "裕融", "9944": "新麗", "9945": "潤泰新",
    "9946": "三發地產", "9955": "佳龍",
    
    # 金融
    "5880": "合庫金", "5876": "上海商銀", "2812": "台中銀", "2823": "中壽",
    "2832": "台產", "2845": "遠東銀", "2849": "安泰銀", "2850": "新產",
    "2851": "中再保", "2852": "第一保",
    
    # 電子零組件
    "2327": "國巨", "2369": "菱生", "2377": "微星", "2385": "群光",
    "2392": "正崴", "2395": "研華", "2397": "友通", "2399": "映泰",
    "2404": "漢唐", "2409": "友達", "2417": "圓剛", "2418": "雅新",
    "2419": "仲琦", "2421": "建準", "2423": "固緯", "2424": "隴華",
    "2426": "鼎元", "2427": "三商電", "2428": "興勤", "2429": "永誠",
    "2430": "燦坤", "2431": "聯昌", "2433": "互盛電", "2434": "統懋",
    "2436": "偉詮電", "2438": "翔耀",
    
    # AI 概念股
    "2330": "台積電", "2454": "聯發科", "3661": "世芯-KY", "2376": "技嘉",
    "3017": "奇鋐", "6669": "緯穎", "3231": "緯創", "2382": "廣達",
    "3037": "欣興", "6515": "穎崴", "8210": "勤誠", "3450": "聯鈞",
}

# ==================== 工具函數 ====================

def get_stock_name(code):
    """取得股票名稱"""
    return STOCK_NAMES.get(code, code)

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

# ==================== Yahoo Finance API ====================

@st.cache_data(ttl=300)
def fetch_stock_data(stock_code, period="3mo"):
    """使用 Yahoo Finance 取得股票資料"""
    try:
        ticker_symbol = f"{stock_code}.TW"
        ticker = yf.Ticker(ticker_symbol)
        
        hist = ticker.history(period=period)
        
        if hist.empty:
            ticker_symbol = f"{stock_code}.TWO"
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period=period)
            
            if hist.empty:
                return None
        
        try:
            info = ticker.info
        except:
            info = {}
        
        # 計算移動平均線
        hist['MA5'] = hist['Close'].rolling(window=5).mean()
        hist['MA20'] = hist['Close'].rolling(window=20).mean()
        hist['MA60'] = hist['Close'].rolling(window=60).mean()
        
        latest = hist.iloc[-1]
        prev = hist.iloc[-2] if len(hist) > 1 else latest
        
        change = latest['Close'] - prev['Close']
        change_pct = (change / prev['Close']) * 100 if prev['Close'] > 0 else 0
        
        # 優先使用對照表的名稱
        stock_name = get_stock_name(stock_code)
        if stock_name == stock_code:
            # 對照表沒有，嘗試從 info 取得
            stock_name = info.get('longName', info.get('shortName', stock_code))
        
        return {
            'code': stock_code,
            'name': stock_name,
            'close': float(latest['Close']),
            'open': float(latest['Open']),
            'high': float(latest['High']),
            'low': float(latest['Low']),
            'volume': int(latest['Volume']) // 1000,
            'change': float(change),
            'change_pct': float(change_pct),
            'prev_close': float(prev['Close']),
            'history': hist,
            'info': info,
            'ticker_symbol': ticker_symbol
        }
    except Exception as e:
        return None

def fetch_single_stock_simple(code, period="1mo"):
    """簡化版單股查詢（用於批次）"""
    try:
        ticker = yf.Ticker(f"{code}.TW")
        hist = ticker.history(period=period)
        
        if hist.empty:
            ticker = yf.Ticker(f"{code}.TWO")
            hist = ticker.history(period=period)
            if hist.empty:
                return None
        
        if len(hist) < 2:
            return None
        
        latest = hist.iloc[-1]
        prev = hist.iloc[-2]
        
        change = latest['Close'] - prev['Close']
        change_pct = (change / prev['Close']) * 100 if prev['Close'] > 0 else 0
        
        five_day_change = 0
        twenty_day_change = 0
        
        if len(hist) >= 5:
            five_day_change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-5]) / hist['Close'].iloc[-5]) * 100
        
        if len(hist) >= 20:
            twenty_day_change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-20]) / hist['Close'].iloc[-20]) * 100
        
        # 估算金額（千元）
        amount = (latest['Close'] * latest['Volume']) / 1000
        
        return {
            'code': code,
            'name': get_stock_name(code),
            'close': float(latest['Close']),
            'change': float(change),
            'change_pct': float(change_pct),
            'volume': int(latest['Volume']) // 1000,
            'amount': float(amount),
            'five_day': float(five_day_change),
            'twenty_day': float(twenty_day_change)
        }
    except:
        return None

@st.cache_data(ttl=300)
def fetch_multiple_stocks_parallel(stock_codes):
    """並行查詢多支股票"""
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_code = {executor.submit(fetch_single_stock_simple, code): code for code in stock_codes}
        
        for future in as_completed(future_to_code):
            data = future.result()
            if data:
                results.append(data)
    
    return results

# ==================== 主程式 ====================

# 標題
col_title, col_mode = st.columns([3, 1])

with col_title:
    st.title("📈 台股籌碼分析系統")
    st.caption("✨ 即時股價、漲跌排行、熱門股追蹤")

with col_mode:
    st.write("")
    mode = st.radio(
        "模式",
        ["個股分析", "大盤排行", "熱門股追蹤"],
        horizontal=True,
        label_visibility="collapsed"
    )

st.markdown("---")

# ==================== 個股分析 ====================

if mode == "個股分析":
    st.subheader("🔍 個股查詢與分析")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        stock_code = st.text_input("股票代號", value="2330", placeholder="例：2330").strip()
    
    with col2:
        period = st.selectbox("查詢期間", ["1個月", "3個月", "6個月", "1年", "2年"], index=1)
    
    with col3:
        st.write("")
        st.write("")
        analyze_btn = st.button("🔍 開始查詢", type="primary", use_container_width=True)
    
    period_map = {"1個月": "1mo", "3個月": "3mo", "6個月": "6mo", "1年": "1y", "2年": "2y"}
    
    if analyze_btn and stock_code:
        with st.spinner('正在查詢中...'):
            data = fetch_stock_data(stock_code, period_map[period])
        
        if not data:
            st.error(f"❌ 查無股票代號 {stock_code}")
            st.info("💡 請確認：\n- 股票代號正確（如：2330）\n- 為台灣上市/上櫃股票")
        else:
            st.markdown(f"### {data['name']} ({stock_code})")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                delta_color = "normal" if data['change'] >= 0 else "inverse"
                st.metric("收盤價", f"${data['close']:.2f}", f"{data['change']:+.2f} ({data['change_pct']:+.2f}%)", delta_color=delta_color)
            
            with col2:
                st.metric("成交量", f"{data['volume']:,} 張")
            
            with col3:
                st.metric("最高", f"${data['high']:.2f}")
            
            with col4:
                st.metric("最低", f"${data['low']:.2f}")
            
            st.markdown("---")
            
            tab1, tab2, tab3, tab4 = st.tabs(["📈 K線圖", "📊 成交量", "📋 歷史數據", "📄 公司資訊"])
            
            hist = data['history']
            
            with tab1:
                st.subheader("K線圖與移動平均線")
                
                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=hist.index, open=hist['Open'], high=hist['High'],
                    low=hist['Low'], close=hist['Close'], name='K線',
                    increasing_line_color='#dc3545', decreasing_line_color='#28a745'
                ))
                fig.add_trace(go.Scatter(x=hist.index, y=hist['MA5'], name='MA5', line=dict(color='#ffc107', width=1.5)))
                fig.add_trace(go.Scatter(x=hist.index, y=hist['MA20'], name='MA20', line=dict(color='#4a90e2', width=1.5)))
                fig.add_trace(go.Scatter(x=hist.index, y=hist['MA60'], name='MA60', line=dict(color='#9c27b0', width=1.5)))
                
                fig.update_layout(
                    yaxis_title='價格 (TWD)', xaxis_title='日期', template='plotly_white',
                    height=500, xaxis_rangeslider_visible=False,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    hovermode='x unified'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                st.subheader("技術指標")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    ma5 = hist['MA5'].iloc[-1]
                    if not pd.isna(ma5):
                        ma5_signal = "📈 站上" if data['close'] > ma5 else "📉 跌破"
                        st.metric("MA5", f"${ma5:.2f}", ma5_signal)
                
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
                colors = ['#dc3545' if hist['Close'].iloc[i] > hist['Open'].iloc[i] else '#28a745' for i in range(len(hist))]
                
                fig_vol.add_trace(go.Bar(x=hist.index, y=hist['Volume'] / 1000, name='成交量', marker_color=colors))
                
                vol_ma20 = hist['Volume'].rolling(window=20).mean() / 1000
                fig_vol.add_trace(go.Scatter(x=hist.index, y=vol_ma20, name='20日均量', line=dict(color='#4a90e2', width=2)))
                
                fig_vol.update_layout(
                    yaxis_title='成交量 (千張)', xaxis_title='日期', template='plotly_white',
                    height=400, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_vol, use_container_width=True)
                
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
                
                st.dataframe(df_display.sort_index(ascending=False), use_container_width=True, height=500)
                
                csv = df_display.to_csv(encoding='utf-8-sig')
                st.download_button(label="📥 下載歷史數據 (CSV)", data=csv, file_name=f"{stock_code}_{period}_history.csv", mime="text/csv")
            
            with tab4:
                st.subheader("公司資訊")
                info = data['info']
                
                if info:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**📊 基本資訊**")
                        st.write(f"**產業：** {info.get('industry', 'N/A')}")
                        st.write(f"**部門：** {info.get('sector', 'N/A')}")
                        if info.get('fullTimeEmployees'):
                            st.write(f"**員工數：** {info['fullTimeEmployees']:,}")
                    
                    with col2:
                        st.markdown("**💰 財務指標**")
                        if info.get('marketCap'):
                            mc = info['marketCap']
                            if mc >= 1e12:
                                st.write(f"**市值：** {mc/1e12:.2f} 兆")
                            elif mc >= 1e8:
                                st.write(f"**市值：** {mc/1e8:.2f} 億")
                        if info.get('trailingPE'):
                            st.write(f"**本益比 (PE)：** {info['trailingPE']:.2f}")
                        if info.get('priceToBook'):
                            st.write(f"**股價淨值比 (PB)：** {info['priceToBook']:.2f}")
                        if info.get('dividendYield'):
                            st.write(f"**股息殖利率：** {info['dividendYield']*100:.2f}%")
                    
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

# ==================== 大盤排行 ====================

elif mode == "大盤排行":
    st.subheader("📊 大盤漲跌排行")
    
    st.info("💡 追蹤台股權值股的漲跌排行，使用 Yahoo Finance 即時資料")
    
    # 大盤代表股票（包含市值前 50 大）
    market_stocks = [
        # 半導體
        "2330", "2454", "2303", "3034", "3008", "3711", "2379", "3661", "6669", "3017",
        # 電子
        "2317", "2308", "2382", "2376", "2474", "2353", "2356", "2357", "3231", "2360",
        # 金融
        "2891", "2881", "2882", "2884", "2886", "2885", "2890", "2887", "2880", "2883",
        # 傳產
        "1303", "1301", "1326", "2002", "2105", "2207", "2912", "1216", "9910", "1101",
        # 航運
        "2603", "2609", "2615", "2618", "2610",
        # 電信
        "2412", "4904", "3045",
        # 通路/百貨
        "8454",
        # 其他重要
        "6505", "2049", "3045", "9921",
    ]
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if st.button("🔄 更新大盤資料", type="primary", use_container_width=True):
            st.session_state['market_data'] = None
    
    with col2:
        st.write("")
    
    # 載入大盤資料
    if 'market_data' not in st.session_state or st.session_state.get('market_data') is None:
        with st.spinner(f'正在查詢 {len(market_stocks)} 支大盤權值股（約 30 秒）...'):
            progress = st.progress(0)
            results = []
            
            for i, code in enumerate(market_stocks):
                data = fetch_single_stock_simple(code, "1mo")
                if data:
                    results.append(data)
                progress.progress((i + 1) / len(market_stocks))
            
            progress.empty()
            st.session_state['market_data'] = results
            st.session_state['market_update_time'] = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    
    if 'market_data' in st.session_state and st.session_state['market_data']:
        results = st.session_state['market_data']
        
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
        
        st.caption(f"📅 最後更新：{st.session_state.get('market_update_time', 'N/A')}")
        
        st.markdown("---")
        
        # 排行榜
        tab1, tab2, tab3, tab4 = st.tabs(["▲ 漲幅 TOP 10", "▼ 跌幅 TOP 10", "💰 成交額 TOP 10", "📊 全部"])
        
        with tab1:
            st.subheader("▲ 漲幅排行 TOP 10")
            sorted_up = sorted(results, key=lambda x: x['change_pct'], reverse=True)[:10]
            
            html = '<table><thead><tr><th>排名</th><th>代號</th><th>名稱</th><th>收盤</th><th>漲跌</th><th>漲跌幅</th><th>5日%</th><th>20日%</th><th>成交量</th></tr></thead><tbody>'
            
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
            st.subheader("▼ 跌幅排行 TOP 10")
            sorted_down = sorted(results, key=lambda x: x['change_pct'])[:10]
            
            html = '<table><thead><tr><th>排名</th><th>代號</th><th>名稱</th><th>收盤</th><th>漲跌</th><th>漲跌幅</th><th>5日%</th><th>20日%</th><th>成交量</th></tr></thead><tbody>'
            
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
        
        with tab3:
            st.subheader("💰 成交額 TOP 10")
            st.caption("成交額 = 成交價 × 成交量")
            sorted_amount = sorted(results, key=lambda x: x['amount'], reverse=True)[:10]
            
            html = '<table><thead><tr><th>排名</th><th>代號</th><th>名稱</th><th>收盤</th><th>漲跌幅</th><th>成交量</th><th>成交額</th></tr></thead><tbody>'
            
            for i, r in enumerate(sorted_amount, 1):
                change_class = 'positive' if r['change'] > 0 else 'negative' if r['change'] < 0 else 'neutral'
                change_sign = '+' if r['change'] > 0 else ''
                
                html += f'<tr>'
                html += f'<td>{i:02d}</td>'
                html += f'<td><strong>{r["code"]}</strong></td>'
                html += f'<td>{r["name"]}</td>'
                html += f'<td>${r["close"]:.2f}</td>'
                html += f'<td><span class="{change_class}">{change_sign}{r["change_pct"]:.2f}%</span></td>'
                html += f'<td>{r["volume"]:,}</td>'
                html += f'<td>{format_number(r["amount"] * 1000)}</td>'
                html += f'</tr>'
            
            html += '</tbody></table>'
            st.markdown(html, unsafe_allow_html=True)
        
        with tab4:
            st.subheader("📊 全部追蹤股票")
            
            # 轉換為 DataFrame
            df = pd.DataFrame(results)
            df = df[['code', 'name', 'close', 'change', 'change_pct', 'five_day', 'twenty_day', 'volume']]
            df.columns = ['代號', '名稱', '收盤', '漲跌', '漲跌幅%', '5日%', '20日%', '成交量']
            df = df.round(2)
            
            st.dataframe(df, use_container_width=True, height=600)

# ==================== 熱門股追蹤 ====================

else:
    st.subheader("📊 熱門股即時追蹤")
    
    st.info("💡 追蹤台股熱門股票的即時表現，每 5 分鐘自動更新")
    
    default_stocks = {
        "權值股": ["2330", "2454", "2317", "2308", "2412", "2382", "2891", "2881", "1303", "1301"],
        "ETF": ["0050", "0056", "00878", "006208", "00929", "00919"],
        "金融": ["2891", "2881", "2882", "2884", "2880", "2885", "2886", "2887", "2890"],
        "AI概念": ["2330", "2454", "3661", "2376", "3017", "6669", "3231", "2382"],
    }
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        category = st.selectbox("選擇類別", list(default_stocks.keys()) + ["自訂"])
    
    with col2:
        st.write("")
        st.write("")
        refresh_btn = st.button("🔄 更新資料", type="primary", use_container_width=True)
    
    if category == "自訂":
        custom_codes = st.text_input("輸入股票代號（以逗號分隔）", value="2330,2454,2317", placeholder="例：2330,2454,2317")
        stock_codes = [c.strip() for c in custom_codes.split(",") if c.strip()]
    else:
        stock_codes = default_stocks[category]
    
    cache_key = f"hot_{category}_{','.join(stock_codes)}"
    
    if refresh_btn or cache_key not in st.session_state:
        with st.spinner(f'正在查詢 {len(stock_codes)} 支股票...'):
            progress = st.progress(0)
            results = []
            
            for i, code in enumerate(stock_codes):
                data = fetch_single_stock_simple(code, "1mo")
                if data:
                    results.append(data)
                progress.progress((i + 1) / len(stock_codes))
            
            progress.empty()
            st.session_state[cache_key] = results
            st.session_state['hot_update_time'] = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    
    if cache_key in st.session_state and st.session_state[cache_key]:
        results = st.session_state[cache_key]
        
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
        
        st.caption(f"📅 最後更新：{st.session_state.get('hot_update_time', 'N/A')}")
        
        st.markdown("---")
        
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
