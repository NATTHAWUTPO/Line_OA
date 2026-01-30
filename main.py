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


if __name__ == "__main__":
    main()
