"""
Stock Monitoring System - Main Orchestrator
=============================================
ไฟล์หลักที่รัน Logic ทั้งหมด (The Execution Core)
ทำหน้าที่ร้อยเรียงทุก Module เข้าด้วยกัน

Workflow:
1. ตรวจสอบ Configuration
2. ดึงราคาหุ้นทุกตัวจาก Yahoo Finance
3. ใช้ AI วิเคราะห์จุดซื้อ/ขาย (Gemini)
4. เปรียบเทียบกับราคาเป้าหมาย
5. ส่งแจ้งเตือนผ่าน LINE Messaging API (Flex Message)

Serverless Design:
- Stateless: ไม่เก็บ state ใดๆ ระหว่างการรัน
- Ephemeral: ทำงานเสร็จแล้วจบ รอ trigger รอบถัดไป
- Idempotent: รันกี่ครั้งก็ได้ผลลัพธ์เหมือนกัน (ณ เวลาเดียวกัน)
"""

import os
from src.config import (
    TARGETS, 
    LINE_CHANNEL_ACCESS_TOKEN, 
    LINE_USER_ID,
    SEND_SUMMARY_REPORT, 
    SEND_PRICE_ALERT,
    USE_AI_ANALYSIS
)
from src.stock_service import get_current_price, get_price_history
from src.line_service import (
    send_price_alert, 
    send_summary_report,
    send_ai_alert,
    send_stop_loss_alert
)
from src.ai_service import analyze_stock_with_ai
from src.firebase_service import get_all_watchlists
from datetime import datetime


