"""
Configuration Module - src/config.py
=====================================
เก็บค่าคงที่และการตั้งค่าทั้งหมดของระบบ
แยก Data ออกจาก Logic เพื่อให้แก้ไขได้ง่ายโดยไม่ต้องแก้โค้ดส่วนอื่น
"""

import os

# ============================================
# LINE Messaging API Configuration
# ============================================
# ดึง Token จาก Environment Variable (Secure way)
# ไม่ Hardcode Token ในโค้ดเพื่อความปลอดภัย

# Channel Access Token จาก LINE Developers Console
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

# User ID ที่จะส่งข้อความหา (ดูได้จาก LINE Developers Console > Your user ID)
# หรือ User ID ของคนที่ Add เป็นเพื่อนกับ LINE OA
LINE_USER_ID = os.getenv("LINE_USER_ID")

# LINE Messaging API Endpoint
LINE_API_ENDPOINT = "https://api.line.me/v2/bot/message/push"


# ============================================
# Stock Monitoring Targets
# ============================================
# โครงสร้างแบบ List of Dictionaries
# ขยายผลง่าย เช่น เพิ่มเงื่อนไข upper_limit, lower_limit ได้ในอนาคต
#
# Fields:
#   - symbol: ชื่อหุ้น (ต้องตรงกับ Yahoo Finance)
#   - target_price: ราคาเป้าหมายที่ต้องการแจ้งเตือน (แจ้งเมื่อราคา <= target)
#   - name: ชื่อเต็มของหุ้น (สำหรับแสดงในข้อความ)

TARGETS = [
    {
        "symbol": "AMD",
        "name": "Advanced Micro Devices",
        "target_price": 120.00
    },
    {
        "symbol": "TSLA",
        "name": "Tesla Inc.",
        "target_price": 180.00
    },
    {
        "symbol": "NVDA",
        "name": "NVIDIA Corporation",
        "target_price": 450.00
    },
    {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "target_price": 170.00
    },
    {
        "symbol": "GOOGL",
        "name": "Alphabet Inc.",
        "target_price": 130.00
    }
]


# ============================================
# Notification Settings
# ============================================
# ตั้งค่าเกี่ยวกับการแจ้งเตือน

# เปิด/ปิดการส่ง Summary Report ทุกครั้งที่รัน
# ⚠️ ปิดไว้เพื่อประหยัด Quota (LINE Messaging API ฟรี 200 ข้อความ/เดือน)
SEND_SUMMARY_REPORT = False

# เปิด/ปิดการแจ้งเตือนเมื่อราคาถึงเป้า
SEND_PRICE_ALERT = True
