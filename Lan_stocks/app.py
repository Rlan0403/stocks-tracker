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
    initial_sidebar_state="expanded"
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
        padding: 0.5rem 2rem;
    }
    .metric-card {
        background: #0d1220;
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 10px;
        padding: 1rem;
    }
    .alert-box {
        background: rgba(255,77,77,0.15);
        border-left: 4px solid #ff4d4d;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .success-box {
        background: rgba(0,232,130,0.15);
        border-left: 4px solid #00e882;
        padding: 1rem;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# 資料夾結構
DATA_DIR = Path("data_storage")
DATA_DIR.mkdir(exist_ok=True)

# ==================== API 函數 ====================

def fetch_stock_price(stock_code, date_str):
    """獲取個股收盤資料"""
    try:
        url = f"https://openapi.twse.com.tw/v1/opendata/t187ap14_L"
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
    """獲取集保戶股權分散表"""
    try:
        # 使用政府資料開放平台
        url = "https://www.tdcc.com.tw/opendata/getOD.ashx?id=1-5"
        response = requests.get(url, timeout=15)
        data = response.json()
        
        for item in data:
            if item.get('證券代號') == stock_code:
                return {
                    'date': item.get('資料日期'),
                    'over_1000': int(item.get('持股1,000張以上', 0)),
                    'under_10': int(item.get('持股10張以下', 0)),
                    'total_holders': int(item.get('持股人數', 0))
                }
        return None
    except:
        return None

def fetch_monthly_revenue(stock_code):
    """獲取每月營收"""
    try:
        url = "https://openapi.twse.com.tw/v1/opendata/t187ap05_P"
        response = requests.get(url, timeout=15)
        data = response.json()
        
        revenue_data = []
        for item in data:
            if item.get('公司代號') == stock_code:
                revenue_data.append({
                    'month': item.get('資料年月'),
                    'revenue': float(item.get('當月營收', 0)),
                    'yoy': float(item.get('去年同期增減(%)', 0))
                })
        
        return sorted(revenue_data, key=lambda x: x['month'], reverse=True)[:6]
    except:
        return []

def fetch_director_shareholding(stock_code):
    """獲取董監持股"""
    try:
        url = "https://openapi.twse.com.tw/v1/opendata/t187ap12_L"
        response = requests.get(url, timeout=15)
        data = response.json()
        
        for item in data:
            if item.get('公司代號') == stock_code:
                return {
                    'directors_shares': float(item.get('董監持股', 0)),
                    'pledge_ratio': float(item.get('質押比例', 0))
                }
        return None
    except:
        return None

# ==================== 分析函數 ====================

def analyze_short_term_momentum(institutional, margin):
    """短線多空分析"""
    if not institutional or not margin:
        return None
    
    signals = []
    score = 0
    
    # 法人買超
    if institutional['total'] > 1000:
        signals.append("✅ 三大法人大幅買超")
        score += 2
    elif institutional['total'] > 0:
        signals.append("🟢 三大法人買超")
        score += 1
    elif institutional['total'] < -1000:
        signals.append("❌ 三大法人大幅賣超")
        score -= 2
    else:
        signals.append("🔴 三大法人賣超")
        score -= 1
    
    # 融資變化
    margin_change = margin['margin_buy'] - margin['margin_sell']
    if margin_change < -500:
        signals.append("✅ 融資大減（籌碼乾淨）")
        score += 2
    elif margin_change < 0:
        signals.append("🟢 融資減少")
        score += 1
    elif margin_change > 500:
        signals.append("❌ 融資大增（散戶追高）")
        score -= 2
    
    # 券資比
    if margin['margin_balance'] > 0:
        sr_ratio = (margin['short_balance'] / margin['margin_balance']) * 100
        if sr_ratio > 30:
            signals.append("⚠️ 券資比偏高（空方力道強）")
            score -= 1
    
    return {
        'score': score,
        'signals': signals,
        'rating': '強多' if score >= 3 else '偏多' if score >= 1 else '中性' if score >= -1 else '偏空' if score >= -3 else '強空'
    }

def analyze_long_term_accumulation(shareholding):
    """中長線大戶吸籌分析"""
    if not shareholding:
        return None
    
    big_holder_ratio = (shareholding['over_1000'] / shareholding['total_holders']) * 100
    retail_ratio = (shareholding['under_10'] / shareholding['total_holders']) * 100
    
    signals = []
    
    if big_holder_ratio > 20:
        signals.append("✅ 千張大戶比例高（籌碼集中）")
    
    if retail_ratio < 30:
        signals.append("✅ 散戶比例低（主力控盤）")
    
    return {
        'big_holder_ratio': round(big_holder_ratio, 2),
        'retail_ratio': round(retail_ratio, 2),
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
            'message': f"⚠️ 高風險：董監質押率 {pledge_ratio:.1f}%（>50%）",
            'color': 'red'
        }
    elif pledge_ratio > 30:
        return {
            'level': 'medium',
            'message': f"⚠️ 中度風險：董監質押率 {pledge_ratio:.1f}%",
            'color': 'orange'
        }
    else:
        return {
            'level': 'low',
            'message': f"✅ 安全：董監質押率 {pledge_ratio:.1f}%",
            'color': 'green'
        }

# ==================== 視覺化函數 ====================

def create_institutional_chart(history_data):
    """建立法人買賣超圖表"""
    if not history_data:
        return None
    
    df = pd.DataFrame(history_data)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='外資',
        x=df['date'],
        y=df['foreign'],
        marker_color='#00d4ff'
    ))
    
    fig.add_trace(go.Bar(
        name='投信',
        x=df['date'],
        y=df['trust'],
        marker_color='#f5c518'
    ))
    
    fig.add_trace(go.Bar(
        name='自營',
        x=df['date'],
        y=df['dealer'],
        marker_color='#00e882'
    ))
    
    fig.update_layout(
        title='三大法人近期買賣超（張）',
        barmode='group',
        template='plotly_dark',
        height=400,
        paper_bgcolor='#0d1220',
        plot_bgcolor='#0d1220'
    )
    
    return fig

