"""
Stock Monitor LINE Chatbot - Main Application
==============================================
Flask server รับ Webhook จาก LINE และตอบกลับผู้ใช้

Features:
- รับข้อความชื่อหุ้น → AI วิเคราะห์
- จัดการ Watchlist
- ตั้งค่าแจ้งเตือน
"""

import os
import json
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    PushMessageRequest,
    TextMessage,
    FlexMessage,
    FlexContainer,
    QuickReply,
    QuickReplyItem,
    MessageAction,
    PostbackAction
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    PostbackEvent,
    FollowEvent
)
from linebot.v3.exceptions import InvalidSignatureError

from src.stock_service import get_current_price, get_price_history
from src.ai_service import analyze_stock_with_ai
from src.firebase_service import (
    add_to_watchlist,
    remove_from_watchlist,
    get_watchlist,
    add_alert,
    get_user_alerts
)
from src.flex_templates import (
    create_ai_analysis_flex,
    create_watchlist_flex,
    create_welcome_flex,
    create_help_flex,
    create_alerts_flex,
    create_menu_flex
)

# Initialize Flask
app = Flask(__name__)

# LINE Bot Configuration
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    print("⚠️ Warning: LINE credentials not set")

configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN or "")
handler = WebhookHandler(LINE_CHANNEL_SECRET or "dummy")


@app.route("/")
def home():
    """Health check endpoint"""
    return {"status": "ok", "message": "Stock Monitor Bot is running! 🚀"}


@app.route("/test-ai")
def test_ai():
    """ทดสอบว่า AI ทำงานไหม"""
    import os
    
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    result = {
        "gemini_key_exists": gemini_key is not None,
        "gemini_key_length": len(gemini_key) if gemini_key else 0,
        "gemini_key_preview": gemini_key[:10] + "..." if gemini_key and len(gemini_key) > 10 else "NOT SET"
    }
    
    # Try to test AI
    if gemini_key:
        try:
            from src.ai_service import analyze_stock_with_ai
            analysis = analyze_stock_with_ai(
                symbol="AAPL",
                current_price=150.0,
                price_history=[{"date": "2024-01-01", "close": 145.0}],
                company_name="Apple Inc."
            )
            result["ai_test"] = "SUCCESS"
            result["ai_result"] = analysis
        except Exception as e:
            result["ai_test"] = "FAILED"
            result["ai_error"] = str(e)
    else:
        result["ai_test"] = "SKIPPED - No API Key"
    
    return result




@app.route("/setup-richmenu")
def setup_rich_menu():
    """
    สร้าง Rich Menu อัตโนมัติ - เรียก URL นี้ครั้งเดียวเพื่อติดตั้งเมนู
    """
    import requests
    
    if not LINE_CHANNEL_ACCESS_TOKEN:
        return {"error": "LINE_CHANNEL_ACCESS_TOKEN not set"}, 400
    
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Step 1: Create Rich Menu
    rich_menu_data = {
        "size": {"width": 2500, "height": 843},
        "selected": True,
        "name": "Stock Monitor Menu",
        "chatBarText": "📊 เมนู",
        "areas": [
            {
                "bounds": {"x": 0, "y": 0, "width": 625, "height": 843},
                "action": {"type": "message", "text": "MENU"}
            },
            {
                "bounds": {"x": 625, "y": 0, "width": 625, "height": 843},
                "action": {"type": "message", "text": "WATCHLIST"}
            },
            {
                "bounds": {"x": 1250, "y": 0, "width": 625, "height": 843},
                "action": {"type": "message", "text": "ALERTS"}
            },
            {
                "bounds": {"x": 1875, "y": 0, "width": 625, "height": 843},
                "action": {"type": "message", "text": "HELP"}
            }
        ]
    }
    
    # Create rich menu
    create_resp = requests.post(
        "https://api.line.me/v2/bot/richmenu",
        headers=headers,
        json=rich_menu_data
    )
    
    if create_resp.status_code != 200:
        return {"error": "Failed to create rich menu", "details": create_resp.text}, 400
    
    rich_menu_id = create_resp.json().get("richMenuId")
    
    # Step 2: Upload Rich Menu Image (simple colored boxes)
    # Using a placeholder - ideally upload a real image
    # For now, we'll use text-based menu which doesn't need image
    
    # Step 3: Set as default rich menu for all users
    default_resp = requests.post(
        f"https://api.line.me/v2/bot/user/all/richmenu/{rich_menu_id}",
        headers=headers
    )
    
    if default_resp.status_code != 200:
        return {"error": "Failed to set default rich menu", "details": default_resp.text}, 400
    
    return {
        "status": "success",
        "message": "Rich Menu created and set as default!",
        "rich_menu_id": rich_menu_id,
        "note": "Please upload menu image via LINE Official Account Manager"
    }


@app.route("/delete-richmenu")
def delete_rich_menu():
    """ลบ Rich Menu ทั้งหมด"""
    import requests
    
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    
    # Get all rich menus
    list_resp = requests.get(
        "https://api.line.me/v2/bot/richmenu/list",
        headers=headers
    )
    
    if list_resp.status_code != 200:
        return {"error": "Failed to list rich menus"}, 400
    
    rich_menus = list_resp.json().get("richmenus", [])
    deleted = []
    
    for menu in rich_menus:
        menu_id = menu.get("richMenuId")
        requests.delete(
            f"https://api.line.me/v2/bot/richmenu/{menu_id}",
            headers=headers
        )
        deleted.append(menu_id)
    
    return {"status": "success", "deleted": deleted}




@app.route("/webhook", methods=["POST"])
def webhook():
    """LINE Webhook endpoint - รับ events จาก LINE"""
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    
    app.logger.info(f"Received webhook: {body[:100]}...")
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.error("Invalid signature")
        abort(400)
    
    return "OK"


