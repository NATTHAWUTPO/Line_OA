"""
Flex Message Templates - src/flex_templates.py
===============================================
สร้าง Flex Message ต่างๆ สำหรับ LINE Bot

Templates:
- Welcome message
- AI Analysis card
- Watchlist carousel
- Help message
"""

from typing import Dict, Any, List


def create_welcome_flex() -> Dict[str, Any]:
    """
    สร้าง Flex Message ต้อนรับ
    """
    return {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "📈 Stock Monitor Bot",
                    "color": "#ffffff",
                    "size": "xl",
                    "weight": "bold"
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
                    "type": "text",
                    "text": "ยินดีต้อนรับครับ! 🎉",
                    "size": "lg",
                    "weight": "bold"
                },
                {
                    "type": "text",
                    "text": "ผมช่วยวิเคราะห์หุ้นด้วย AI ได้",
                    "size": "sm",
                    "color": "#666666",
                    "margin": "md",
                    "wrap": True
                },
                {
                    "type": "separator",
                    "margin": "lg"
                },
                {
                    "type": "text",
                    "text": "วิธีใช้งาน:",
                    "size": "md",
                    "weight": "bold",
                    "margin": "lg"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "md",
                    "contents": [
                        {
                            "type": "text",
                            "text": "1️⃣ พิมพ์ชื่อหุ้น เช่น AAPL, TSLA",
                            "size": "sm",
                            "color": "#555555"
                        },
                        {
                            "type": "text",
                            "text": "2️⃣ AI จะวิเคราะห์ให้ทันที",
                            "size": "sm",
                            "color": "#555555",
                            "margin": "sm"
                        },
                        {
                            "type": "text",
                            "text": "3️⃣ เพิ่ม Watchlist หรือตั้งแจ้งเตือน",
                            "size": "sm",
                            "color": "#555555",
                            "margin": "sm"
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
                    "text": "ลองพิมพ์ 'AAPL' เพื่อเริ่มต้น! 👆",
                    "color": "#27ACB2",
                    "size": "sm",
                    "align": "center",
                    "weight": "bold"
                }
            ],
            "paddingAll": "15px"
        }
    }


