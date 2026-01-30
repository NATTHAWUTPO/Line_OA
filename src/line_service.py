"""
LINE Service Module - src/line_service.py
==========================================
รับผิดชอบการส่งข้อความผ่าน LINE Messaging API
รองรับทั้ง Text Message และ Flex Message (UI สวยๆ)

API Reference: https://developers.line.biz/en/reference/messaging-api/
Flex Message Simulator: https://developers.line.biz/flex-simulator/
"""

import requests
from typing import Tuple, Dict, Any
from src.config import LINE_API_ENDPOINT


def send_push_message(user_id: str, message: str, token: str) -> Tuple[bool, int]:
    """
    ส่งข้อความ Text ธรรมดาผ่าน LINE Messaging API
    """
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
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


def send_flex_message(user_id: str, alt_text: str, flex_content: Dict[str, Any], token: str) -> Tuple[bool, int]:
    """
    ส่ง Flex Message (UI สวยๆ) ผ่าน LINE Messaging API
    
    Args:
        user_id: LINE User ID
        alt_text: ข้อความที่แสดงใน notification
        flex_content: Flex Message JSON object
        token: Channel Access Token
    """
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    payload = {
        'to': user_id,
        'messages': [
            {
                'type': 'flex',
                'altText': alt_text,
                'contents': flex_content
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
            print(f"❌ LINE Flex Error: Status {response.status_code}")
            print(f"   Response: {response.text}")
        
        return success, response.status_code
    
    except Exception as e:
        print(f"❌ LINE Flex Error: {e}")
        return False, 500


def create_price_alert_flex(
    symbol: str,
    name: str,
    current_price: float,
    target_price: float
) -> Dict[str, Any]:
    """
    สร้าง Flex Message สำหรับแจ้งเตือนราคาหุ้น
    """
    discount_percent = round(((target_price - current_price) / target_price) * 100, 1)
    
    return {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": "🚨 PRICE ALERT",
                            "color": "#ffffff",
                            "size": "sm",
                            "weight": "bold"
                        }
                    ]
                },
                {
                    "type": "text",
                    "text": symbol,
                    "color": "#ffffff",
                    "size": "xxl",
                    "weight": "bold"
                },
                {
                    "type": "text",
                    "text": name,
                    "color": "#ffffff99",
                    "size": "sm"
                }
            ],
            "backgroundColor": "#27ACB2",
            "paddingAll": "20px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": "ราคาปัจจุบัน",
                            "color": "#8c8c8c",
                            "size": "sm",
                            "flex": 1
                        },
                        {
                            "type": "text",
                            "text": f"${current_price:,.2f}",
                            "color": "#27ACB2",
                            "size": "xl",
                            "weight": "bold",
                            "flex": 2,
                            "align": "end"
                        }
                    ]
                },
                {
                    "type": "separator",
                    "margin": "lg"
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "lg",
                    "contents": [
                        {
                            "type": "text",
                            "text": "ราคาเป้าหมาย",
                            "color": "#8c8c8c",
                            "size": "sm",
                            "flex": 1
                        },
                        {
                            "type": "text",
                            "text": f"${target_price:,.2f}",
                            "size": "md",
                            "flex": 2,
                            "align": "end"
                        }
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "md",
                    "contents": [
                        {
                            "type": "text",
                            "text": "ต่ำกว่าเป้า",
                            "color": "#8c8c8c",
                            "size": "sm",
                            "flex": 1
                        },
                        {
                            "type": "text",
                            "text": f"📉 {discount_percent}%",
                            "color": "#FF5551",
                            "size": "md",
                            "weight": "bold",
                            "flex": 2,
                            "align": "end"
                        }
                    ]
                }
            ],
            "paddingAll": "20px"
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "💡 พิจารณาซื้อตามแผนที่วางไว้",
                    "color": "#27ACB2",
                    "size": "sm",
                    "align": "center"
                }
            ],
            "paddingAll": "15px"
        }
    }


