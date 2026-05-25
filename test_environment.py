"""
環境測試腳本
執行此腳本可以快速檢查環境是否設定正確
"""

import sys

def check_python_version():
    """檢查 Python 版本"""
    print("🔍 檢查 Python 版本...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python 版本過舊：{version.major}.{version.minor}.{version.micro}")
        print(f"   需要 Python 3.8 或以上")
        return False

def check_packages():
    """檢查必要套件"""
    print("\n🔍 檢查必要套件...")
    packages = ['streamlit', 'pandas', 'requests', 'openpyxl']
    all_ok = True
    
    for package in packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} 未安裝")
            all_ok = False
    
    if not all_ok:
        print("\n   執行以下指令安裝：")
        print("   pip install -r requirements.txt")
    
    return all_ok

def check_files():
    """檢查必要檔案"""
    print("\n🔍 檢查必要檔案...")
    import os
    files = [
        'app.py',
        'requirements.txt',
        '.streamlit/config.toml'
    ]
    all_ok = True
    
    for file in files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} 不存在")
            all_ok = False
    
    return all_ok

def test_api():
    """測試證交所 API 連線"""
    print("\n🔍 測試證交所 API 連線...")
    try:
        import requests
        from datetime import datetime, timedelta
        
        # 嘗試最近的交易日
        for i in range(7):
            date = datetime.now() - timedelta(days=i)
            date_str = date.strftime("%Y%m%d")
            
            url = f"https://www.twse.com.tw/fund/T86?response=json&date={date_str}&selectType=ALL"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('stat') == 'OK' and data.get('data'):
                    print(f"   ✅ API 連線正常")
                    print(f"   最新交易日：{date_str[:4]}/{date_str[4:6]}/{date_str[6:8]}")
                    print(f"   資料筆數：{len(data['data'])}")
                    return True
        
        print(f"   ⚠️  最近 7 天無交易日資料")
        print(f"   可能原因：連續假期或週末")
        return True
        
    except Exception as e:
        print(f"   ❌ API 連線失敗：{str(e)}")
        return False

def main():
    """主程式"""
    print("=" * 60)
    print("台股追蹤系統 - 環境測試")
    print("=" * 60)
    
    results = []
    
    results.append(check_python_version())
    results.append(check_packages())
    results.append(check_files())
    results.append(test_api())
    
    print("\n" + "=" * 60)
    print("📊 測試結果")
    print("=" * 60)
    
    if all(results):
        print("✅ 所有檢查通過！")
        print("\n🚀 您可以執行以下指令啟動應用：")
        print("   streamlit run app.py")
    else:
        print("❌ 部分檢查失敗，請修正後再試")
        print("\n💡 常見解決方案：")
        print("   1. 確認 Python 版本 >= 3.8")
        print("   2. 執行：pip install -r requirements.txt")
        print("   3. 確認所有檔案都已下載")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
