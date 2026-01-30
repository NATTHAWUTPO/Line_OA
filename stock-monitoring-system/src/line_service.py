"""
LINE Service Module - src/line_service.py
==========================================
รับผิดชอบการส่งข้อความผ่าน LINE Notify API
ทำหน้าที่เดียวคือ "ยิง API ไปหา LINE" (Single Responsibility Principle)
"""

import requests
from typing import Optional, Tuple
from src.config import LINE_NOTIFY_URL


def send_notification(message: str, token: str) -> Tuple[bool, int]:
    """
    ส่งข้อความเข้า LINE Notify
    
    Args:
        message (str): ข้อความที่ต้องการส่ง
        token (str): LINE Notify Access Token
    
    Returns:
        tuple: (success: bool, status_code: int)
            - success: True ถ้าส่งสำเร็จ (status 200)
            - status_code: HTTP Status Code
    
    Example:
        >>> success, status = send_notification("Hello!", "YOUR_TOKEN")
        >>> print(success)  # True
    """
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    payload = {
        'message': message
    }
    
    try:
        response = requests.post(
            LINE_NOTIFY_URL,
            headers=headers,
            data=payload,
            timeout=10  # Timeout 10 วินาที
        )
        
        success = response.status_code == 200
        
        if not success:
            print(f"❌ LINE Notify Error: Status {response.status_code}")
            print(f"   Response: {response.text}")
        
        return success, response.status_code
    
    except requests.exceptions.Timeout:
        print("❌ LINE Notify Error: Request timeout")
        return False, 408
    
    except requests.exceptions.RequestException as e:
        print(f"❌ LINE Notify Error: {e}")
        return False, 500


def send_price_alert(
    symbol: str,
    name: str,
    current_price: float,
    target_price: float,
    token: str
) -> Tuple[bool, int]:
    """
    ส่งแจ้งเตือนเมื่อราคาหุ้นถึงเป้าหมาย
    
    Args:
        symbol: ชื่อย่อหุ้น (e.g., "AAPL")
        name: ชื่อเต็มหุ้น (e.g., "Apple Inc.")
        current_price: ราคาปัจจุบัน
        target_price: ราคาเป้าหมาย
        token: LINE Notify Token
    
    Returns:
        tuple: (success: bool, status_code: int)
    """
    # คำนวณส่วนลด
    discount_percent = round(((target_price - current_price) / target_price) * 100, 1)
    
    message = f"""
🚨 แจ้งเตือนราคาหุ้น!

📈 {symbol} - {name}
💰 ราคาปัจจุบัน: ${current_price:,.2f}
🎯 ราคาเป้าหมาย: ${target_price:,.2f}
📉 ต่ำกว่าเป้า: {discount_percent}%

⏰ เวลาแจ้งเตือน: ตลาดเปิดอยู่
💡 พิจารณาซื้อตามแผนที่วางไว้
"""
    
    return send_notification(message, token)


def send_summary_report(
    stocks_data: list,
    token: str
) -> Tuple[bool, int]:
    """
    ส่งสรุปราคาหุ้นทั้งหมด
    
    Args:
        stocks_data: รายการข้อมูลหุ้น
            [{"symbol": "AAPL", "price": 178.45, "target": 170.00, "status": "watching"}, ...]
        token: LINE Notify Token
    
    Returns:
        tuple: (success: bool, status_code: int)
    """
    # สร้างตารางสรุป
    lines = ["📊 สรุปราคาหุ้น", "=" * 20]
    
    for stock in stocks_data:
        symbol = stock.get("symbol", "N/A")
        price = stock.get("price")
        target = stock.get("target", 0)
        
        if price is None:
            status_icon = "⚪"
            price_str = "N/A"
        elif price <= target:
            status_icon = "🟢"  # ถึงเป้า - ซื้อได้
            price_str = f"${price:,.2f}"
        else:
            status_icon = "🔴"  # ยังไม่ถึงเป้า
            price_str = f"${price:,.2f}"
        
        lines.append(f"{status_icon} {symbol}: {price_str} (เป้า: ${target:,.2f})")
    
    lines.append("=" * 20)
    lines.append("🟢 = ถึงเป้า | 🔴 = ยังไม่ถึง")
    
    message = "\n".join(lines)
    return send_notification(message, token)