def main():
    """
    Main function - Entry point ของโปรแกรม
    """
    print("=" * 50)
    print("🚀 STOCK MONITORING SYSTEM + AI ANALYSIS")
    print(f"⏰ Run Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # ============================================
    # Step 1: Validate Configuration
    # ============================================
    if not LINE_CHANNEL_ACCESS_TOKEN:
        print("❌ Error: LINE_CHANNEL_ACCESS_TOKEN not found!")
        print("   Please set LINE_CHANNEL_ACCESS_TOKEN in GitHub Secrets")
        return
    
    if not LINE_USER_ID:
        print("❌ Error: LINE_USER_ID not found!")
        print("   Please set LINE_USER_ID in GitHub Secrets")
        return
    
    if not TARGETS:
        print("⚠️ Warning: No stock targets configured!")
        return
    
    # Check AI availability
    gemini_key = os.getenv("GEMINI_API_KEY")
    ai_enabled = USE_AI_ANALYSIS and gemini_key
    print(f"🤖 AI Analysis: {'✅ Enabled' if ai_enabled else '❌ Disabled'}")
    print(f"📋 Monitoring {len(TARGETS)} stocks...")
    print("-" * 50)
    
    # ============================================
    # Step 2: Fetch & Process Stock Prices
    # ============================================
    summary_data = []
    alerts_sent = 0
    
    for item in TARGETS:
        symbol = item['symbol']
        name = item.get('name', symbol)
        
        # 2.1 Fetch current price from Yahoo Finance
        current_price = get_current_price(symbol)
        
        if current_price is None:
            print(f"⚠️ {symbol}: Could not fetch price, skipping...")
            summary_data.append({
                "symbol": symbol,
                "price": None,
                "target": item.get('target_price', 0)
            })
            continue
        
        print(f"📈 {symbol}: ${current_price:,.2f}")
        
        # ============================================
        # Step 3: AI Analysis (if enabled)
        # ============================================
        if ai_enabled:
            print(f"   🤖 Running AI analysis...")
            
            # Get price history for AI
            price_history = get_price_history(symbol, days=30)
            
            # Analyze with Gemini AI
            analysis = analyze_stock_with_ai(
                symbol=symbol,
                current_price=current_price,
                price_history=price_history,
                company_name=name
            )
            
            if analysis:
                print(f"   📊 AI Recommendation: {analysis['recommendation']}")
                print(f"   📍 Entry: ${analysis['entry_price']:,.2f} | TP: ${analysis['take_profit']:,.2f} | SL: ${analysis['stop_loss']:,.2f}")
                
                # Send AI analysis alert if price hits entry point and BUY recommended
                if current_price <= analysis['entry_price'] and analysis['recommendation'] == 'BUY':
                    print(f"   🚨 Price at entry point! Sending AI alert...")
                    
                    success, status_code = send_ai_alert(
                        symbol=symbol,
                        name=name,
                        current_price=current_price,
                        analysis=analysis,
                        user_id=LINE_USER_ID,
                        token=LINE_CHANNEL_ACCESS_TOKEN
                    )
                    
                    if success:
                        print(f"   ✅ AI alert sent (Flex Message)!")
                        alerts_sent += 1
                    else:
                        print(f"   ❌ Failed to send AI alert (Status: {status_code})")
                
                # Check stop loss
                if current_price <= analysis['stop_loss']:
                    print(f"   🛑 Price hit STOP LOSS! Sending alert...")
                    
                    success, status_code = send_stop_loss_alert(
                        symbol=symbol,
                        name=name,
                        current_price=current_price,
                        stop_loss=analysis['stop_loss'],
                        user_id=LINE_USER_ID,
                        token=LINE_CHANNEL_ACCESS_TOKEN
                    )
                    
                    if success:
                        print(f"   ✅ Stop Loss alert sent (Flex Message)!")
                        alerts_sent += 1
        
        # ============================================
        # Step 4: Legacy Price Alert (fallback)
        # ============================================
        target_price = item.get('target_price', 0)
        if target_price > 0:
            summary_data.append({
                "symbol": symbol,
                "price": current_price,
                "target": target_price
            })
            
            if SEND_PRICE_ALERT and current_price <= target_price:
                print(f"   📤 Sending price alert for {symbol}...")
                
                success, status_code = send_price_alert(
                    symbol=symbol,
                    name=name,
                    current_price=current_price,
                    target_price=target_price,
                    user_id=LINE_USER_ID,
                    token=LINE_CHANNEL_ACCESS_TOKEN
                )
                
                if success:
                    print(f"   ✅ Price alert sent (Flex Message)!")
                    alerts_sent += 1
                else:
                    print(f"   ❌ Failed to send alert (Status: {status_code})")
    
    print("-" * 50)
    
    # ============================================
    # Step 5: Send Summary Report (Optional)
    # ============================================
    if SEND_SUMMARY_REPORT and summary_data:
        print("📊 Sending summary report...")
        
        success, status_code = send_summary_report(
            stocks_data=summary_data,
            user_id=LINE_USER_ID,
            token=LINE_CHANNEL_ACCESS_TOKEN
        )
        
        if success:
            print("✅ Summary report sent!")
        else:
            print(f"❌ Failed to send summary (Status: {status_code})")
    
    # ============================================
    # Step 6: Job Completion (Stateless Termination)
    # ============================================
    print("=" * 50)
    print("📈 JOB SUMMARY")
    print(f"   Stocks Checked: {len(TARGETS)}")
    print(f"   Alerts Sent: {alerts_sent}")
    print(f"   AI Analysis: {'Enabled' if ai_enabled else 'Disabled'}")
    print(f"   End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    print("✅ Job Finished (Stateless Termination)")


def send_watchlist_summary():
    """
    ส่ง Watchlist Summary พร้อม AI Analysis ให้ทุก User
    เรียกจาก GitHub Actions scheduler ทุกเช้า
    """
    import requests
    
    print("=" * 50)
    print("📊 WATCHLIST DAILY SUMMARY")
    print(f"⏰ Run Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    if not LINE_CHANNEL_ACCESS_TOKEN:
        print("❌ LINE_CHANNEL_ACCESS_TOKEN not found")
        return
    
    # Get all users' watchlists
    all_watchlists = get_all_watchlists()
    
    if not all_watchlists:
        print("📋 No watchlists found")
        return
    
    print(f"👥 Found {len(all_watchlists)} users with watchlists")
    
    for user_data in all_watchlists:
        user_id = user_data["user_id"]
        stocks = user_data["stocks"]
        
        print(f"\n📤 Processing user: {user_id[:8]}... ({len(stocks)} stocks)")
        
        summary_items = []
        best_opportunity = None
        
        for stock in stocks:
            symbol = stock["symbol"]
            
            # Get current price
            current_price = get_current_price(symbol)
            if current_price is None:
                continue
            
            # Get price history for AI
            price_history = get_price_history(symbol, days=30)
            
            # AI Analysis
            analysis = analyze_stock_with_ai(
                symbol=symbol,
                current_price=current_price,
                price_history=price_history,
                company_name=symbol
            )
            
            if analysis:
                item = {
                    "symbol": symbol,
                    "current_price": current_price,
                    "recommendation": analysis["recommendation"],
                    "entry_price": analysis["entry_price"],
                    "confidence": analysis.get("confidence", 50),
                    "analysis": analysis.get("analysis", "")
                }
                summary_items.append(item)
                
                # Track best opportunity (BUY with highest confidence)
                if analysis["recommendation"] == "BUY":
                    if best_opportunity is None or analysis.get("confidence", 0) > best_opportunity.get("confidence", 0):
                        best_opportunity = item
                
                print(f"   ✅ {symbol}: ${current_price:.2f} - {analysis['recommendation']}")
        
        if not summary_items:
            continue
        
        # Build Flex Message for summary
        flex_message = _build_watchlist_summary_flex(summary_items, best_opportunity)
        
        # Send to user
        try:
            headers = {
                "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
                "Content-Type": "application/json"
            }
            
            body = {
                "to": user_id,
                "messages": [{
                    "type": "flex",
                    "altText": f"📊 Watchlist Summary - {len(summary_items)} หุ้น",
                    "contents": flex_message
                }]
            }
            
            resp = requests.post(
                "https://api.line.me/v2/bot/message/push",
                headers=headers,
                json=body
            )
            
            if resp.status_code == 200:
                print(f"   📤 Summary sent to user!")
            else:
                print(f"   ❌ Failed to send: {resp.text}")
                
        except Exception as e:
            print(f"   ❌ Error sending: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Watchlist Summary Job Completed")


def _build_watchlist_summary_flex(items: list, best_opportunity: dict = None) -> dict:
    """สร้าง Flex Message สำหรับ Watchlist Summary"""
    
    # Header
    header_color = "#1DB446" if best_opportunity else "#4A90D9"
    
    # Build stock rows
    stock_contents = []
    for item in items:
        rec_color = {
            "BUY": "#1DB446",
            "SELL": "#E53935",
            "HOLD": "#FFB300"
        }.get(item["recommendation"], "#888888")
        
        stock_contents.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {"type": "text", "text": item["symbol"], "weight": "bold", "size": "sm", "flex": 2},
                {"type": "text", "text": f"${item['current_price']:.2f}", "size": "sm", "flex": 2, "align": "end"},
                {"type": "text", "text": item["recommendation"], "size": "sm", "flex": 1, "align": "end", "color": rec_color, "weight": "bold"}
            ],
            "margin": "md"
        })
    
    # Build best opportunity section
    best_section = []
    if best_opportunity:
        best_section = [
            {"type": "separator", "margin": "lg"},
            {
                "type": "box",
                "layout": "vertical",
                "margin": "lg",
                "contents": [
                    {"type": "text", "text": "🎯 โอกาสที่ดีที่สุด", "weight": "bold", "color": "#1DB446"},
                    {"type": "text", "text": f"{best_opportunity['symbol']} - รอซื้อที่ ${best_opportunity['entry_price']:.2f}", "size": "sm", "margin": "sm"},
                    {"type": "text", "text": best_opportunity.get("analysis", "")[:100], "size": "xs", "color": "#888888", "wrap": True, "margin": "sm"}
                ]
            }
        ]
    
    return {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": header_color,
            "contents": [
                {"type": "text", "text": "📊 WATCHLIST SUMMARY", "color": "#FFFFFF", "weight": "bold", "size": "lg"},
                {"type": "text", "text": datetime.now().strftime("%d %b %Y"), "color": "#FFFFFFCC", "size": "xs"}
            ]
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "หุ้น", "weight": "bold", "size": "xs", "color": "#888888", "flex": 2},
                        {"type": "text", "text": "ราคา", "weight": "bold", "size": "xs", "color": "#888888", "flex": 2, "align": "end"},
                        {"type": "text", "text": "สัญญาณ", "weight": "bold", "size": "xs", "color": "#888888", "flex": 1, "align": "end"}
                    ]
                },
                {"type": "separator", "margin": "sm"},
                *stock_contents,
                *best_section
            ]
        }
    }


if __name__ == "__main__":
    main()
