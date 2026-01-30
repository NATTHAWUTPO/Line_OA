"""
Stock Service Module - src/stock_service.py
=============================================
รับผิดชอบการดึงข้อมูลราคาหุ้นจาก Yahoo Finance
ทำหน้าที่เดียวคือ "คุยกับ Yahoo Finance" (Single Responsibility Principle)
"""

import yfinance as yf
from typing import Optional, Dict, Any


def get_current_price(symbol: str) -> Optional[float]:
    """
    ดึงราคาปัจจุบันของหุ้น 1 ตัว
    
    Args:
        symbol (str): ชื่อหุ้น เช่น "AAPL", "TSLA", "AMD"
    
    Returns:
        float: ราคาปิดล่าสุด (ปัดเป็น 2 ตำแหน่ง)
        None: ถ้าดึงข้อมูลไม่สำเร็จ
    
    Example:
        >>> price = get_current_price("AAPL")
        >>> print(price)  # 178.45
    """
    try:
        ticker = yf.Ticker(symbol)
        # ดึงข้อมูลราคา 1 วันล่าสุด
        data = ticker.history(period="1d")
        
        if data.empty:
            print(f"⚠️ Warning: No data available for {symbol}")
            return None
        
        # ดึงราคาปิดล่าสุด
        last_price = data['Close'].iloc[-1]
        return round(float(last_price), 2)
    
    except Exception as e:
        print(f"❌ Error fetching {symbol}: {e}")
        return None


def get_stock_info(symbol: str) -> Optional[Dict[str, Any]]:
    """
    ดึงข้อมูลรายละเอียดของหุ้น (สำหรับ Feature เพิ่มเติมในอนาคต)
    
    Args:
        symbol (str): ชื่อหุ้น
    
    Returns:
        dict: ข้อมูลหุ้น รวมถึง price, change, percent_change
        None: ถ้าดึงข้อมูลไม่สำเร็จ
    """
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="2d")  # ดึง 2 วันเพื่อคำนวณ % เปลี่ยนแปลง
        
        if data.empty or len(data) < 1:
            return None
        
        current_price = round(float(data['Close'].iloc[-1]), 2)
        
        # คำนวณการเปลี่ยนแปลง (ถ้ามีข้อมูล 2 วัน)
        if len(data) >= 2:
            previous_close = float(data['Close'].iloc[-2])
            price_change = round(current_price - previous_close, 2)
            percent_change = round((price_change / previous_close) * 100, 2)
        else:
            price_change = 0.0
            percent_change = 0.0
        
        return {
            "symbol": symbol,
            "price": current_price,
            "change": price_change,
            "percent_change": percent_change,
            "trend": "🟢" if price_change >= 0 else "🔴"
        }
    
    except Exception as e:
        print(f"❌ Error fetching info for {symbol}: {e}")
        return None


def get_multiple_prices(symbols: list) -> Dict[str, Optional[float]]:
    """
    ดึงราคาหุ้นหลายตัวพร้อมกัน
    
    Args:
        symbols (list): รายชื่อหุ้น เช่น ["AAPL", "TSLA", "AMD"]
    
    Returns:
        dict: Dictionary ของ symbol -> price
    
    Example:
        >>> prices = get_multiple_prices(["AAPL", "TSLA"])
        >>> print(prices)  # {"AAPL": 178.45, "TSLA": 245.30}
    """
    results = {}
    for symbol in symbols:
        results[symbol] = get_current_price(symbol)
    return results


def get_price_history(symbol: str, days: int = 30) -> list:
    """
    ดึงข้อมูลราคาย้อนหลังสำหรับ AI วิเคราะห์
    
    Args:
        symbol (str): ชื่อหุ้น
        days (int): จำนวนวันย้อนหลัง (default: 30)
    
    Returns:
        list: รายการราคาย้อนหลัง
            [{"date": "2024-01-01", "open": 180, "high": 182, "low": 179, "close": 181, "volume": 1000000}, ...]
    """
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=f"{days}d")
        
        if data.empty:
            return []
        
        history = []
        for date, row in data.iterrows():
            history.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": round(float(row['Open']), 2),
                "high": round(float(row['High']), 2),
                "low": round(float(row['Low']), 2),
                "close": round(float(row['Close']), 2),
                "volume": int(row['Volume'])
            })
        
        return history
    
    except Exception as e:
        print(f"❌ Error fetching history for {symbol}: {e}")
        return []

