"""
LINE Service Module - src/line_service.py
==========================================
รับผิดชอบการส่งข้อความผ่าน LINE Messaging API
ใช้ Push Message API สำหรับส่งข้อความหาผู้ใช้โดยตรง

API Reference: https://developers.line.biz/en/reference/messaging-api/#send-push-message
"""

import requests
from typing import Tuple
from src.config import LINE_API_ENDPOINT


def send_push_message(user_id: str, message: str, token: str) -> Tuple[bool, int]:
    """
    ส่งข้อความผ่าน LINE Messaging API (Push Message)
    
    Args:
        user_id (str): LINE User ID ของผู้รับ
        message (str): ข้อความที่ต้องการส่ง
        token (str): Channel Access Token
    
    Returns:
        tuple: (success: bool, status_code: int)
            - success: True ถ้าส่งสำเร็จ (status 200)
            - status_code: HTTP Status Code
    """
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    # LINE Messaging API Push Message format
    payload = {
        'to': user_id,
        'messages': [
            {
                'type': 'text',
                'text': message
            }
        ]
    }
    
    try:
        response = requests.post(
            LINE_API_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=10
        )
        
        success = response.status_code == 200
        
        if not success:
            print(f"❌ LINE API Error: Status {response.status_code}")
            print(f"   Response: {response.text}")
        
        return success, response.status_code
    
    except requests.exceptions.Timeout:
        print("❌ LINE API Error: Request timeout")
        return False, 408
    
    except requests.exceptions.RequestException as e:
        print(f"❌ LINE API Error: {e}")
        return False, 500


def send_price_alert(
    symbol: str,
    name: str,
    current_price: float,
    target_price: float,
    user_id: str,
    token: str
) -> Tuple[bool, int]:
    """
    ส่งแจ้งเตือนเมื่อราคาหุ้นถึงเป้าหมาย
    
    Args:
        symbol: ชื่อย่อหุ้น (e.g., "AAPL")
        name: ชื่อเต็มหุ้น (e.g., "Apple Inc.")
        current_price: ราคาปัจจุบัน
        target_price: ราคาเป้าหมาย
        user_id: LINE User ID
        token: Channel Access Token
    
    Returns:
        tuple: (success: bool, status_code: int)
    """
    # คำนวณส่วนลด
    discount_percent = round(((target_price - current_price) / target_price) * 100, 1)
    
    message = f"""🚨 แจ้งเตือนราคาหุ้น!

📈 {symbol} - {name}
💰 ราคาปัจจุบัน: ${current_price:,.2f}
🎯 ราคาเป้าหมาย: ${target_price:,.2f}
📉 ต่ำกว่าเป้า: {discount_percent}%

⏰ ตลาดเปิดอยู่
💡 พิจารณาซื้อตามแผนที่วางไว้"""
    
    return send_push_message(user_id, message, token)


def send_summary_report(
    stocks_data: list,
    user_id: str,
    token: str
) -> Tuple[bool, int]:
    """
    ส่งสรุปราคาหุ้นทั้งหมด
    
    Args:
        stocks_data: รายการข้อมูลหุ้น
        user_id: LINE User ID
        token: Channel Access Token
    
    Returns:
        tuple: (success: bool, status_code: int)
    """
    lines = ["📊 สรุปราคาหุ้น", "─" * 18]
    
    for stock in stocks_data:
        symbol = stock.get("symbol", "N/A")
        price = stock.get("price")
        target = stock.get("target", 0)
        
        if price is None:
            status_icon = "⚪"
            price_str = "N/A"
        elif price <= target:
            status_icon = "🟢"
            price_str = f"${price:,.2f}"
        else:
            status_icon = "🔴"
            price_str = f"${price:,.2f}"
        
        lines.append(f"{status_icon} {symbol}: {price_str}")
    
    lines.append("─" * 18)
    lines.append("🟢 ถึงเป้า | 🔴 ยังไม่ถึง")
    
    message = "\n".join(lines)
    return send_push_message(user_id, message, token)
