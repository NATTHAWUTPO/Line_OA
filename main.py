"""
Stock Monitoring System - Main Orchestrator
=============================================
ไฟล์หลักที่รัน Logic ทั้งหมด (The Execution Core)
ทำหน้าที่ร้อยเรียงทุก Module เข้าด้วยกัน

Workflow:
1. ตรวจสอบ Configuration
2. ดึงราคาหุ้นทุกตัวจาก Yahoo Finance
3. เปรียบเทียบกับราคาเป้าหมาย
4. ส่งแจ้งเตือนผ่าน LINE Messaging API (ถ้าราคาถึงเป้า)
5. ส่งสรุปราคาทุกตัว (Optional)

Serverless Design:
- Stateless: ไม่เก็บ state ใดๆ ระหว่างการรัน
- Ephemeral: ทำงานเสร็จแล้วจบ รอ trigger รอบถัดไป
- Idempotent: รันกี่ครั้งก็ได้ผลลัพธ์เหมือนกัน (ณ เวลาเดียวกัน)
"""

from src.config import (
    TARGETS, 
    LINE_CHANNEL_ACCESS_TOKEN, 
    LINE_USER_ID,
    SEND_SUMMARY_REPORT, 
    SEND_PRICE_ALERT
)
from src.stock_service import get_current_price
from src.line_service import send_price_alert, send_summary_report
from datetime import datetime


def main():
    """
    Main function - Entry point ของโปรแกรม
    """
    print("=" * 50)
    print("🚀 STOCK MONITORING SYSTEM")
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
        target_price = item['target_price']
        
        # 2.1 Fetch current price from Yahoo Finance
        current_price = get_current_price(symbol)
        
        if current_price is None:
            print(f"⚠️ {symbol}: Could not fetch price, skipping...")
            summary_data.append({
                "symbol": symbol,
                "price": None,
                "target": target_price
            })
            continue
        
        # 2.2 Log current status
        status_icon = "🟢" if current_price <= target_price else "🔴"
        print(f"{status_icon} {symbol}: ${current_price:,.2f} (Target: ${target_price:,.2f})")
        
        # 2.3 Add to summary
        summary_data.append({
            "symbol": symbol,
            "price": current_price,
            "target": target_price
        })
        
        # ============================================
        # Step 3: Send Alert if Price Hits Target
        # ============================================
        if SEND_PRICE_ALERT and current_price <= target_price:
            print(f"   📤 Sending alert for {symbol}...")
            
            success, status_code = send_price_alert(
                symbol=symbol,
                name=name,
                current_price=current_price,
                target_price=target_price,
                user_id=LINE_USER_ID,
                token=LINE_CHANNEL_ACCESS_TOKEN
            )
            
            if success:
                print(f"   ✅ Alert sent successfully!")
                alerts_sent += 1
            else:
                print(f"   ❌ Failed to send alert (Status: {status_code})")
    
    print("-" * 50)
    
    # ============================================
    # Step 4: Send Summary Report (Optional)
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
    # Step 5: Job Completion (Stateless Termination)
    # ============================================
    print("=" * 50)
    print("📈 JOB SUMMARY")
    print(f"   Stocks Checked: {len(TARGETS)}")
    print(f"   Alerts Sent: {alerts_sent}")
    print(f"   End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    print("✅ Job Finished (Stateless Termination)")


if __name__ == "__main__":
    main()