def create_ai_analysis_flex(
    symbol: str,
    name: str,
    current_price: float,
    analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    สร้าง Flex Message สำหรับแสดงผลการวิเคราะห์ AI
    """
    rec = analysis.get("recommendation", "HOLD")
    
    # สีตามคำแนะนำ
    if rec == "BUY":
        header_color = "#00B900"  # เขียว
        rec_text = "🟢 BUY"
    elif rec == "SELL":
        header_color = "#FF5551"  # แดง
        rec_text = "🔴 SELL"
    else:
        header_color = "#FFC107"  # เหลือง
        rec_text = "🟡 HOLD"
    
    return {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": "🤖 AI ANALYSIS",
                            "color": "#ffffff",
                            "size": "sm",
                            "weight": "bold"
                        },
                        {
                            "type": "text",
                            "text": f"{analysis.get('confidence', 0)}%",
                            "color": "#ffffffcc",
                            "size": "sm",
                            "align": "end"
                        }
                    ]
                },
                {
                    "type": "text",
                    "text": symbol,
                    "color": "#ffffff",
                    "size": "xxl",
                    "weight": "bold"
                },
                {
                    "type": "text",
                    "text": name,
                    "color": "#ffffff99",
                    "size": "sm"
                }
            ],
            "backgroundColor": header_color,
            "paddingAll": "20px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": "คำแนะนำ",
                            "color": "#8c8c8c",
                            "size": "sm",
                            "flex": 1
                        },
                        {
                            "type": "text",
                            "text": rec_text,
                            "size": "lg",
                            "weight": "bold",
                            "flex": 2,
                            "align": "end"
                        }
                    ]
                },
                {
                    "type": "separator",
                    "margin": "lg"
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "lg",
                    "contents": [
                        {
                            "type": "text",
                            "text": "💰 ราคาปัจจุบัน",
                            "color": "#8c8c8c",
                            "size": "sm",
                            "flex": 1
                        },
                        {
                            "type": "text",
                            "text": f"${current_price:,.2f}",
                            "size": "md",
                            "weight": "bold",
                            "flex": 1,
                            "align": "end"
                        }
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "md",
                    "contents": [
                        {
                            "type": "text",
                            "text": "📍 Entry Point",
                            "color": "#00B900",
                            "size": "sm",
                            "flex": 1
                        },
                        {
                            "type": "text",
                            "text": f"${analysis.get('entry_price', 0):,.2f}",
                            "size": "md",
                            "flex": 1,
                            "align": "end"
                        }
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "md",
                    "contents": [
                        {
                            "type": "text",
                            "text": "🎯 Take Profit",
                            "color": "#27ACB2",
                            "size": "sm",
                            "flex": 1
                        },
                        {
                            "type": "text",
                            "text": f"${analysis.get('take_profit', 0):,.2f}",
                            "size": "md",
                            "flex": 1,
                            "align": "end"
                        }
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "md",
                    "contents": [
                        {
                            "type": "text",
                            "text": "🛑 Stop Loss",
                            "color": "#FF5551",
                            "size": "sm",
                            "flex": 1
                        },
                        {
                            "type": "text",
                            "text": f"${analysis.get('stop_loss', 0):,.2f}",
                            "size": "md",
                            "flex": 1,
                            "align": "end"
                        }
                    ]
                },
                {
                    "type": "separator",
                    "margin": "lg"
                },
                {
                    "type": "text",
                    "text": analysis.get("analysis", ""),
                    "color": "#666666",
                    "size": "sm",
                    "wrap": True,
                    "margin": "lg"
                }
            ],
            "paddingAll": "20px"
        }
    }


def create_stop_loss_flex(
    symbol: str,
    name: str,
    current_price: float,
    stop_loss: float
) -> Dict[str, Any]:
    """
    สร้าง Flex Message สำหรับแจ้งเตือน Stop Loss
    """
    loss_percent = round(((stop_loss - current_price) / stop_loss) * 100, 1)
    
    return {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "🛑 STOP LOSS ALERT",
                    "color": "#ffffff",
                    "size": "lg",
                    "weight": "bold"
                },
                {
                    "type": "text",
                    "text": symbol,
                    "color": "#ffffff",
                    "size": "xxl",
                    "weight": "bold",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": name,
                    "color": "#ffffff99",
                    "size": "sm"
                }
            ],
            "backgroundColor": "#FF5551",
            "paddingAll": "20px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": "ราคาปัจจุบัน",
                            "color": "#8c8c8c",
                            "size": "sm",
                            "flex": 1
                        },
                        {
                            "type": "text",
                            "text": f"${current_price:,.2f}",
                            "color": "#FF5551",
                            "size": "xl",
                            "weight": "bold",
                            "flex": 2,
                            "align": "end"
                        }
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "lg",
                    "contents": [
                        {
                            "type": "text",
                            "text": "Stop Loss",
                            "color": "#8c8c8c",
                            "size": "sm",
                            "flex": 1
                        },
                        {
                            "type": "text",
                            "text": f"${stop_loss:,.2f}",
                            "size": "md",
                            "flex": 2,
                            "align": "end"
                        }
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "md",
                    "contents": [
                        {
                            "type": "text",
                            "text": "ขาดทุน",
                            "color": "#8c8c8c",
                            "size": "sm",
                            "flex": 1
                        },
                        {
                            "type": "text",
                            "text": f"📉 {loss_percent}%",
                            "color": "#FF5551",
                            "size": "md",
                            "weight": "bold",
                            "flex": 2,
                            "align": "end"
                        }
                    ]
                }
            ],
            "paddingAll": "20px"
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "⚠️ พิจารณาขายเพื่อตัดขาดทุน",
                    "color": "#FF5551",
                    "size": "sm",
                    "weight": "bold",
                    "align": "center"
                }
            ],
            "paddingAll": "15px"
        }
    }


# ============================================
# High-level Functions (ใช้ Flex Message)
# ============================================

def send_price_alert(
    symbol: str,
    name: str,
    current_price: float,
    target_price: float,
    user_id: str,
    token: str
) -> Tuple[bool, int]:
    """
    ส่งแจ้งเตือนราคาหุ้น (Flex Message)
    """
    flex_content = create_price_alert_flex(symbol, name, current_price, target_price)
    return send_flex_message(user_id, f"🚨 {symbol} ราคาถึงเป้า!", flex_content, token)


def send_ai_alert(
    symbol: str,
    name: str,
    current_price: float,
    analysis: Dict[str, Any],
    user_id: str,
    token: str
) -> Tuple[bool, int]:
    """
    ส่งผลวิเคราะห์ AI (Flex Message)
    """
    flex_content = create_ai_analysis_flex(symbol, name, current_price, analysis)
    return send_flex_message(user_id, f"🤖 AI วิเคราะห์ {symbol}", flex_content, token)


def send_stop_loss_alert(
    symbol: str,
    name: str,
    current_price: float,
    stop_loss: float,
    user_id: str,
    token: str
) -> Tuple[bool, int]:
    """
    ส่งแจ้งเตือน Stop Loss (Flex Message)
    """
    flex_content = create_stop_loss_flex(symbol, name, current_price, stop_loss)
    return send_flex_message(user_id, f"🛑 {symbol} ถึง Stop Loss!", flex_content, token)


def send_summary_report(
    stocks_data: list,
    user_id: str,
    token: str
) -> Tuple[bool, int]:
    """
    ส่งสรุปราคาหุ้นทั้งหมด (Text Message)
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
