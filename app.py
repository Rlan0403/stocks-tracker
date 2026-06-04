import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go

st.set_page_config(page_title="台股籌碼分析系統", page_icon="📈", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
.main .block-container {max-width: 1200px; padding: 1rem 2rem;}
@media (max-width: 768px) {.main .block-container {padding: 1rem;}}
.main {background: #f5f7fa;}
h1, h2, h3, h4 {color: #2c3e50 !important; font-weight: 700 !important;}
h1 {font-size: 2rem !important; margin-bottom: 0.5rem !important;}
@media (max-width: 768px) {h1 {font-size: 1.5rem !important;}}
.metric-card {background: #ffffff; border: 1px solid #dee2e6; border-radius: 12px; padding: 1.2rem; box-shadow: 0 2px 4px rgba(0,0,0,0.08); margin-bottom: 1rem;}
.stat-label {font-size: 0.85rem; color: #6c757d; margin-bottom: 0.5rem; font-weight: 600;}
.stat-value {font-size: 1.8rem; font-weight: 700; margin: 0;}
@media (max-width: 768px) {.stat-value {font-size: 1.4rem;}}
.stButton {width: 100%;}
.stButton>button {background: #4a90e2; color: #ffffff; font-weight: 600; border: none; border-radius: 10px; padding: 0.75rem 1.5rem; width: 100%;}
.stButton>button:hover {background: #357abd; transform: translateY(-2px);}
table {width: 100%; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-collapse: separate; border-spacing: 0;}
thead th {background: #e9ecef; color: #2c3e50; font-weight: 700; padding: 1rem 0.75rem; text-align: center; border: none; font-size: 0.9rem;}
@media (max-width: 768px) {thead th {padding: 0.75rem 0.5rem; font-size: 0.75rem;}}
tbody td {background: #ffffff; color: #495057; padding: 0.9rem 0.75rem; text-align: center; border-bottom: 1px solid #f1f3f5; font-size: 0.9rem;}
@media (max-width: 768px) {tbody td {padding: 0.7rem 0.5rem; font-size: 0.8rem;}}
tbody tr:nth-child(even) td {background: #f8f9fa;}
tbody tr:hover td {background: #dee2e6;}
.streak-2 td {background: #fff9e6 !important;}
.streak-3 td {background: #ffe0b3 !important; border-left: 4px solid #ff9800 !important;}
.streak-5 td {background: #f8d7da !important; border-left: 4px solid #dc3545 !important;}
.positive {color: #dc3545 !important; font-weight: 700;}
.negative {color: #28a745 !important; font-weight: 700;}
.neutral {color: #6c757d !important;}
.badge {display: inline-block; padding: 0.35rem 0.75rem; border-radius: 12px; font-size: 0.8rem; font-weight: 700;}
.badge-2 {background: #fff9e6; color: #856404; border: 1px solid #ffc107;}
.badge-3 {background: #ffe0b3; color: #b65f00; border: 1px solid #ff9800;}
.badge-5 {background: #f8d7da; color: #721c24; border: 1px solid #dc3545;}
.badge-normal {background: #e9ecef; color: #6c757d;}
.source-tag {display: inline-block; padding: 0.25rem 0.6rem; border-radius: 6px; font-size: 0.75rem; font-weight: 600;}
.source-twse {background: #d1ecf1; color: #0c5460;}
.source-yahoo {background: #d4edda; color: #155724;}
.stTabs [data-baseweb="tab-list"] {gap: 8px; background: #ffffff; padding: 0.5rem; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.08);}
.stTabs [data-baseweb="tab"] {background: transparent; color: #6c757d; border-radius: 8px; padding: 0.75rem 1.5rem; font-weight: 600;}
.stTabs [aria-selected="true"] {background: #4a90e2; color: white;}
.stTextInput > div > div > input {background: #ffffff; border: 2px solid #dee2e6; border-radius: 8px;}
.stRadio > div {background: #ffffff; padding: 0.5rem; border-radius: 10px;}
[data-testid="stMetricValue"] {color: #2c3e50; font-size: 1.8rem;}
@media (max-width: 768px) {[data-testid="stMetricValue"] {font-size: 1.3rem;}}
</style>
""", unsafe_allow_html=True)

# 股票名稱對照表
STOCK_NAMES = {
    "2330":"台積電","2454":"聯發科","2303":"聯電","2379":"瑞昱","3034":"聯詠","3008":"大立光",
    "3711":"日月光投控","3661":"世芯-KY","6669":"緯穎","3017":"奇鋐","2376":"技嘉","2474":"可成",
    "2356":"英業達","2353":"宏碁","2357":"華碩","3231":"緯創","6488":"環球晶","4938":"和碩",
    "3035":"智原","2344":"華邦電","2408":"南亞科","3443":"創意","6770":"力積電","3037":"欣興",
    "3533":"嘉澤","2458":"義隆","5483":"中美晶","8016":"矽創","6271":"同欣電","8069":"元太",
    "6515":"穎崴","6531":"愛普","3413":"京鼎","6781":"AES-KY","5285":"界霖","3653":"健策",
    "2449":"京元電子","6285":"啟碁","2393":"億光","2436":"偉詮電","8081":"致新","3105":"穩懋",
    "2455":"全新","2308":"台達電","2317":"鴻海","2382":"廣達","2412":"中華電","2327":"國巨",
    "2385":"群光","2392":"正崴","2395":"研華","2360":"致茂","2049":"上銀","8210":"勤誠",
    "3450":"聯鈞","2377":"微星","0050":"元大台灣50","0056":"元大高股息","00878":"國泰永續高股息",
    "006208":"富邦台50","00929":"復華台灣科技優息","00919":"群益台灣精選高息","00713":"元大台灣高息低波",
    "00701":"國泰股利精選30","00733":"富邦臺灣中小","0051":"元大中型100","0052":"富邦科技",
    "00631L":"元大台灣50正2","00632R":"元大台灣50反1","00692":"富邦公司治理100","00850":"元大ESG永續",
    "00940":"元大臺灣價值高息","00939":"統一台灣高息動能","2891":"中信金","2881":"富邦金","2882":"國泰金",
    "2884":"玉山金","2886":"兆豐金","2885":"元大金","2890":"永豐金","2887":"台新金","2880":"華南金",
    "2883":"開發金","2888":"新光金","2889":"國票金","2892":"第一金","5880":"合庫金","5876":"上海商銀",
    "2801":"彰銀","2823":"中壽","2812":"台中銀","2845":"遠東銀","1303":"南亞","1301":"台塑","1326":"台化",
    "6505":"台塑化","2002":"中鋼","2006":"東和鋼鐵","2014":"中鴻","2015":"豐興","2027":"大成鋼",
    "1216":"統一","2912":"統一超","1227":"佳格","1210":"大成","1232":"大統益","2727":"王品","9910":"豐泰",
    "1402":"遠東新","1409":"新纖","1434":"福懋","1101":"台泥","1102":"亞泥","2603":"長榮","2609":"陽明",
    "2615":"萬海","2618":"長榮航","2610":"華航","2605":"新興","2606":"裕民","2731":"雄獅","5871":"中租-KY",
    "2207":"和泰車","9921":"巨大","9914":"美利達","3045":"台灣大","4904":"遠傳","8454":"富邦媒",
    "9933":"中鼎","1707":"葡萄王","6446":"藥華藥","4174":"浩鼎","4128":"中天","4142":"國光生","4123":"晟德",
    "9105":"泰金寶-DR","9917":"中保科","9941":"裕融","9945":"潤泰新","2105":"正新",
    # 面板
    "2409":"友達","3481":"群創","6116":"彩晶","3504":"揚明光",
    # IC 通路
    "3036":"文曄","2347":"聯強","2351":"順德","6202":"盛群",
    # 債券型 ETF
    "00679B":"元大美債20","00687B":"國泰20年美債","00696B":"富邦美債20年",
    "00697B":"元大美債7-10","00720B":"元大投資級公司債","00772B":"中信高評級公司債",
    "00773B":"中信優先金融債","00777B":"凱基AAA-AA公司債","00778B":"凱基金融債20+",
    "00779B":"凱基美債25+","00937B":"群益ESG投等債20+","00938B":"凱基US優選非投等債",
    "00988A":"凱基美國非投等債","00990A":"兆豐美國非投等債","00991B":"富邦中國投資級債",
    "00942B":"台新美A公司債20+","00943B":"兆豐10年期以上A級美元公司債",
    "00945B":"凱基美國非投等債","00937B":"群益ESG投等債20+",
    # 其他常見
    "2887":"台新金","2880":"華南金","2618":"長榮航","2882":"國泰金","2881":"富邦金",
    "2027":"大成鋼","2603":"長榮","2609":"陽明","2615":"萬海",
}

# 產業分類對照表
INDUSTRY_MAP = {
    "2330":"半導體-晶圓代工","2454":"半導體-IC設計","2303":"半導體-晶圓代工","2379":"半導體-IC設計",
    "3034":"半導體-IC設計","3008":"半導體-光學","3711":"半導體-封測","3661":"半導體-IC設計",
    "6669":"半導體-伺服器","3017":"半導體-散熱","6488":"半導體-矽晶圓","3035":"半導體-IC設計",
    "2344":"半導體-記憶體","2408":"半導體-記憶體","3443":"半導體-IC設計","6770":"半導體-記憶體",
    "3037":"半導體-載板","3533":"半導體-設備","2458":"半導體-IC設計","5483":"半導體-矽晶圓",
    "8016":"半導體-IC設計","6271":"半導體-封測","8069":"半導體-面板驅動","6515":"半導體-設備",
    "6531":"半導體-IC設計","3413":"半導體-設備","6781":"半導體-設備","5285":"半導體-設備",
    "3653":"半導體-設備","2449":"半導體-封測","2393":"半導體-LED","2436":"半導體-IC設計",
    "8081":"半導體-IC設計","3105":"半導體-IC設計","2455":"半導體-IC設計","2308":"電子-電源",
    "2317":"電子-代工組裝","2382":"電子-代工組裝","2376":"電子-代工組裝","2474":"電子-機殼",
    "2356":"電子-代工組裝","2353":"電子-代工組裝","2357":"電子-代工組裝","3231":"電子-代工組裝",
    "4938":"電子-代工組裝","2327":"電子-被動元件","2385":"電子-零組件","2392":"電子-連接器",
    "2395":"電子-工業電腦","2360":"電子-測試設備","2049":"電子-機械","8210":"電子-機殼",
    "3450":"電子-光學","2377":"電子-代工組裝","2891":"金融-金控","2881":"金融-金控",
    "2882":"金融-金控","2884":"金融-金控","2886":"金融-金控","2885":"金融-金控","2890":"金融-金控",
    "2887":"金融-金控","2880":"金融-金控","2883":"金融-金控","2888":"金融-金控","2889":"金融-金控",
    "2892":"金融-金控","5880":"金融-金控","5876":"金融-銀行","2801":"金融-銀行","2823":"金融-保險",
    "2812":"金融-銀行","2845":"金融-銀行","5871":"金融-租賃","1303":"塑化","1301":"塑化",
    "1326":"塑化","6505":"塑化","2002":"鋼鐵","2006":"鋼鐵","2014":"鋼鐵","2015":"鋼鐵",
    "2027":"鋼鐵","1216":"食品","2912":"食品-通路","1227":"食品","1210":"食品","1232":"食品",
    "2727":"食品-餐飲","9910":"運動用品","1402":"紡織","1409":"紡織","1434":"紡織","1101":"水泥",
    "1102":"水泥","2603":"航運-貨櫃","2609":"航運-貨櫃","2615":"航運-貨櫃","2618":"航運-航空",
    "2610":"航運-航空","2605":"航運-散裝","2606":"航運-散裝","2731":"觀光","2207":"汽車",
    "9921":"自行車","9914":"自行車","2412":"電信","3045":"電信","4904":"電信","8454":"電商通路",
    "9933":"工程","1707":"生技","6446":"生技","4174":"生技","4128":"生技","4142":"生技","4123":"生技",
    "0050":"ETF","0056":"ETF","00878":"ETF","006208":"ETF","00929":"ETF","00919":"ETF",
    "00713":"ETF","00701":"ETF","00733":"ETF","0051":"ETF","0052":"ETF","00631L":"ETF-槓桿",
    "00632R":"ETF-反向","00692":"ETF","00850":"ETF","00940":"ETF","00939":"ETF","2105":"輪胎",
}

def get_stock_name(code):
    return STOCK_NAMES.get(code, code)

def get_industry(code):
    return INDUSTRY_MAP.get(code, "其他")

def get_industry_stocks(industry, exclude=None):
    """取得同產業股票（主分類匹配）"""
    main_industry = industry.split('-')[0]
    stocks = []
    for code, ind in INDUSTRY_MAP.items():
        if exclude and code == exclude:
            continue
        if ind.startswith(main_industry):
            stocks.append(code)
    return stocks

def format_number(n):
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

def get_trading_days(num_days=10):
    days = []
    d = datetime.now()
    while len(days) < num_days:
        if d.weekday() < 5:
            days.append(d.strftime("%Y%m%d"))
        d -= timedelta(days=1)
    return days

# ==================== 證交所 API ====================

def fetch_twse_t86(date_str):
    try:
        url = f"https://www.twse.com.tw/fund/T86?response=json&date={date_str}&selectType=ALL"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Referer': 'https://www.twse.com.tw/'
        }
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get('stat') != 'OK' or not data.get('data'):
            return None
        
        stocks = []
        for row in data['data']:
            if not row[0] or len(row[0].strip()) < 4:
                continue
            def parse_int(s):
                try:
                    return int(s.replace(',', ''))
                except:
                    return 0
            stocks.append({
                'code': row[0].strip(),
                'name': row[1].strip(),
                'foreign': parse_int(row[4]),
                'trust': parse_int(row[7]),
                'dealer': parse_int(row[10]) + parse_int(row[13]),
                'total': parse_int(row[14])
            })
        return stocks
    except:
        return None

@st.cache_data(ttl=600)
def fetch_twse_history(num_days=10):
    trading_days = get_trading_days(num_days)
    history = {}
    for date_str in trading_days:
        data = fetch_twse_t86(date_str)
        if data:
            history[date_str] = data
    return history if history else None

def calculate_consecutive(stock_code, history, key='total'):
    """計算連續買/賣天數，返回 (天數, 方向, 日期列表)"""
    dates = sorted(history.keys(), reverse=True)
    consecutive_dates = []
    direction = None
    started_buy = False
    started_sell = False
    
    for date_str in dates:
        stocks = history[date_str]
        found_stock = None
        for s in stocks:
            if s['code'] == stock_code:
                found_stock = s
                break
        
        if not found_stock:
            break
        
        value = found_stock.get(key, 0)
        
        if value > 0:
            if started_sell:
                break
            started_buy = True
            consecutive_dates.append(date_str)
            direction = 'buy'
        elif value < 0:
            if started_buy:
                break
            started_sell = True
            consecutive_dates.append(date_str)
            direction = 'sell'
        else:
            break
    
    return len(consecutive_dates), direction or 'none', consecutive_dates

def format_dates_short(date_list):
    """格式化日期列表為 6/01,6/02 格式"""
    if not date_list:
        return ''
    formatted = [f"{int(d[4:6])}/{int(d[6:8])}" for d in sorted(date_list)]
    return ' '.join(formatted)

# ==================== Yahoo Finance API ====================

@st.cache_data(ttl=300)
def fetch_yf_single(code, period="3mo"):
    try:
        ticker = yf.Ticker(f"{code}.TW")
        hist = ticker.history(period=period)
        if hist.empty:
            ticker = yf.Ticker(f"{code}.TWO")
            hist = ticker.history(period=period)
            if hist.empty:
                return None
        try:
            info = ticker.info
        except:
            info = {}
        hist['MA5'] = hist['Close'].rolling(window=5).mean()
        hist['MA20'] = hist['Close'].rolling(window=20).mean()
        hist['MA60'] = hist['Close'].rolling(window=60).mean()
        latest = hist.iloc[-1]
        prev = hist.iloc[-2] if len(hist) > 1 else latest
        change = latest['Close'] - prev['Close']
        change_pct = (change / prev['Close']) * 100 if prev['Close'] > 0 else 0
        name = get_stock_name(code) if get_stock_name(code) != code else info.get('longName', code)
        return {
            'code': code, 'name': name, 'close': float(latest['Close']),
            'open': float(latest['Open']), 'high': float(latest['High']), 'low': float(latest['Low']),
            'volume': int(latest['Volume']) // 1000, 'change': float(change),
            'change_pct': float(change_pct), 'prev_close': float(prev['Close']),
            'history': hist, 'info': info
        }
    except:
        return None

def fetch_yf_simple(code):
    try:
        ticker = yf.Ticker(f"{code}.TW")
        hist = ticker.history(period="1mo")
        if hist.empty:
            ticker = yf.Ticker(f"{code}.TWO")
            hist = ticker.history(period="1mo")
            if hist.empty:
                return None
        if len(hist) < 2:
            return None
        latest = hist.iloc[-1]
        prev = hist.iloc[-2]
        change = latest['Close'] - prev['Close']
        change_pct = (change / prev['Close']) * 100 if prev['Close'] > 0 else 0
        volume_shares = int(latest['Volume'])
        volume_lots = volume_shares // 1000
        amount = latest['Close'] * volume_shares
        return {
            'code': code, 'name': get_stock_name(code), 'industry': get_industry(code),
            'close': float(latest['Close']), 'change': float(change), 'change_pct': float(change_pct),
            'volume': volume_lots, 'amount': float(amount),
        }
    except:
        return None

# ==================== UI ====================

col_title, col_mode = st.columns([3, 1])
with col_title:
    st.title("📈 台股籌碼分析系統")
    st.caption("✨ 個股分析、法人排行、成交量排行 + 同產業推薦")
with col_mode:
    st.write("")
    mode = st.radio("模式", ["個股分析", "法人排行", "成交量排行"], horizontal=True, label_visibility="collapsed")

st.markdown("---")

# ==================== 個股分析 ====================

if mode == "個股分析":
    st.subheader("🔍 個股查詢")
    
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
        with st.spinner('查詢中...'):
            data = fetch_yf_single(stock_code, period_map[period])
        
        if not data:
            st.error(f"❌ 查無股票代號 {stock_code}")
        else:
            col_n, col_s = st.columns([4, 1])
            with col_n:
                st.markdown(f"### {data['name']} ({stock_code})")
                st.caption(f"📂 產業：{get_industry(stock_code)}")
            with col_s:
                st.markdown('<span class="source-tag source-yahoo">📊 Yahoo Finance</span>', unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("收盤價", f"${data['close']:.2f}", f"{data['change']:+.2f} ({data['change_pct']:+.2f}%)", delta_color="inverse")
            with col2:
                st.metric("成交量", f"{data['volume']:,} 張")
            with col3:
                st.metric("最高", f"${data['high']:.2f}")
            with col4:
                st.metric("最低", f"${data['low']:.2f}")
            
            st.markdown("---")
            tab1, tab2, tab3 = st.tabs(["📈 K線圖", "📊 成交量", "📋 歷史數據"])
            hist = data['history']
            
            with tab1:
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'],
                    low=hist['Low'], close=hist['Close'], name='K線',
                    increasing_line_color='#dc3545', decreasing_line_color='#28a745'))
                fig.add_trace(go.Scatter(x=hist.index, y=hist['MA5'], name='MA5', line=dict(color='#ffc107', width=1.5)))
                fig.add_trace(go.Scatter(x=hist.index, y=hist['MA20'], name='MA20', line=dict(color='#4a90e2', width=1.5)))
                fig.add_trace(go.Scatter(x=hist.index, y=hist['MA60'], name='MA60', line=dict(color='#9c27b0', width=1.5)))
                fig.update_layout(yaxis_title='價格 (TWD)', xaxis_title='日期', template='plotly_white',
                    height=500, xaxis_rangeslider_visible=False,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                st.plotly_chart(fig, use_container_width=True)
            
            with tab2:
                fig_vol = go.Figure()
                colors = ['#dc3545' if hist['Close'].iloc[i] > hist['Open'].iloc[i] else '#28a745' for i in range(len(hist))]
                fig_vol.add_trace(go.Bar(x=hist.index, y=hist['Volume'] / 1000, name='成交量', marker_color=colors))
                vol_ma20 = hist['Volume'].rolling(window=20).mean() / 1000
                fig_vol.add_trace(go.Scatter(x=hist.index, y=vol_ma20, name='20日均量', line=dict(color='#4a90e2', width=2)))
                fig_vol.update_layout(yaxis_title='成交量 (千張)', xaxis_title='日期', template='plotly_white', height=400)
                st.plotly_chart(fig_vol, use_container_width=True)
            
            with tab3:
                df_d = hist.copy()
                df_d['漲跌'] = df_d['Close'] - df_d['Open']
                df_d['漲跌幅%'] = ((df_d['Close'] - df_d['Open']) / df_d['Open']) * 100
                df_d['成交量(張)'] = (df_d['Volume'] / 1000).astype(int)
                df_d = df_d[['Open','High','Low','Close','漲跌','漲跌幅%','成交量(張)']]
                df_d.columns = ['開盤','最高','最低','收盤','漲跌','漲跌幅%','成交量(張)']
                df_d = df_d.round(2)
                st.dataframe(df_d.sort_index(ascending=False), use_container_width=True, height=500)

# ==================== 法人排行 ====================

elif mode == "法人排行":
    st.subheader("🏦 三大法人買賣超排行")
    
    if st.button("🔄 載入法人資料（最近 10 個交易日）", type="primary"):
        st.session_state['twse_history'] = None
    
    if 'twse_history' not in st.session_state or st.session_state.get('twse_history') is None:
        with st.spinner('正在從證交所 API 載入資料...'):
            history = fetch_twse_history(10)
            st.session_state['twse_history'] = history
    
    history = st.session_state.get('twse_history')
    
    if not history:
        st.error("❌ 無法取得證交所資料")
        st.warning("""
        **🚫 證交所 API 在 Streamlit Cloud 被 IP 限制（403 Forbidden）**
        
        三大法人資料**只能在本地運行**才能取得。
        
        📖 **如何在本地運行？**
        ```bash
        git clone https://github.com/Rlan0403/stocks-tracker.git
        cd stocks-tracker
        pip install -r requirements.txt
        streamlit run app.py
        ```
        
        本地運行可以看到：
        - ✅ 外資、投信、自營商買賣超排行
        - ✅ 連續買/賣天數標示（黃/橘/紅）
        
        💡 您可以使用「**成交量排行**」功能（用 Yahoo Finance 在 Cloud 上能用）
        """)
    else:
        latest_date = sorted(history.keys(), reverse=True)[0]
        latest_data = history[latest_date]
        
        st.markdown(f'**資料日期：{latest_date[:4]}/{latest_date[4:6]}/{latest_date[6:8]}** <span class="source-tag source-twse">📊 證交所 OpenAPI</span>', unsafe_allow_html=True)
        st.caption(f"📅 已載入 {len(history)} 個交易日的資料")
        st.info("💡 **連續買賣顏色**：🟡 2 天 ｜ 🟠 3 天 ｜ 🔴 5 天以上")
        st.markdown("---")
        
        tab_overall, tab1, tab2, tab3 = st.tabs(["🎯 綜合（三大法人合計）", "🌍 外資", "💼 投信", "🏛️ 自營商"])
        
        # ===== 綜合 tab (15 名 + 法人比例) =====
        with tab_overall:
            col_buy, col_sell = st.columns(2)
            buy_sorted = sorted([s for s in latest_data if s['total'] > 0], key=lambda x: x['total'], reverse=True)[:15]
            sell_sorted = sorted([s for s in latest_data if s['total'] < 0], key=lambda x: x['total'])[:15]
            
            def render_overall_row(i, s, is_buy=True):
                """渲染綜合排名的一列"""
                consec, direction, dates = calculate_consecutive(s['code'], history, 'total')
                
                row_class = ''
                badge = '<span class="badge badge-normal">1天</span>'
                target_direction = 'buy' if is_buy else 'sell'
                
                if direction == target_direction:
                    if consec >= 5:
                        row_class, badge = 'streak-5', f'<span class="badge badge-5">{consec}天</span>'
                    elif consec >= 3:
                        row_class, badge = 'streak-3', f'<span class="badge badge-3">{consec}天</span>'
                    elif consec >= 2:
                        row_class, badge = 'streak-2', f'<span class="badge badge-2">{consec}天</span>'
                
                # 日期顯示
                date_str = format_dates_short(dates) if direction == target_direction and consec >= 2 else ''
                date_html = f'<div style="font-size:0.7rem;color:#6c757d;margin-top:0.3rem;">{date_str}</div>' if date_str else ''
                
                # 名稱
                name = STOCK_NAMES.get(s['code']) or s.get('name') or s['code']
                
                # 三大法人比例（取絕對值算佔比，方便閱讀）
                total_abs = abs(s['foreign']) + abs(s['trust']) + abs(s['dealer'])
                if total_abs > 0:
                    foreign_pct = (abs(s['foreign']) / total_abs) * 100
                    trust_pct = (abs(s['trust']) / total_abs) * 100
                    dealer_pct = (abs(s['dealer']) / total_abs) * 100
                else:
                    foreign_pct = trust_pct = dealer_pct = 0
                
                # 各分量符號（正/負）
                fc = 'positive' if s['foreign'] > 0 else 'negative' if s['foreign'] < 0 else 'neutral'
                tc = 'positive' if s['trust'] > 0 else 'negative' if s['trust'] < 0 else 'neutral'
                dc = 'positive' if s['dealer'] > 0 else 'negative' if s['dealer'] < 0 else 'neutral'
                
                fs = '+' if s['foreign'] > 0 else ''
                ts = '+' if s['trust'] > 0 else ''
                ds = '+' if s['dealer'] > 0 else ''
                
                total_class = 'positive' if is_buy else 'negative'
                total_sign = '+' if is_buy else ''
                
                row = f'<tr class="{row_class}">'
                row += f'<td>{i:02d}</td>'
                row += f'<td><strong>{s["code"]}</strong></td>'
                row += f'<td>{name}</td>'
                row += f'<td><strong><span class="{total_class}">{total_sign}{format_number(s["total"])}</span></strong></td>'
                row += f'<td><span class="{fc}">{fs}{format_number(s["foreign"])}</span><div style="font-size:0.7rem;color:#6c757d;">{foreign_pct:.0f}%</div></td>'
                row += f'<td><span class="{tc}">{ts}{format_number(s["trust"])}</span><div style="font-size:0.7rem;color:#6c757d;">{trust_pct:.0f}%</div></td>'
                row += f'<td><span class="{dc}">{ds}{format_number(s["dealer"])}</span><div style="font-size:0.7rem;color:#6c757d;">{dealer_pct:.0f}%</div></td>'
                row += f'<td>{badge}{date_html}</td>'
                row += '</tr>'
                return row
            
            with col_buy:
                st.subheader("▲ 三大法人 買超 TOP 15")
                html = '<table><thead><tr><th>排名</th><th>代號</th><th>名稱</th><th>合計</th><th>外資</th><th>投信</th><th>自營</th><th>連買</th></tr></thead><tbody>'
                for i, s in enumerate(buy_sorted, 1):
                    html += render_overall_row(i, s, is_buy=True)
                html += '</tbody></table>'
                st.markdown(html, unsafe_allow_html=True)
            
            with col_sell:
                st.subheader("▼ 三大法人 賣超 TOP 15")
                html = '<table><thead><tr><th>排名</th><th>代號</th><th>名稱</th><th>合計</th><th>外資</th><th>投信</th><th>自營</th><th>連賣</th></tr></thead><tbody>'
                for i, s in enumerate(sell_sorted, 1):
                    html += render_overall_row(i, s, is_buy=False)
                html += '</tbody></table>'
                st.markdown(html, unsafe_allow_html=True)
        
        # ===== 各別法人 tab (10 名 + 日期) =====
        for tab, key, title in [(tab1,'foreign','外資'),(tab2,'trust','投信'),(tab3,'dealer','自營商')]:
            with tab:
                col_buy, col_sell = st.columns(2)
                buy_sorted = sorted([s for s in latest_data if s[key] > 0], key=lambda x: x[key], reverse=True)[:10]
                sell_sorted = sorted([s for s in latest_data if s[key] < 0], key=lambda x: x[key])[:10]
                
                with col_buy:
                    st.subheader(f"▲ {title} 買超 TOP 10")
                    html = '<table><thead><tr><th>排名</th><th>代號</th><th>名稱</th><th>買超(張)</th><th>連買</th></tr></thead><tbody>'
                    for i, s in enumerate(buy_sorted, 1):
                        consec, direction, dates = calculate_consecutive(s['code'], history, key)
                        row_class = ''
                        badge = '<span class="badge badge-normal">1天</span>'
                        if direction == 'buy':
                            if consec >= 5:
                                row_class, badge = 'streak-5', f'<span class="badge badge-5">{consec}天</span>'
                            elif consec >= 3:
                                row_class, badge = 'streak-3', f'<span class="badge badge-3">{consec}天</span>'
                            elif consec >= 2:
                                row_class, badge = 'streak-2', f'<span class="badge badge-2">{consec}天</span>'
                        
                        date_str = format_dates_short(dates) if direction == 'buy' and consec >= 2 else ''
                        date_html = f'<div style="font-size:0.7rem;color:#6c757d;margin-top:0.3rem;">{date_str}</div>' if date_str else ''
                        
                        name = STOCK_NAMES.get(s['code']) or s.get('name') or s['code']
                        html += f'<tr class="{row_class}"><td>{i:02d}</td><td><strong>{s["code"]}</strong></td><td>{name}</td><td><span class="positive">+{format_number(s[key])}</span></td><td>{badge}{date_html}</td></tr>'
                    html += '</tbody></table>'
                    st.markdown(html, unsafe_allow_html=True)
                
                with col_sell:
                    st.subheader(f"▼ {title} 賣超 TOP 10")
                    html = '<table><thead><tr><th>排名</th><th>代號</th><th>名稱</th><th>賣超(張)</th><th>連賣</th></tr></thead><tbody>'
                    for i, s in enumerate(sell_sorted, 1):
                        consec, direction, dates = calculate_consecutive(s['code'], history, key)
                        row_class = ''
                        badge = '<span class="badge badge-normal">1天</span>'
                        if direction == 'sell':
                            if consec >= 5:
                                row_class, badge = 'streak-5', f'<span class="badge badge-5">{consec}天</span>'
                            elif consec >= 3:
                                row_class, badge = 'streak-3', f'<span class="badge badge-3">{consec}天</span>'
                            elif consec >= 2:
                                row_class, badge = 'streak-2', f'<span class="badge badge-2">{consec}天</span>'
                        
                        date_str = format_dates_short(dates) if direction == 'sell' and consec >= 2 else ''
                        date_html = f'<div style="font-size:0.7rem;color:#6c757d;margin-top:0.3rem;">{date_str}</div>' if date_str else ''
                        
                        name = STOCK_NAMES.get(s['code']) or s.get('name') or s['code']
                        html += f'<tr class="{row_class}"><td>{i:02d}</td><td><strong>{s["code"]}</strong></td><td>{name}</td><td><span class="negative">{format_number(s[key])}</span></td><td>{badge}{date_html}</td></tr>'
                    html += '</tbody></table>'
                    st.markdown(html, unsafe_allow_html=True)

# ==================== 成交量排行 ====================

else:
    st.subheader("💰 成交量排行 + 同產業推薦")
    
    market_stocks = [
        "2330","2454","2303","3034","3008","3711","2379","3661","6669","3017",
        "6488","3037","6770","2344","2408","3443","5483","3105","3711","2317",
        "2308","2382","2376","2474","2353","2356","2357","3231","2360","2049",
        "2327","2385","2395","2392","2891","2881","2882","2884","2886","2885",
        "2890","2887","2880","2883","2892","5880","5876","0050","0056","00878",
        "006208","00929","00919","00713","00940","1303","1301","1326","2002",
        "2105","2207","2912","1216","9910","1101","1102","2603","2609","2615",
        "2618","2610","2412","4904","3045","6505","8454","9921","5871",
    ]
    
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🔄 更新資料", type="primary", use_container_width=True):
            st.session_state['volume_data'] = None
    with col2:
        st.markdown('<span class="source-tag source-yahoo">📊 Yahoo Finance</span>', unsafe_allow_html=True)
    
    if 'volume_data' not in st.session_state or st.session_state.get('volume_data') is None:
        with st.spinner(f'正在查詢 {len(market_stocks)} 支股票...'):
            progress = st.progress(0)
            results = []
            for i, code in enumerate(market_stocks):
                data = fetch_yf_simple(code)
                if data:
                    results.append(data)
                progress.progress((i + 1) / len(market_stocks))
            progress.empty()
            st.session_state['volume_data'] = results
            st.session_state['volume_update_time'] = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    
    results = st.session_state.get('volume_data', [])
    
    if results:
        st.caption(f"📅 最後更新：{st.session_state.get('volume_update_time', 'N/A')}")
        
        # TOP 10 成交額
        top10 = sorted(results, key=lambda x: x['amount'], reverse=True)[:10]
        
        st.markdown("### 🏆 成交額 TOP 10")
        
        html = '<table><thead><tr><th>排名</th><th>代號</th><th>名稱</th><th>產業</th><th>收盤</th><th>漲跌幅</th><th>成交量</th><th>成交額</th></tr></thead><tbody>'
        for i, r in enumerate(top10, 1):
            cc = 'positive' if r['change'] > 0 else 'negative' if r['change'] < 0 else 'neutral'
            cs = '+' if r['change'] > 0 else ''
            html += f'<tr><td>{i:02d}</td><td><strong>{r["code"]}</strong></td><td>{r["name"]}</td><td>{r["industry"]}</td><td>${r["close"]:.2f}</td><td><span class="{cc}">{cs}{r["change_pct"]:.2f}%</span></td><td>{r["volume"]:,}</td><td><strong>{format_number(r["amount"])}</strong></td></tr>'
        html += '</tbody></table>'
        st.markdown(html, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 🔍 同產業推薦")
        st.caption("選擇 TOP 10 中的股票，查看同產業其他股票")
        
        stock_options = [f"#{i+1} {r['code']} {r['name']} ({r['industry']})" for i, r in enumerate(top10)]
        selected = st.selectbox("選擇股票", stock_options)
        
        selected_idx = stock_options.index(selected)
        selected_stock = top10[selected_idx]
        
        st.markdown(f"#### 與 **{selected_stock['name']} ({selected_stock['code']})** 同產業（{selected_stock['industry']}）")
        
        industry_codes = get_industry_stocks(selected_stock['industry'], exclude=selected_stock['code'])
        
        if not industry_codes:
            st.info("📊 該產業目前沒有其他追蹤股票")
        else:
            with st.spinner(f'查詢同產業 {len(industry_codes)} 支股票...'):
                industry_results = []
                for code in industry_codes:
                    found = next((r for r in results if r['code'] == code), None)
                    if found:
                        industry_results.append(found)
                    else:
                        data = fetch_yf_simple(code)
                        if data:
                            industry_results.append(data)
            
            if industry_results:
                industry_results.sort(key=lambda x: x['amount'], reverse=True)
                
                html = '<table><thead><tr><th>排名</th><th>代號</th><th>名稱</th><th>細分產業</th><th>收盤</th><th>漲跌幅</th><th>成交量</th><th>成交額</th></tr></thead><tbody>'
                for i, r in enumerate(industry_results, 1):
                    cc = 'positive' if r['change'] > 0 else 'negative' if r['change'] < 0 else 'neutral'
                    cs = '+' if r['change'] > 0 else ''
                    html += f'<tr><td>{i:02d}</td><td><strong>{r["code"]}</strong></td><td>{r["name"]}</td><td>{r["industry"]}</td><td>${r["close"]:.2f}</td><td><span class="{cc}">{cs}{r["change_pct"]:.2f}%</span></td><td>{r["volume"]:,}</td><td>{format_number(r["amount"])}</td></tr>'
                html += '</tbody></table>'
                st.markdown(html, unsafe_allow_html=True)
            else:
                st.info("📊 暫無同產業股票資料")
    else:
        st.info("👆 點擊「更新資料」開始查詢")

st.markdown("---")
st.caption("📊 資料來源：證交所 OpenAPI（法人）+ Yahoo Finance（成交量、個股） | ⚠️ 僅供參考，非投資建議")