def create_help_flex() -> Dict[str, Any]:
    """
    สร้าง Flex Message วิธีใช้งาน
    """
    return {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "❓ วิธีใช้งาน",
                    "color": "#ffffff",
                    "size": "lg",
                    "weight": "bold"
                }
            ],
            "backgroundColor": "#6C5CE7",
            "paddingAll": "20px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "📝 คำสั่งที่ใช้ได้:",
                    "weight": "bold",
                    "size": "md"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "lg",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "AAPL", "size": "sm", "color": "#27ACB2", "flex": 2},
                                {"type": "text", "text": "→ วิเคราะห์หุ้น Apple", "size": "sm", "color": "#666666", "flex": 5}
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "WATCHLIST", "size": "sm", "color": "#27ACB2", "flex": 2},
                                {"type": "text", "text": "→ ดูรายการที่ติดตาม", "size": "sm", "color": "#666666", "flex": 5}
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "HELP", "size": "sm", "color": "#27ACB2", "flex": 2},
                                {"type": "text", "text": "→ ดูวิธีใช้งาน", "size": "sm", "color": "#666666", "flex": 5}
                            ]
                        }
                    ]
                },
                {
                    "type": "separator",
                    "margin": "lg"
                },
                {
                    "type": "text",
                    "text": "🤖 AI จะวิเคราะห์และแนะนำ:",
                    "weight": "bold",
                    "size": "sm",
                    "margin": "lg"
                },
                {
                    "type": "text",
                    "text": "• จุดเข้าซื้อ (Entry Point)\n• จุดขายทำกำไร (Take Profit)\n• จุดตัดขาดทุน (Stop Loss)",
                    "size": "sm",
                    "color": "#666666",
                    "margin": "md",
                    "wrap": True
                }
            ],
            "paddingAll": "20px"
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
        header_color = "#00B900"
        rec_text = "🟢 BUY"
    elif rec == "SELL":
        header_color = "#FF5551"
        rec_text = "🔴 SELL"
    else:
        header_color = "#FFC107"
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
                            "text": f"{analysis.get('confidence', 0)}% conf.",
                            "color": "#ffffffcc",
                            "size": "xs",
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
                        {"type": "text", "text": "คำแนะนำ", "color": "#8c8c8c", "size": "sm", "flex": 1},
                        {"type": "text", "text": rec_text, "size": "lg", "weight": "bold", "flex": 2, "align": "end"}
                    ]
                },
                {"type": "separator", "margin": "lg"},
                {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "lg",
                    "contents": [
                        {"type": "text", "text": "💰 ราคาปัจจุบัน", "color": "#8c8c8c", "size": "sm", "flex": 1},
                        {"type": "text", "text": f"${current_price:,.2f}", "size": "md", "weight": "bold", "flex": 1, "align": "end"}
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "md",
                    "contents": [
                        {"type": "text", "text": "📍 Entry Point", "color": "#00B900", "size": "sm", "flex": 1},
                        {"type": "text", "text": f"${analysis.get('entry_price', 0):,.2f}", "size": "md", "flex": 1, "align": "end"}
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "md",
                    "contents": [
                        {"type": "text", "text": "🎯 Take Profit", "color": "#27ACB2", "size": "sm", "flex": 1},
                        {"type": "text", "text": f"${analysis.get('take_profit', 0):,.2f}", "size": "md", "flex": 1, "align": "end"}
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "md",
                    "contents": [
                        {"type": "text", "text": "🛑 Stop Loss", "color": "#FF5551", "size": "sm", "flex": 1},
                        {"type": "text", "text": f"${analysis.get('stop_loss', 0):,.2f}", "size": "md", "flex": 1, "align": "end"}
                    ]
                },
                {"type": "separator", "margin": "lg"},
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


def create_watchlist_flex(watchlist: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    สร้าง Flex Message แสดง Watchlist
    """
    if not watchlist:
        return {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "⭐ Watchlist ว่างเปล่า",
                        "size": "lg",
                        "weight": "bold",
                        "align": "center"
                    },
                    {
                        "type": "text",
                        "text": "พิมพ์ชื่อหุ้น เช่น AAPL\nแล้วกด 'เพิ่ม Watchlist'",
                        "size": "sm",
                        "color": "#666666",
                        "align": "center",
                        "margin": "lg",
                        "wrap": True
                    }
                ],
                "paddingAll": "30px"
            }
        }
    
    # Create list of stocks
    stock_items = []
    for item in watchlist[:10]:  # Max 10 items
        symbol = item.get("symbol", "N/A")
        added_price = item.get("added_price", 0)
        
        stock_items.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": symbol,
                    "size": "md",
                    "weight": "bold",
                    "flex": 2
                },
                {
                    "type": "text",
                    "text": f"${added_price:,.2f}",
                    "size": "sm",
                    "color": "#666666",
                    "flex": 2,
                    "align": "end"
                }
            ],
            "margin": "md"
        })
    
    return {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": f"⭐ Watchlist ({len(watchlist)} หุ้น)",
                    "color": "#ffffff",
                    "size": "lg",
                    "weight": "bold"
                }
            ],
            "backgroundColor": "#FFA000",
            "paddingAll": "20px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "กดชื่อหุ้นเพื่อดูรายละเอียด",
                    "size": "xs",
                    "color": "#999999"
                },
                {"type": "separator", "margin": "md"},
                *stock_items
            ],
            "paddingAll": "20px"
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "💡 พิมพ์ชื่อหุ้นเพื่อดูราคาล่าสุด",
                    "size": "xs",
                    "color": "#999999",
                    "align": "center"
                }
            ],
            "paddingAll": "10px"
        }
    }
