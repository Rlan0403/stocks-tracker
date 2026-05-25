"""
台股三大法人資料抓取腳本
可定時執行此腳本來自動更新資料
"""

import requests
import json
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path("data_storage")
DATA_DIR.mkdir(exist_ok=True)

def fetch_twse_data(date_str):
    """
    從證交所 API 獲取三大法人資料
    
    Args:
        date_str: 格式 YYYYMMDD
    
    Returns:
        tuple: (資料列表, 錯誤訊息)
    """
    url = f"https://www.twse.com.tw/fund/T86?response=json&date={date_str}&selectType=ALL"
    
    try:
        print(f"正在獲取 {date_str} 的資料...")
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get('stat') != 'OK':
            return None, f"證交所回應：{data.get('stat', '未知錯誤')}"
        
        if not data.get('data'):
            return None, "非交易日或資料尚未更新"
        
        # 解析資料
        stocks = []
        for row in data['data']:
            if not row[0] or len(row[0].strip()) < 4:
                continue
            
            code = row[0].strip()
            name = row[1].strip()
            
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
        
        print(f"✅ 成功獲取 {len(stocks)} 檔個股資料")
        return stocks, None
        
    except Exception as e:
        return None, f"錯誤：{str(e)}"

def save_to_json(stocks, date_str):
    """儲存資料到 JSON 檔案"""
    filename = DATA_DIR / f"twse_{date_str}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            'date': date_str,
            'update_time': datetime.now().isoformat(),
            'total_stocks': len(stocks),
            'data': stocks
        }, f, ensure_ascii=False, indent=2)
    
    print(f"💾 資料已儲存至 {filename}")

def main():
    """主程式"""
    # 預設抓取今天的資料
    today = datetime.now()
    date_str = today.strftime("%Y%m%d")
    
    print("=" * 60)
    print("台股三大法人資料抓取工具")
    print("=" * 60)
    print(f"查詢日期：{date_str}")
    print()
    
    stocks, error = fetch_twse_data(date_str)
    
    if error:
        print(f"❌ {error}")
        
        # 如果是今天沒資料，嘗試抓取前一個交易日
        if "非交易日" in error or "尚未更新" in error:
            print("\n嘗試抓取前一個交易日資料...")
            yesterday = today - timedelta(days=1)
            date_str = yesterday.strftime("%Y%m%d")
            stocks, error = fetch_twse_data(date_str)
            
            if error:
                print(f"❌ {error}")
                return
    
    # 儲存資料
    save_to_json(stocks, date_str)
    
    # 顯示統計
    print("\n" + "=" * 60)
    print("📊 資料統計")
    print("=" * 60)
    
    buy_stocks = [s for s in stocks if s['total'] > 0]
    sell_stocks = [s for s in stocks if s['total'] < 0]
    
    print(f"總檔數：{len(stocks)}")
    print(f"買超檔數：{len(buy_stocks)}")
    print(f"賣超檔數：{len(sell_stocks)}")
    
    if buy_stocks:
        top_buy = sorted(buy_stocks, key=lambda x: x['total'], reverse=True)[:5]
        print("\n▲ 買超前 5 名：")
        for i, s in enumerate(top_buy, 1):
            print(f"  {i}. {s['code']} {s['name']} (+{s['total']:,} 張)")
    
    if sell_stocks:
        top_sell = sorted(sell_stocks, key=lambda x: x['total'])[:5]
        print("\n▼ 賣超前 5 名：")
        for i, s in enumerate(top_sell, 1):
            print(f"  {i}. {s['code']} {s['name']} ({s['total']:,} 張)")
    
    print("\n✨ 完成！")

if __name__ == "__main__":
    main()
