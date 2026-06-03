import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from datetime import datetime, timedelta
import json
from pathlib import Path
import plotly.graph_objects as go
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
    
    .metric-card {background: #ffffff; border: 1px solid #dee2e6; border-radius: 12px; padding: 1.2rem; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08); margin-bottom: 1rem;}
    .stat-label {font-size: 0.85rem; color: #6c757d; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.5rem; font-weight: 600;}
    .stat-value {font-size: 1.8rem; font-weight: 700; margin: 0;}
    @media (max-width: 768px) {.stat-value {font-size: 1.4rem;}}
    
    .stButton {width: 100%;}
    .stButton>button {background: #4a90e2; color: #ffffff; font-weight: 600; border: none; border-radius: 10px; padding: 0.75rem 1.5rem; width: 100%; box-shadow: 0 2px 8px rgba(74, 144, 226, 0.3); transition: all 0.3s ease;}
    .stButton>button:hover {background: #357abd; box-shadow: 0 4px 12px rgba(74, 144, 226, 0.4); transform: translateY(-2px);}
    
    table {width: 100%; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08); border-collapse: separate; border-spacing: 0;}
    thead th {background: #e9ecef; color: #2c3e50; font-weight: 700; padding: 1rem 0.75rem; text-align: center; border: none; font-size: 0.9rem;}
    @media (max-width: 768px) {thead th {padding: 0.75rem 0.5rem; font-size: 0.75rem;}}
    tbody td {background: #ffffff; color: #495057; padding: 0.9rem 0.75rem; text-align: center; border-bottom: 1px solid #f1f3f5; font-size: 0.9rem;}
    @media (max-width: 768px) {tbody td {padding: 0.7rem 0.5rem; font-size: 0.8rem;}}
    tbody tr:nth-child(even) td {background: #f8f9fa;}
    tbody tr:hover td {background: #dee2e6;}
    
    /* 連續天數警示 - 整列同色 */
    tr.streak-2 td {background: #fff9e6 !important;}  /* 淺黃 */
    tr.streak-3 td {background: #ffd9a8 !important;}  /* 橘色 */
    tr.streak-5 td {background: #ffb3b3 !important;}  /* 紅色 */
    
    .positive {color: #28a745 !important; font-weight: 700;}
    .negative {color: #dc3545 !important; font-weight: 700;}
    .neutral {color: #6c757d !important;}
    
    .badge {display: inline-block; padding: 0.35rem 0.75rem; border-radius: 12px; font-size: 0.8rem; font-weight: 700; white-space: nowrap;}
    .badge-2 {background: #fff3cd; color: #856404; border: 1px solid #ffc107;}
    .badge-3 {background: #ffe0b3; color: #b96d00; border: 1px solid #ff8c00;}
    .badge-5 {background: #ffcccc; color: #b30000; border: 1px solid #dc3545;}
    
    .stTabs [data-baseweb="tab-list"] {gap: 8px; background: #ffffff; padding: 0.5rem; border-radius: 12px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);}
    .stTabs [data-baseweb="tab"] {background: transparent; color: #6c757d; border-radius: 8px; padding: 0.75rem 1.5rem; font-weight: 600;}
    .stTabs [aria-selected="true"] {background: #4a90e2; color: white;}
    
    [data-testid="stMetricValue"] {color: #2c3e50; font-size: 1.6rem;}
    @media (max-width: 768px) {[data-testid="stMetricValue"] {font-size: 1.2rem;}}
</style>
""", unsafe_allow_html=True)

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

def format_lots(n):
    """轉換股數為張數"""
    if n is None or n == 0:
        return "0"
    lots = n / 1000  # 1 張 = 1000 股
    abs_lots = abs(lots)
    sign = '-' if lots < 0 else ''
    if abs_lots >= 10000:
        return f"{sign}{abs_lots/10000:.1f}萬張"
    else:
        return f"{lots:,.0f}張"

def calculate_streak(dates_list, target_dates):
    """計算連續天數（連續日期）"""
    if not target_dates:
        return 0
    
    # 排序日期（降序，最新在前）
    all_dates = sorted(dates_list, reverse=True)
    target_set = set(target_dates)
    
    streak = 0
    for d in all_dates:
        if d in target_set:
            streak += 1
        else:
            break
    return streak

def get_streak_class(streak):
    """根據連續天數返回 CSS class"""
    if streak >= 5:
        return "streak-5"
    elif streak >= 3:
        return "streak-3"
    elif streak >= 2:
        return "streak-2"
    return ""

def get_streak_badge(streak):
    """連續天數徽章"""
    if streak >= 5:
        return f'<span class="badge badge-5">連{streak}天</span>'
    elif streak >= 3:
        return f'<span class="badge badge-3">連{streak}天</span>'
    elif streak >= 2:
        return f'<span class="badge badge-2">連{streak}天</span>'
    return f'{streak}天' if streak > 0 else '-'

# ==================== FinMind API ====================

FINMIND_URL = "https://api.finmindtrade.com/api/v4/data"

@st.cache_data(ttl=86400)  # 快取 24 小時
def fetch_stock_info():
    """取得所有台股資訊（含產業類別）"""
    try:
        params = {"dataset": "TaiwanStockInfo"}
        resp = requests.get(FINMIND_URL, params=params, timeout=30)
        
        if resp.status_code != 200:
            return None
        
        data = resp.json()
        if data.get('status') != 200:
            return None
        
        df = pd.DataFrame(data['data'])
        # 過濾上市櫃股票（排除權證、ETN 等）
        df = df[df['type'].isin(['twse', 'tpex'])]
        return df
    except Exception as e:
        st.warning(f"取得股票資訊失敗：{e}")
        return None

@st.cache_data(ttl=1800)  # 快取 30 分鐘
def fetch_institutional_data(start_date, end_date):
    """取得指定日期範圍的三大法人資料"""
    try:
        params = {
            "dataset": "TaiwanStockInstitutionalInvestorsBuySell",
            "start_date": start_date,
            "end_date": end_date,
        }
        resp = requests.get(FINMIND_URL, params=params, timeout=60)
        
        if resp.status_code != 200:
            return None
        
        data = resp.json()
        if data.get('status') != 200:
            return None
        
        df = pd.DataFrame(data['data'])
        return df
    except Exception as e:
        st.warning(f"取得法人資料失敗：{e}")
        return None

@st.cache_data(ttl=1800)
def fetch_market_price(start_date, end_date):
    """取得指定日期範圍的股價資料"""
    try:
        params = {
            "dataset": "TaiwanStockPrice",
            "start_date": start_date,
            "end_date": end_date,
        }
        resp = requests.get(FINMIND_URL, params=params, timeout=60)
        
        if resp.status_code != 200:
            return None
        
        data = resp.json()
        if data.get('status') != 200:
            return None
        
        df = pd.DataFrame(data['data'])
        return df
    except Exception as e:
        st.warning(f"取得股價失敗：{e}")
        return None

@st.cache_data(ttl=300)
def fetch_yfinance_data(stock_code, period="3mo"):
    """Yahoo Finance 補充資料"""
    try:
        for suffix in [".TW", ".TWO"]:
            ticker = yf.Ticker(f"{stock_code}{suffix}")
            hist = ticker.history(period=period)
            if not hist.empty:
                try:
                    info = ticker.info
                except:
                    info = {}
                return {
                    'history': hist,
                    'info': info
                }
        return None
    except:
        return None

# ==================== 核心分析邏輯 ====================

def get_recent_trading_days(num_days=14):
    """取得最近 N 個交易日（排除週末）"""
    days = []
    current = datetime.now()
    
    # 多預留幾天，因為要排除週末
    while len(days) < num_days + 5:
        if current.weekday() < 5:  # 週一到週五
            days.append(current.strftime("%Y-%m-%d"))
        current -= timedelta(days=1)
    
    return days

def calculate_institutional_rankings(inst_df, stock_info_df, target_date=None):
    """計算三大法人買賣超排行 + 連續天數"""
    if inst_df is None or inst_df.empty:
        return None
    
    # 法人類型對照
    inst_types = {
        'Foreign_Investor': '外資',
        'Investment_Trust': '投信',
        'Dealer_self': '自營商(自行)',
        'Dealer_Hedging': '自營商(避險)',
    }
    
    # 取得最新日期
    if target_date is None:
        target_date = inst_df['date'].max()
    
    # 整合自營商（自行+避險）
    inst_df = inst_df.copy()
    inst_df['net'] = inst_df['buy'] - inst_df['sell']
    
    # 建立股票名稱對照
    stock_name_map = {}
    industry_map = {}
    if stock_info_df is not None:
        for _, row in stock_info_df.iterrows():
            stock_name_map[row['stock_id']] = row['stock_name']
            industry_map[row['stock_id']] = row.get('industry_category', '其他')
    
    results = {}
    
    for inst_eng, inst_zh in [
        ('Foreign_Investor', '外資'),
        ('Investment_Trust', '投信'),
    ]:
        inst_data = inst_df[inst_df['name'] == inst_eng].copy()
        
        if inst_data.empty:
            continue
        
        # 最新日期的買賣超
        latest = inst_data[inst_data['date'] == target_date].copy()
        
        # 計算每支股票的連續買/賣天數
        all_dates = sorted(inst_data['date'].unique(), reverse=True)
        
        stock_streaks = {}
        for stock_id in latest['stock_id'].unique():
            stock_history = inst_data[inst_data['stock_id'] == stock_id].copy()
            stock_history = stock_history.sort_values('date', ascending=False)
            
            # 連續買超
            buy_streak = 0
            for _, row in stock_history.iterrows():
                if row['net'] > 0:
                    buy_streak += 1
                else:
                    break
            
            # 連續賣超
            sell_streak = 0
            for _, row in stock_history.iterrows():
                if row['net'] < 0:
                    sell_streak += 1
                else:
                    break
            
            stock_streaks[stock_id] = {
                'buy_streak': buy_streak,
                'sell_streak': sell_streak
            }
        
        # 加入股票名稱、產業、連續天數
        latest['name_zh'] = latest['stock_id'].map(stock_name_map).fillna(latest['stock_id'])
        latest['industry'] = latest['stock_id'].map(industry_map).fillna('其他')
        latest['buy_streak'] = latest['stock_id'].map(lambda x: stock_streaks.get(x, {}).get('buy_streak', 0))
        latest['sell_streak'] = latest['stock_id'].map(lambda x: stock_streaks.get(x, {}).get('sell_streak', 0))
        
        # 排行
        buy_top10 = latest.sort_values('net', ascending=False).head(10)
        sell_top10 = latest.sort_values('net', ascending=True).head(10)
        
        results[inst_zh] = {
            'buy_top10': buy_top10,
            'sell_top10': sell_top10,
            'target_date': target_date
        }
    
    # 處理自營商（合併自行 + 避險）
    dealer_data = inst_df[inst_df['name'].isin(['Dealer_self', 'Dealer_Hedging'])].copy()
    if not dealer_data.empty:
        dealer_grouped = dealer_data.groupby(['date', 'stock_id'])['net'].sum().reset_index()
        
        latest_dealer = dealer_grouped[dealer_grouped['date'] == target_date].copy()
        
        # 計算連續天數
        stock_streaks = {}
        for stock_id in latest_dealer['stock_id'].unique():
            stock_history = dealer_grouped[dealer_grouped['stock_id'] == stock_id].copy()
            stock_history = stock_history.sort_values('date', ascending=False)
            
            buy_streak = 0
            for _, row in stock_history.iterrows():
                if row['net'] > 0:
                    buy_streak += 1
                else:
                    break
            
            sell_streak = 0
            for _, row in stock_history.iterrows():
                if row['net'] < 0:
                    sell_streak += 1
                else:
                    break
            
            stock_streaks[stock_id] = {'buy_streak': buy_streak, 'sell_streak': sell_streak}
        
        latest_dealer['name_zh'] = latest_dealer['stock_id'].map(stock_name_map).fillna(latest_dealer['stock_id'])
        latest_dealer['industry'] = latest_dealer['stock_id'].map(industry_map).fillna('其他')
        latest_dealer['buy_streak'] = latest_dealer['stock_id'].map(lambda x: stock_streaks.get(x, {}).get('buy_streak', 0))
        latest_dealer['sell_streak'] = latest_dealer['stock_id'].map(lambda x: stock_streaks.get(x, {}).get('sell_streak', 0))
        
        buy_top10 = latest_dealer.sort_values('net', ascending=False).head(10)
        sell_top10 = latest_dealer.sort_values('net', ascending=True).head(10)
        
        results['自營商'] = {
            'buy_top10': buy_top10,
            'sell_top10': sell_top10,
            'target_date': target_date
        }
    
    return results

def calculate_volume_rankings(price_df, stock_info_df, target_date=None):
    """計算成交量排行 + 產業分類"""
    if price_df is None or price_df.empty:
        return None
    
    if target_date is None:
        target_date = price_df['date'].max()
    
    latest = price_df[price_df['date'] == target_date].copy()
    
    # 建立對照
    stock_name_map = {}
    industry_map = {}
    if stock_info_df is not None:
        for _, row in stock_info_df.iterrows():
            stock_name_map[row['stock_id']] = row['stock_name']
            industry_map[row['stock_id']] = row.get('industry_category', '其他')
    
    latest['name_zh'] = latest['stock_id'].map(stock_name_map).fillna(latest['stock_id'])
    latest['industry'] = latest['stock_id'].map(industry_map).fillna('其他')
    latest['change'] = latest['close'] - latest['open']
    latest['change_pct'] = ((latest['close'] - latest['open']) / latest['open'] * 100).round(2)
    
    # 排除無產業分類的（通常是 ETF 等）
    latest = latest[latest['industry'] != '其他']
    
    volume_top10 = latest.sort_values('Trading_Volume', ascending=False).head(10)
    
    return {
        'top10': volume_top10,
        'all_data': latest,
        'target_date': target_date
    }

def get_industry_peers(stock_id, industry, all_data, top_n=10):
    """取得同產業的其他股票"""
    peers = all_data[all_data['industry'] == industry].copy()
    peers = peers[peers['stock_id'] != stock_id]  # 排除自己
    peers = peers.sort_values('Trading_Volume', ascending=False).head(top_n)
    return peers

# ==================== 主程式 ====================

col_title, col_mode = st.columns([3, 1])

with col_title:
    st.title("📈 台股籌碼分析系統")
    st.caption("✨ 資料來源：FinMind + Yahoo Finance")

with col_mode:
    st.write("")
    mode = st.radio(
        "模式",
        ["大盤排行", "個股分析", "成交量同業"],
        horizontal=True,
        label_visibility="collapsed"
    )

st.markdown("---")

# ==================== 大盤排行（三大法人）====================

if mode == "大盤排行":
    st.subheader("📊 三大法人買賣超排行")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🔄 載入/更新資料", type="primary", use_container_width=True):
            # 清除快取
            fetch_institutional_data.clear()
            st.session_state.pop('inst_results', None)
    
    with col2:
        days_back = st.selectbox("追蹤天數", [14, 21, 30], index=0, help="分析過去 N 天的法人連續買賣")
    
    with col3:
        st.info(f"💡 取得最近 {days_back} 個交易日，計算連續買賣天數")
    
    # 載入資料
    if 'inst_results' not in st.session_state:
        with st.spinner("正在載入大盤法人資料（首次載入約需 30-60 秒）..."):
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=days_back + 10)).strftime("%Y-%m-%d")
            
            stock_info = fetch_stock_info()
            inst_df = fetch_institutional_data(start_date, end_date)
            
            if inst_df is not None and not inst_df.empty:
                results = calculate_institutional_rankings(inst_df, stock_info)
                st.session_state['inst_results'] = results
                st.session_state['inst_load_time'] = datetime.now().strftime("%Y/%m/%d %H:%M")
            else:
                st.error("❌ 無法取得法人資料，請稍後再試")
                st.info("可能原因：FinMind API 暫時無法存取，或資料尚未更新")
    
    # 顯示結果
    if 'inst_results' in st.session_state and st.session_state['inst_results']:
        results = st.session_state['inst_results']
        
        # 顏色說明
        st.markdown("""
        **連續天數顏色說明：** 
        <span style="background:#fff9e6; padding:4px 10px; border-radius:4px;">🟡 連2天</span>
        　<span style="background:#ffd9a8; padding:4px 10px; border-radius:4px;">🟠 連3天以上</span>
        　<span style="background:#ffb3b3; padding:4px 10px; border-radius:4px;">🔴 連5天以上</span>
        """, unsafe_allow_html=True)
        
        # 顯示資料日期
        if results:
            sample = list(results.values())[0]
            st.caption(f"📅 資料日期：{sample['target_date']} ｜ 更新時間：{st.session_state.get('inst_load_time', 'N/A')}")
        
        st.markdown("---")
        
        # 三大法人分頁
        tabs = st.tabs([f"💼 {name}" for name in results.keys()])
        
        for idx, (inst_name, data) in enumerate(results.items()):
            with tabs[idx]:
                buy_top10 = data['buy_top10']
                sell_top10 = data['sell_top10']
                
                # 子分頁：買超 / 賣超
                sub_tab1, sub_tab2 = st.tabs(["▲ 買超 TOP 10", "▼ 賣超 TOP 10"])
                
                with sub_tab1:
                    st.subheader(f"{inst_name} 買超 TOP 10")
                    
                    if buy_top10.empty:
                        st.info("無買超資料")
                    else:
                        html = '<table><thead><tr>'
                        html += '<th>排名</th><th>代號</th><th>名稱</th><th>產業</th>'
                        html += '<th>買進(張)</th><th>賣出(張)</th><th>買賣超(張)</th><th>連續</th>'
                        html += '</tr></thead><tbody>'
                        
                        for i, (_, row) in enumerate(buy_top10.iterrows(), 1):
                            streak = row['buy_streak']
                            row_class = get_streak_class(streak) if streak >= 2 else ""
                            
                            buy_lots = row.get('buy', 0) / 1000
                            sell_lots = row.get('sell', 0) / 1000
                            net_lots = row['net'] / 1000
                            
                            html += f'<tr class="{row_class}">'
                            html += f'<td>{i:02d}</td>'
                            html += f'<td><strong>{row["stock_id"]}</strong></td>'
                            html += f'<td>{row["name_zh"]}</td>'
                            html += f'<td style="font-size:0.85rem;">{row["industry"]}</td>'
                            html += f'<td>{buy_lots:,.0f}</td>'
                            html += f'<td>{sell_lots:,.0f}</td>'
                            html += f'<td><span class="positive">+{net_lots:,.0f}</span></td>'
                            html += f'<td>{get_streak_badge(streak)}</td>'
                            html += f'</tr>'
                        
                        html += '</tbody></table>'
                        st.markdown(html, unsafe_allow_html=True)
                
                with sub_tab2:
                    st.subheader(f"{inst_name} 賣超 TOP 10")
                    
                    if sell_top10.empty:
                        st.info("無賣超資料")
                    else:
                        html = '<table><thead><tr>'
                        html += '<th>排名</th><th>代號</th><th>名稱</th><th>產業</th>'
                        html += '<th>買進(張)</th><th>賣出(張)</th><th>買賣超(張)</th><th>連續</th>'
                        html += '</tr></thead><tbody>'
                        
                        for i, (_, row) in enumerate(sell_top10.iterrows(), 1):
                            streak = row['sell_streak']
                            row_class = get_streak_class(streak) if streak >= 2 else ""
                            
                            buy_lots = row.get('buy', 0) / 1000
                            sell_lots = row.get('sell', 0) / 1000
                            net_lots = row['net'] / 1000
                            
                            html += f'<tr class="{row_class}">'
                            html += f'<td>{i:02d}</td>'
                            html += f'<td><strong>{row["stock_id"]}</strong></td>'
                            html += f'<td>{row["name_zh"]}</td>'
                            html += f'<td style="font-size:0.85rem;">{row["industry"]}</td>'
                            html += f'<td>{buy_lots:,.0f}</td>'
                            html += f'<td>{sell_lots:,.0f}</td>'
                            html += f'<td><span class="negative">{net_lots:,.0f}</span></td>'
                            html += f'<td>{get_streak_badge(streak)}</td>'
                            html += f'</tr>'
                        
                        html += '</tbody></table>'
                        st.markdown(html, unsafe_allow_html=True)

# ==================== 成交量同業比較 ====================

elif mode == "成交量同業":
    st.subheader("💰 成交量 TOP 10 + 同業比較")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if st.button("🔄 載入/更新", type="primary", use_container_width=True):
            fetch_market_price.clear()
            st.session_state.pop('volume_results', None)
    
    with col2:
        st.info("💡 顯示當日成交量前 10 名，並提供同產業的其他公司排行")
    
    # 載入資料
    if 'volume_results' not in st.session_state:
        with st.spinner("正在載入大盤股價資料..."):
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
            
            stock_info = fetch_stock_info()
            price_df = fetch_market_price(start_date, end_date)
            
            if price_df is not None and not price_df.empty:
                results = calculate_volume_rankings(price_df, stock_info)
                st.session_state['volume_results'] = results
                st.session_state['volume_load_time'] = datetime.now().strftime("%Y/%m/%d %H:%M")
            else:
                st.error("❌ 無法取得股價資料")
    
    if 'volume_results' in st.session_state and st.session_state['volume_results']:
        results = st.session_state['volume_results']
        top10 = results['top10']
        all_data = results['all_data']
        
        st.caption(f"📅 資料日期：{results['target_date']} ｜ 更新時間：{st.session_state.get('volume_load_time', 'N/A')}")
        st.markdown("---")
        
        # 成交量 TOP 10 表格
        st.subheader("📊 成交量 TOP 10")
        
        html = '<table><thead><tr>'
        html += '<th>排名</th><th>代號</th><th>名稱</th><th>產業</th>'
        html += '<th>收盤</th><th>漲跌%</th><th>成交量(張)</th><th>成交金額</th>'
        html += '</tr></thead><tbody>'
        
        for i, (_, row) in enumerate(top10.iterrows(), 1):
            volume_lots = row['Trading_Volume'] / 1000
            amount = row['Trading_money'] if 'Trading_money' in row else (row['close'] * row['Trading_Volume'])
            change_pct = row['change_pct']
            change_class = 'positive' if change_pct > 0 else 'negative' if change_pct < 0 else 'neutral'
            change_sign = '+' if change_pct > 0 else ''
            
            html += f'<tr>'
            html += f'<td>{i:02d}</td>'
            html += f'<td><strong>{row["stock_id"]}</strong></td>'
            html += f'<td>{row["name_zh"]}</td>'
            html += f'<td style="font-size:0.85rem;">{row["industry"]}</td>'
            html += f'<td>${row["close"]:.2f}</td>'
            html += f'<td><span class="{change_class}">{change_sign}{change_pct:.2f}%</span></td>'
            html += f'<td>{volume_lots:,.0f}</td>'
            html += f'<td>{format_number(amount)}</td>'
            html += f'</tr>'
        
        html += '</tbody></table>'
        st.markdown(html, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 選擇查看同業
        st.subheader("🔍 查看同業排行")
        
        selected_stock = st.selectbox(
            "選擇要查看同業的股票",
            options=top10['stock_id'].tolist(),
            format_func=lambda x: f"{x} {top10[top10['stock_id']==x]['name_zh'].values[0]} ({top10[top10['stock_id']==x]['industry'].values[0]})"
        )
        
        if selected_stock:
            selected_row = top10[top10['stock_id'] == selected_stock].iloc[0]
            industry = selected_row['industry']
            
            st.markdown(f"### 📂 {industry} 產業 - 成交量排行")
            st.caption(f"目標股票：{selected_stock} {selected_row['name_zh']}（成交量大盤第 {top10[top10['stock_id']==selected_stock].index[0]+1} 名）")
            
            peers = get_industry_peers(selected_stock, industry, all_data, top_n=15)
            
            if peers.empty:
                st.info(f"{industry} 產業沒有其他股票資料")
            else:
                html = '<table><thead><tr>'
                html += '<th>排名</th><th>代號</th><th>名稱</th>'
                html += '<th>收盤</th><th>漲跌%</th><th>成交量(張)</th><th>成交金額</th>'
                html += '</tr></thead><tbody>'
                
                # 先把目標股票放最上面
                target_lots = selected_row['Trading_Volume'] / 1000
                target_amount = selected_row.get('Trading_money', selected_row['close'] * selected_row['Trading_Volume'])
                target_change = selected_row['change_pct']
                target_change_class = 'positive' if target_change > 0 else 'negative' if target_change < 0 else 'neutral'
                target_sign = '+' if target_change > 0 else ''
                
                html += f'<tr style="background:#fff9e6 !important;">'
                html += f'<td>★</td>'
                html += f'<td><strong>{selected_stock}</strong></td>'
                html += f'<td><strong>{selected_row["name_zh"]}</strong></td>'
                html += f'<td>${selected_row["close"]:.2f}</td>'
                html += f'<td><span class="{target_change_class}">{target_sign}{target_change:.2f}%</span></td>'
                html += f'<td>{target_lots:,.0f}</td>'
                html += f'<td>{format_number(target_amount)}</td>'
                html += f'</tr>'
                
                for i, (_, row) in enumerate(peers.iterrows(), 1):
                    volume_lots = row['Trading_Volume'] / 1000
                    amount = row.get('Trading_money', row['close'] * row['Trading_Volume'])
                    change_pct = row['change_pct']
                    change_class = 'positive' if change_pct > 0 else 'negative' if change_pct < 0 else 'neutral'
                    change_sign = '+' if change_pct > 0 else ''
                    
                    html += f'<tr>'
                    html += f'<td>{i:02d}</td>'
                    html += f'<td><strong>{row["stock_id"]}</strong></td>'
                    html += f'<td>{row["name_zh"]}</td>'
                    html += f'<td>${row["close"]:.2f}</td>'
                    html += f'<td><span class="{change_class}">{change_sign}{change_pct:.2f}%</span></td>'
                    html += f'<td>{volume_lots:,.0f}</td>'
                    html += f'<td>{format_number(amount)}</td>'
                    html += f'</tr>'
                
                html += '</tbody></table>'
                st.markdown(html, unsafe_allow_html=True)
                
                st.caption("⭐ 黃色高亮 = 您選擇的目標股票")

# ==================== 個股分析 ====================

else:
    st.subheader("🔍 個股查詢與分析")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        stock_code = st.text_input("股票代號", value="2330").strip()
    
    with col2:
        period = st.selectbox("查詢期間", ["1個月", "3個月", "6個月", "1年"], index=1)
    
    with col3:
        st.write("")
        st.write("")
        analyze_btn = st.button("🔍 開始查詢", type="primary", use_container_width=True)
    
    period_map = {"1個月": "1mo", "3個月": "3mo", "6個月": "6mo", "1年": "1y"}
    
    if analyze_btn and stock_code:
        with st.spinner('正在查詢中...'):
            # Yahoo Finance 資料
            yf_data = fetch_yfinance_data(stock_code, period_map[period])
            
            # 從 FinMind 取得股票資訊
            stock_info = fetch_stock_info()
            stock_name = stock_code
            industry = "未知"
            
            if stock_info is not None:
                stock_row = stock_info[stock_info['stock_id'] == stock_code]
                if not stock_row.empty:
                    stock_name = stock_row.iloc[0]['stock_name']
                    industry = stock_row.iloc[0].get('industry_category', '未知')
        
        if not yf_data:
            st.error(f"❌ 查無股票代號 {stock_code}")
        else:
            hist = yf_data['history']
            info = yf_data['info']
            
            # 計算數據
            latest = hist.iloc[-1]
            prev = hist.iloc[-2] if len(hist) > 1 else latest
            change = latest['Close'] - prev['Close']
            change_pct = (change / prev['Close']) * 100 if prev['Close'] > 0 else 0
            
            st.markdown(f"### {stock_name} ({stock_code})")
            st.caption(f"📂 產業類別：{industry}")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                delta_color = "normal" if change >= 0 else "inverse"
                st.metric("收盤價", f"${latest['Close']:.2f}", f"{change:+.2f} ({change_pct:+.2f}%)", delta_color=delta_color)
            
            with col2:
                st.metric("成交量", f"{int(latest['Volume']) // 1000:,} 張")
            
            with col3:
                st.metric("最高", f"${latest['High']:.2f}")
            
            with col4:
                st.metric("最低", f"${latest['Low']:.2f}")
            
            st.markdown("---")
            
            tab1, tab2, tab3 = st.tabs(["📈 K線圖", "📊 成交量", "📄 公司資訊"])
            
            hist['MA5'] = hist['Close'].rolling(window=5).mean()
            hist['MA20'] = hist['Close'].rolling(window=20).mean()
            hist['MA60'] = hist['Close'].rolling(window=60).mean()
            
            with tab1:
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
                    yaxis_title='價格 (TWD)', template='plotly_white',
                    height=500, xaxis_rangeslider_visible=False,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with tab2:
                fig_vol = go.Figure()
                colors = ['#dc3545' if hist['Close'].iloc[i] > hist['Open'].iloc[i] else '#28a745' for i in range(len(hist))]
                fig_vol.add_trace(go.Bar(x=hist.index, y=hist['Volume'] / 1000, name='成交量', marker_color=colors))
                
                fig_vol.update_layout(
                    yaxis_title='成交量 (千張)', template='plotly_white', height=400
                )
                st.plotly_chart(fig_vol, use_container_width=True)
            
            with tab3:
                if info:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**📊 基本資訊**")
                        st.write(f"**產業：** {industry}")
                        st.write(f"**英文名：** {info.get('longName', 'N/A')}")
                    
                    with col2:
                        st.markdown("**💰 財務指標**")
                        if info.get('marketCap'):
                            mc = info['marketCap']
                            if mc >= 1e12:
                                st.write(f"**市值：** {mc/1e12:.2f} 兆")
                            elif mc >= 1e8:
                                st.write(f"**市值：** {mc/1e8:.2f} 億")
                        if info.get('trailingPE'):
                            st.write(f"**本益比：** {info['trailingPE']:.2f}")
                        if info.get('dividendYield'):
                            st.write(f"**股息殖利率：** {info['dividendYield']*100:.2f}%")

# 頁尾
st.markdown("---")
st.caption("📊 資料來源：FinMind API + Yahoo Finance | ⚠️ 僅供參考，非投資建議")
st.caption("💡 FinMind 免費版：300 次/小時")