def create_revenue_chart(revenue_data):
    """建立營收圖表"""
    if not revenue_data:
        return None
    
    df = pd.DataFrame(revenue_data)
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Bar(
            name='月營收',
            x=df['month'],
            y=df['revenue'],
            marker_color='#00d4ff'
        ),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Scatter(
            name='YoY%',
            x=df['month'],
            y=df['yoy'],
            line=dict(color='#ff4d4d', width=3),
            mode='lines+markers'
        ),
        secondary_y=True
    )
    
    fig.update_layout(
        title='月營收與年增率',
        template='plotly_dark',
        height=400,
        paper_bgcolor='#0d1220',
        plot_bgcolor='#0d1220'
    )
    
    fig.update_yaxes(title_text="營收（千元）", secondary_y=False)
    fig.update_yaxes(title_text="YoY %", secondary_y=True)
    
    return fig

# ==================== 主程式 ====================

st.title("📈 台股籌碼分析系統")

# 側邊欄
with st.sidebar:
    st.header("⚙️ 功能選擇")
    
    mode = st.radio(
        "選擇模式",
        ["個股分析", "大盤追蹤"],
        index=0
    )
    
    st.markdown("---")

# ==================== 個股分析模式 ====================

if mode == "個股分析":
    st.subheader("🔍 個股多維度分析")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        stock_code = st.text_input(
            "輸入股票代號",
            value="2330",
            max_chars=10,
            placeholder="例：2330"
        ).strip()
    
    with col2:
        query_date = st.date_input(
            "查詢日期",
            value=datetime.now()
        )
    
    with col3:
        st.write("")
        st.write("")
        analyze_btn = st.button("🔍 開始分析", type="primary", use_container_width=True)
    
    if analyze_btn and stock_code:
        date_str = query_date.strftime("%Y%m%d")
        
        with st.spinner('正在獲取資料...'):
            # 獲取所有資料
            price_data = fetch_stock_price(stock_code, date_str)
            institutional_data = fetch_institutional_trading(stock_code, date_str)
            margin_data = fetch_margin_trading(stock_code)
            shareholding_data = fetch_shareholding_distribution(stock_code)
            revenue_data = fetch_monthly_revenue(stock_code)
            director_data = fetch_director_shareholding(stock_code)
        
        if not price_data:
            st.error(f"❌ 查無股票代號 {stock_code} 的資料")
        else:
            # 基本資訊
            st.markdown(f"### {price_data['name']} ({stock_code})")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                change_color = "🟢" if price_data['change'] > 0 else "🔴" if price_data['change'] < 0 else "⚪"
                st.metric(
                    "收盤價",
                    f"${price_data['close']:.2f}",
                    f"{price_data['change']:+.2f}"
                )
            
            with col2:
                st.metric(
                    "成交量",
                    f"{price_data['volume']:,} 張"
                )
            
            with col3:
                if institutional_data:
                    total_color = "🟢" if institutional_data['total'] > 0 else "🔴"
                    st.metric(
                        "法人買賣超",
                        f"{total_color} {institutional_data['total']:,} 張"
                    )
            
            with col4:
                if margin_data:
                    st.metric(
                        "融資餘額",
                        f"{margin_data['margin_balance']:,} 張"
                    )
            
            st.markdown("---")
            
            # 分析結果
            tab1, tab2, tab3, tab4 = st.tabs([
                "📊 短線分析",
                "📈 中長線分析",
                "💰 財務數據",
                "⚠️ 風險評估"
            ])
            
            with tab1:
                st.subheader("短線多空角力分析")
                
                analysis = analyze_short_term_momentum(institutional_data, margin_data)
                
                if analysis:
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        rating_color = {
                            '強多': '#00e882',
                            '偏多': '#90ee90',
                            '中性': '#f5c518',
                            '偏空': '#ff8c42',
                            '強空': '#ff4d4d'
                        }.get(analysis['rating'], '#f5c518')
                        
                        st.markdown(f"""
                        <div style="background: {rating_color}22; border-left: 4px solid {rating_color}; padding: 1.5rem; border-radius: 8px;">
                            <h2 style="color: {rating_color}; margin: 0;">{analysis['rating']}</h2>
                            <p style="color: #c8d4e8; margin-top: 0.5rem;">評分：{analysis['score']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.write("**市場訊號：**")
                        for signal in analysis['signals']:
                            st.write(signal)
                
                # 法人資料詳細
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
                        st.metric(
                            "融資變化",
                            f"{margin_change:+,} 張",
                            f"餘額 {margin_data['margin_balance']:,}"
                        )
                    
                    with col2:
                        short_change = margin_data['short_cover'] - margin_data['short_sell']
                        st.metric(
                            "融券變化",
                            f"{short_change:+,} 張",
                            f"餘額 {margin_data['short_balance']:,}"
                        )
                    
                    with col3:
                        if margin_data['margin_balance'] > 0:
                            sr_ratio = (margin_data['short_balance'] / margin_data['margin_balance']) * 100
                            st.metric(
                                "券資比",
                                f"{sr_ratio:.2f}%"
                            )
            
            with tab2:
                st.subheader("中長線大戶吸籌分析")
                
                analysis = analyze_long_term_accumulation(shareholding_data)
                
                if analysis:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"""
                        <div class="metric-card">
                            <h3 style="color: #00d4ff;">千張大戶比例</h3>
                            <h1 style="color: #00e882;">{analysis['big_holder_ratio']}%</h1>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"""
                        <div class="metric-card">
                            <h3 style="color: #00d4ff;">散戶比例</h3>
                            <h1 style="color: #f5c518;">{analysis['retail_ratio']}%</h1>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.write("")
                    st.write("**籌碼結構分析：**")
                    for signal in analysis['signals']:
                        st.write(signal)
                else:
                    st.info("📊 集保股權資料每週五更新，請稍後查詢")
            
            with tab3:
                st.subheader("財務數據")
                
                if revenue_data:
                    # 營收圖表
                    fig = create_revenue_chart(revenue_data)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # 營收表格
                    st.markdown("#### 近期月營收")
                    df_revenue = pd.DataFrame(revenue_data)
                    df_revenue.columns = ['年月', '營收（千元）', 'YoY%']
                    st.dataframe(df_revenue, use_container_width=True, hide_index=True)
                    
                    # 營收分析
                    latest_yoy = revenue_data[0]['yoy']
                    if latest_yoy > 20:
                        st.success(f"✅ 最新月營收 YoY {latest_yoy:.2f}%，成長強勁！")
                    elif latest_yoy > 0:
                        st.info(f"🟢 最新月營收 YoY {latest_yoy:.2f}%，穩定成長")
                    else:
                        st.warning(f"⚠️ 最新月營收 YoY {latest_yoy:.2f}%，需注意衰退")
                else:
                    st.info("📊 查無營收資料")
            
            with tab4:
                st.subheader("風險評估")
                
                risk_check = check_director_risk(director_data)
                
                if risk_check:
                    if risk_check['level'] == 'high':
                        st.markdown(f"""
                        <div class="alert-box">
                            <h3>🚨 高風險警示</h3>
                            <p>{risk_check['message']}</p>
                            <p><small>董監事質押比例過高，大盤下跌時可能面臨斷頭風險</small></p>
                        </div>
                        """, unsafe_allow_html=True)
                    elif risk_check['level'] == 'medium':
                        st.warning(risk_check['message'])
                    else:
                        st.markdown(f"""
                        <div class="success-box">
                            <h3>✅ 風險可控</h3>
                            <p>{risk_check['message']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("📊 查無董監持股資料")
                
                # 綜合風險評分
                st.markdown("#### 綜合風險評估")
                
                risk_factors = []
                risk_score = 0
                
                if institutional_data and institutional_data['total'] < -2000:
                    risk_factors.append("⚠️ 法人大幅賣超")
                    risk_score += 2
                
                if margin_data:
                    margin_change = margin_data['margin_buy'] - margin_data['margin_sell']
                    if margin_change > 1000:
                        risk_factors.append("⚠️ 融資大增")
                        risk_score += 1
                
                if risk_check and risk_check['level'] == 'high':
                    risk_factors.append("⚠️ 董監高質押")
                    risk_score += 3
                
                if risk_score == 0:
                    st.success("✅ 目前無明顯風險因子")
                else:
                    for factor in risk_factors:
                        st.write(factor)
                    
                    if risk_score >= 4:
                        st.error("🚨 高風險，建議謹慎")
                    elif risk_score >= 2:
                        st.warning("⚠️ 中度風險，需密切觀察")

# ==================== 大盤追蹤模式 ====================

else:
    st.subheader("📊 大盤法人動向追蹤")
    
    # 這裡保留原本的大盤追蹤功能
    st.info("使用原本的大盤 TOP 10 買賣超追蹤功能")
    
    # ... 原本的程式碼 ...

# 頁尾
st.markdown("---")
st.caption("📊 資料來源：證交所、櫃買中心、集保所 | ⚠️ 僅供參考，非投資建議")