@handler.add(FollowEvent)
def handle_follow(event):
    """เมื่อมีคน Add เป็นเพื่อน - ส่งข้อความต้อนรับ"""
    user_id = event.source.user_id
    
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
        # ส่ง Welcome message
        welcome_flex = create_welcome_flex()
        
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    FlexMessage(
                        alt_text="ยินดีต้อนรับสู่ Stock Monitor Bot!",
                        contents=FlexContainer.from_dict(welcome_flex)
                    )
                ]
            )
        )


@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    """รับข้อความจากผู้ใช้ - วิเคราะห์หุ้น"""
    user_id = event.source.user_id
    text = event.message.text.strip().upper()
    
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
        # Check for commands
        if text in ["HELP", "วิธีใช้", "ช่วยเหลือ"]:
            help_flex = create_help_flex()
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        FlexMessage(
                            alt_text="วิธีใช้งาน",
                            contents=FlexContainer.from_dict(help_flex)
                        )
                    ]
                )
            )
            return
        
        if text in ["WATCHLIST", "รายการ", "ดูรายการ"]:
            watchlist = get_watchlist(user_id)
            watchlist_flex = create_watchlist_flex(watchlist)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        FlexMessage(
                            alt_text="Watchlist ของคุณ",
                            contents=FlexContainer.from_dict(watchlist_flex)
                        )
                    ]
                )
            )
            return
        
        if text in ["ALERTS", "แจ้งเตือน", "การแจ้งเตือน"]:
            alerts = get_user_alerts(user_id)
            alerts_flex = create_alerts_flex(alerts)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        FlexMessage(
                            alt_text="การแจ้งเตือนของคุณ",
                            contents=FlexContainer.from_dict(alerts_flex)
                        )
                    ]
                )
            )
            return
        
        if text in ["MENU", "เมนู"]:
            menu_flex = create_menu_flex()
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        FlexMessage(
                            alt_text="เมนูหลัก",
                            contents=FlexContainer.from_dict(menu_flex)
                        )
                    ]
                )
            )
            return
        
        # Assume it's a stock symbol - analyze it
        symbol = text
        
        # Get current price
        current_price = get_current_price(symbol)
        
        if current_price is None:
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(text=f"❌ ไม่พบหุ้น '{symbol}'\n\nลองใช้ชื่อย่อเช่น:\n• AAPL (Apple)\n• TSLA (Tesla)\n• NVDA (Nvidia)")
                    ]
                )
            )
            return
        
        # Get price history for AI
        price_history = get_price_history(symbol, days=30)
        
        # AI Analysis
        analysis = analyze_stock_with_ai(
            symbol=symbol,
            current_price=current_price,
            price_history=price_history,
            company_name=symbol
        )
        
        # Create Flex Message
        analysis_flex = create_ai_analysis_flex(
            symbol=symbol,
            name=symbol,
            current_price=current_price,
            analysis=analysis
        )
        
        # Quick Reply buttons
        quick_reply = QuickReply(
            items=[
                QuickReplyItem(
                    action=PostbackAction(
                        label="➕ เพิ่ม Watchlist",
                        data=f"action=add_watchlist&symbol={symbol}&price={current_price}"
                    )
                ),
                QuickReplyItem(
                    action=PostbackAction(
                        label="🔔 ตั้งแจ้งเตือน",
                        data=f"action=set_alert&symbol={symbol}&entry={analysis.get('entry_price', 0)}&tp={analysis.get('take_profit', 0)}&sl={analysis.get('stop_loss', 0)}"
                    )
                ),
                QuickReplyItem(
                    action=MessageAction(
                        label="📋 Watchlist",
                        text="WATCHLIST"
                    )
                )
            ]
        )
        
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    FlexMessage(
                        alt_text=f"🤖 AI วิเคราะห์ {symbol}",
                        contents=FlexContainer.from_dict(analysis_flex),
                        quick_reply=quick_reply
                    )
                ]
            )
        )


@handler.add(PostbackEvent)
def handle_postback(event):
    """รับ Postback จากปุ่มกด"""
    user_id = event.source.user_id
    data = event.postback.data
    
    # Parse postback data
    params = dict(param.split("=") for param in data.split("&"))
    action = params.get("action")
    
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
        if action == "add_watchlist":
            symbol = params.get("symbol")
            price = float(params.get("price", 0))
            
            # Add to Firebase
            add_to_watchlist(user_id, symbol, price)
            
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(text=f"✅ เพิ่ม {symbol} ใน Watchlist แล้ว!")
                    ]
                )
            )
        
        elif action == "set_alert":
            symbol = params.get("symbol")
            entry = float(params.get("entry", 0))
            tp = float(params.get("tp", 0))
            sl = float(params.get("sl", 0))
            
            # Add alert to Firebase
            add_alert(user_id, symbol, entry, tp, sl)
            
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(
                            text=f"🔔 ตั้งแจ้งเตือน {symbol} แล้ว!\n\n"
                                 f"📍 Entry: ${entry:,.2f}\n"
                                 f"🎯 Take Profit: ${tp:,.2f}\n"
                                 f"🛑 Stop Loss: ${sl:,.2f}"
                        )
                    ]
                )
            )
        
        elif action == "remove_watchlist":
            symbol = params.get("symbol")
            remove_from_watchlist(user_id, symbol)
            
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(text=f"🗑️ ลบ {symbol} ออกจาก Watchlist แล้ว")
                    ]
                )
            )
        
        elif action == "delete_alert":
            symbol = params.get("symbol")
            from src.firebase_service import mark_alert_triggered
            mark_alert_triggered(user_id, symbol)
            
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(text=f"🗑️ ลบการแจ้งเตือน {symbol} แล้ว")
                    ]
                )
            )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
