import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import json
from pathlib import Path

# 頁面設定
st.set_page_config(
    page_title="台股三大法人追蹤系統",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自訂 CSS 樣式
st.markdown("""
<style>
    .main {
        background-color: #07090f;
    }
    .stButton>button {
        background: linear-gradient(135deg, #0099cc, #00d4ff);
        color: #07090f;
        font-weight: bold;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        border: none;
    }
    .metric-card {
        background: #0d1220;
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .warning-row {
        background-color: rgba(245,197,24,0.15) !important;
        border-left: 3px solid #f5c518 !important;
    }
    .alert-row {
        background-color: rgba(255,77,77,0.2) !important;
        border-left: 3px solid #ff4d4d !important;
        animation: pulse 2s ease-in-out infinite;
    }
    @keyframes pulse {
        0%, 100% { background-color: rgba(255,77,77,0.2); }
        50% { background-color: rgba(255,77,77,0.3); }
    }
    h1 {
        color: #00d4ff;
        font-family: 'JetBrains Mono', monospace;
    }
    .stDataFrame {
        border: 1px solid rgba(0,212,255,0.2);
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# 建立資料夾結構
DATA_DIR = Path("data_storage")
DATA_DIR.mkdir(exist_ok=True)

HISTORY_FILE = DATA_DIR / "history.json"

# 載入歷史資料
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
        # 允許週末間隔
        if (d1 - d2).days <= 3:
            streak += 1
        else:
            break
    
    return streak

def update_history(rows, date_key, history_type):
    """更新歷史紀錄"""
    history = load_history()
    
    for row in rows:
        key = f"{row['code']}_{history_type}"
        if key not in history:
            history[key] = {
                'name': row['name'],
                'dates': []
            }
        
        if date_key not in history[key]['dates']:
            history[key]['dates'].append(date_key)
            # 只保留最近 60 天
            history[key]['dates'] = sorted(history[key]['dates'])[-60:]
    
    save_history(history)

def highlight_rows(row):
    """根據連續天數上色"""
    streak = row.get('連買天數', 0) or row.get('連賣天數', 0)
    
    if streak >= 5:
        return ['background-color: rgba(255,77,77,0.2); border-left: 3px solid #ff4d4d' for _ in row]
    elif streak >= 3:
        return ['background-color: rgba(245,197,24,0.15); border-left: 3px solid #f5c518' for _ in row]
    else:
        return ['' for _ in row]

def format_number(n):
    """格式化數字（萬、億）"""
    abs_n = abs(n)
    sign = '-' if n < 0 else ''
    
    if abs_n >= 100000000:
        return f"{sign}{abs_n/100000000:.2f}億"
    elif abs_n >= 10000:
        return f"{sign}{abs_n/10000:.1f}萬"
    else:
        return f"{n:,}"

def fetch_twse_data(date_str):
    """
    從證交所 API 獲取三大法人資料
    date_str: 格式 YYYYMMDD
    """
    import requests
    
    url = f"https://www.twse.com.tw/fund/T86?response=json&date={date_str}&selectType=ALL"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('stat') != 'OK':
            return None, f"證交所回應：{data.get('stat', '未知錯誤')}"
        
        if not data.get('data'):
            return None, "非交易日或資料尚未更新（盤後約 18:00-20:00 才有資料）"
        
        # 解析資料
        stocks = []
        for row in data['data']:
            if not row[0] or len(row[0].strip()) < 4:
                continue
            
            code = row[0].strip()
            name = row[1].strip()
            
            # 轉換數字（移除千分位逗號）
            def parse_num(s):
                try:
                    return int(s.replace(',', ''))
                except:
                    return 0
            
            foreign = parse_num(row[4])
            trust = parse_num(row[7])
            dealer = parse_num(row[10]) + parse_num(row[13])
            total = parse_num(row[14])
            
            stocks.append({
                'code': code,
                'name': name,
                'foreign': foreign,
                'trust': trust,
                'dealer': dealer,
                'total': total
            })
        
        return stocks, None
        
    except requests.exceptions.Timeout:
        return None, "連線逾時，請稍後再試"
    except requests.exceptions.RequestException as e:
        return None, f"網路錯誤：{str(e)}"
    except Exception as e:
        return None, f"資料處理錯誤：{str(e)}"

# ==================== 主程式 ====================

st.title("📈 台股三大法人追蹤系統")
st.markdown("### 各股買超 / 賣超 TOP 10 · 連續預警系統")

# 側邊欄
with st.sidebar:
    st.header("⚙️ 設定")
    
    # 日期選擇
    selected_date = st.date_input(
        "選擇查詢日期",
        value=datetime.now(),
        max_value=datetime.now()
    )
    
    # 更新按鈕
    fetch_button = st.button("🔄 更新資料", type="primary", use_container_width=True)
    
    st.markdown("---")
    st.info("💡 資料來源：證交所 T86\n\n⏰ 盤後 18:00 後才有資料\n\n📊 連買≥3天顯示黃色\n\n🔴 連買≥5天顯示紅色")

# 主要內容區
if fetch_button or 'data_loaded' not in st.session_state:
    date_key = selected_date.strftime("%Y%m%d")
    
    with st.spinner('正在從證交所獲取資料...'):
        stocks, error = fetch_twse_data(date_key)
    
    if error:
        st.error(f"❌ {error}")
        st.info("""
        **可能原因：**
        1. 選擇的日期為非交易日（週末或國定假日）
        2. 盤中或盤後資料尚未更新（建議 18:00 後使用）
        3. 證交所網站暫時無法連線
        """)
    else:
        # 分類買超與賣超
        buy_stocks = [s for s in stocks if s['total'] > 0]
        sell_stocks = [s for s in stocks if s['total'] < 0]
        
        # 排序並取前 10
        buy_top10 = sorted(buy_stocks, key=lambda x: x['total'], reverse=True)[:10]
        sell_top10 = sorted(sell_stocks, key=lambda x: x['total'])[:10]
        
        # 計算連續天數並更新歷史
        for stock in buy_top10:
            stock['streak'] = calculate_streak(stock['code'], date_key, 'buy')
        
        for stock in sell_top10:
            stock['streak'] = calculate_streak(stock['code'], date_key, 'sell')
        
        update_history(buy_top10, date_key, 'buy')
        update_history(sell_top10, date_key, 'sell')
        
        # 儲存到 session_state
        st.session_state['buy_data'] = buy_top10
        st.session_state['sell_data'] = sell_top10
        st.session_state['date_key'] = date_key
        st.session_state['data_loaded'] = True
        st.session_state['update_time'] = datetime.now()
        
        st.success(f"✅ 資料更新成功！共 {len(stocks)} 檔個股")

# 顯示資料（如果已載入）
if 'data_loaded' in st.session_state:
    buy_data = st.session_state.get('buy_data', [])
    sell_data = st.session_state.get('sell_data', [])
    date_key = st.session_state.get('date_key', '')
    
    # 統計資訊
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div style="color: #00d4ff; font-size: 0.8rem;">查詢日期</div>
            <div style="font-size: 1.5rem; font-weight: bold; color: #00d4ff;">
                {date_key[:4]}/{date_key[4:6]}/{date_key[6:8]}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        max_buy = max([s['streak'] for s in buy_data], default=0)
        color = "#ff4d4d" if max_buy >= 5 else "#f5c518" if max_buy >= 3 else "#00d4ff"
        st.markdown(f"""
        <div class="metric-card">
            <div style="color: {color}; font-size: 0.8rem;">最高連買</div>
            <div style="font-size: 1.5rem; font-weight: bold; color: {color};">
                {max_buy} 天
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        warn_count = len([s for s in buy_data if 3 <= s['streak'] < 5])
        st.markdown(f"""
        <div class="metric-card">
            <div style="color: #f5c518; font-size: 0.8rem;">黃色注意</div>
            <div style="font-size: 1.5rem; font-weight: bold; color: #f5c518;">
                {warn_count} 檔
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        alert_count = len([s for s in buy_data if s['streak'] >= 5])
        st.markdown(f"""
        <div class="metric-card">
            <div style="color: #ff4d4d; font-size: 0.8rem;">紅色警示</div>
            <div style="font-size: 1.5rem; font-weight: bold; color: #ff4d4d;">
                {alert_count} 檔
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # 警示通知
    alert_stocks = [s for s in buy_data if s['streak'] >= 5]
    if alert_stocks:
        alert_msg = "🔴 **連買警示觸發！**\n\n以下個股連續買超達 5 天以上：\n\n"
        for s in alert_stocks:
            alert_msg += f"- **{s['code']} {s['name']}** 連買 {s['streak']} 天\n"
        st.warning(alert_msg)
    
    # Tab 切換
    tab1, tab2 = st.tabs(["▲ 買超 TOP 10", "▼ 賣超 TOP 10"])
    
    with tab1:
        st.subheader("▲ 三大法人合計買超 TOP 10")
        
        if buy_data:
            # 建立 DataFrame
            df_buy = pd.DataFrame([{
                '排名': i+1,
                '代號': s['code'],
                '名稱': s['name'],
                '外資(張)': format_number(s['foreign']),
                '投信(張)': format_number(s['trust']),
                '自營(張)': format_number(s['dealer']),
                '合計(張)': format_number(s['total']),
                '連買天數': s['streak']
            } for i, s in enumerate(buy_data)])
            
            # 套用樣式
            styled_df = df_buy.style.apply(highlight_rows, axis=1)
            
            st.dataframe(styled_df, use_container_width=True, height=450)
            
            # 圖例
            st.markdown("""
            <div style="display: flex; gap: 1rem; margin-top: 1rem; font-size: 0.85rem;">
                <div><span style="display: inline-block; width: 12px; height: 12px; background: rgba(68,85,102,0.4); border-radius: 3px;"></span> 正常 (1-2天)</div>
                <div><span style="display: inline-block; width: 12px; height: 12px; background: rgba(245,197,24,0.5); border-radius: 3px;"></span> 注意 連買≥3天</div>
                <div><span style="display: inline-block; width: 12px; height: 12px; background: rgba(255,77,77,0.5); border-radius: 3px;"></span> 警示 連買≥5天</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("本日無買超資料")
    
    with tab2:
        st.subheader("▼ 三大法人合計賣超 TOP 10")
        
        if sell_data:
            df_sell = pd.DataFrame([{
                '排名': i+1,
                '代號': s['code'],
                '名稱': s['name'],
                '外資(張)': format_number(s['foreign']),
                '投信(張)': format_number(s['trust']),
                '自營(張)': format_number(s['dealer']),
                '合計(張)': format_number(s['total']),
                '連賣天數': s['streak']
            } for i, s in enumerate(sell_data)])
            
            styled_df = df_sell.style.apply(highlight_rows, axis=1)
            
            st.dataframe(styled_df, use_container_width=True, height=450)
            
            st.markdown("""
            <div style="display: flex; gap: 1rem; margin-top: 1rem; font-size: 0.85rem;">
                <div><span style="display: inline-block; width: 12px; height: 12px; background: rgba(68,85,102,0.4); border-radius: 3px;"></span> 正常 (1-2天)</div>
                <div><span style="display: inline-block; width: 12px; height: 12px; background: rgba(255,140,66,0.5); border-radius: 3px;"></span> 注意 連賣≥3天</div>
                <div><span style="display: inline-block; width: 12px; height: 12px; background: rgba(204,34,0,0.6); border-radius: 3px;"></span> 警示 連賣≥5天</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("本日無賣超資料")
    
    # 更新時間
    if 'update_time' in st.session_state:
        update_time = st.session_state['update_time']
        st.caption(f"⏱️ 最後更新：{update_time.strftime('%Y-%m-%d %H:%M:%S')}")

else:
    st.info("👆 請點擊側邊欄的「更新資料」按鈕載入資料")

# 頁尾
st.markdown("---")
st.caption("📊 資料來源：證交所 T86 | ⚠️ 僅供參考，非投資建議 | 💾 歷史紀錄存於本機裝置")
