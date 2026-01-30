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
# Gemini AI Configuration
# ============================================
# API Key สำหรับ Google Gemini AI
# ดึงได้จาก https://aistudio.google.com/app/apikey
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# ============================================
# Stock Monitoring Targets
# ============================================
# โครงสร้างแบบ List of Dictionaries
# 
# Fields:
#   - symbol: ชื่อหุ้น (ต้องตรงกับ Yahoo Finance)
#   - name: ชื่อเต็มของหุ้น
#   - target_price: (Optional) ราคาเป้าหมายแบบ Manual
#
# ถ้าเปิด AI Analysis จะใช้ค่าจาก AI แทน target_price

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

# เปิด/ปิดการแจ้งเตือนเมื่อราคาถึงเป้า (Manual target_price)
SEND_PRICE_ALERT = True

# เปิด/ปิดการใช้ AI วิเคราะห์หุ้น (ต้องมี GEMINI_API_KEY)
# ถ้าเปิด AI จะวิเคราะห์จุดซื้อ/ขาย/TP/SL ให้อัตโนมัติ
USE_AI_ANALYSIS = True
