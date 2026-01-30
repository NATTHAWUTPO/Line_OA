# 📈 Stock Monitoring System

> **Serverless Stock Price Alert via LINE Messaging API**  
> ระบบแจ้งเตือนราคาหุ้นอัตโนมัติผ่าน LINE โดยใช้ GitHub Actions เป็น Serverless Infrastructure

[![GitHub Actions](https://img.shields.io/badge/Powered%20by-GitHub%20Actions-2088FF?logo=github-actions&logoColor=white)](https://github.com/features/actions)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org)
[![LINE](https://img.shields.io/badge/LINE-Messaging%20API-00B900?logo=line&logoColor=white)](https://developers.line.biz/)

---

## 🌟 Features

- ✅ **Real-time Monitoring** - ดึงราคาหุ้นล่าสุดจาก Yahoo Finance
- 🔔 **Smart Alerts** - แจ้งเตือนผ่าน LINE **เฉพาะเมื่อราคาถึงเป้าหมาย**
- ⏰ **Scheduled Runs** - ทำงานอัตโนมัติทุกชั่วโมงในเวลาตลาด
- 💰 **$0 Cost** - ใช้ GitHub Actions ฟรี + LINE Free Tier (200 ข้อความ/เดือน)
- 🔐 **Secure** - เก็บ Token ใน GitHub Secrets

---

## 📂 Project Structure

```
stock-monitoring-system/
│
├── .github/
│   └── workflows/
│       └── scheduler.yml    # GitHub Actions Cron Job
│
├── src/                     # Source Code (Modular Design)
│   ├── __init__.py
│   ├── config.py            # Configuration & Targets
│   ├── stock_service.py     # Yahoo Finance Integration
│   └── line_service.py      # LINE Messaging API Integration
│
├── main.py                  # Main Orchestrator
├── requirements.txt         # Python Dependencies
├── .gitignore              
└── README.md               
```

---

## 🚀 Quick Start

### Prerequisites
- GitHub Account
- LINE Official Account (สร้างฟรี)

### Step 1: สร้าง LINE Official Account & Messaging API

1. ไปที่ [LINE Developers](https://developers.line.biz/)
2. สร้าง **Provider** (ถ้ายังไม่มี)
3. สร้าง **Messaging API Channel**
4. ใน Channel Settings:
   - Copy **Channel Access Token** (กด Issue ถ้ายังไม่มี)
   - Copy **Your user ID** (อยู่ใน Basic Settings)

### Step 2: Fork & Clone

```bash
git clone https://github.com/YOUR_USERNAME/stock-monitoring-system.git
cd stock-monitoring-system
```

### Step 3: Configure Stock Targets

Edit `src/config.py`:
```python
TARGETS = [
    {"symbol": "AAPL", "name": "Apple Inc.", "target_price": 170.00},
    {"symbol": "TSLA", "name": "Tesla Inc.", "target_price": 180.00},
    # Add more stocks...
]
```

### Step 4: Add Secrets to GitHub

1. Go to repo → **Settings** → **Secrets and variables** → **Actions**
2. Add these secrets:

| Secret Name | Value |
|-------------|-------|
| `LINE_CHANNEL_ACCESS_TOKEN` | Channel Access Token จาก LINE Developers |
| `LINE_USER_ID` | Your user ID จาก LINE Developers |

### Step 5: Enable GitHub Actions

1. Go to **Actions** tab
2. Click **Enable workflows**
3. The scheduler will run automatically!

---

## ⏰ Schedule Configuration

The workflow runs during US market hours (9:00 AM - 4:00 PM ET) on weekdays.

Edit `.github/workflows/scheduler.yml` to customize:
```yaml
schedule:
  - cron: '30 14-21 * * 1-5'  # Every hour during market hours
```

---

## 🛠️ Local Development

### Setup Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Set Environment Variables
```bash
# Windows PowerShell
$env:LINE_CHANNEL_ACCESS_TOKEN="your_token_here"
$env:LINE_USER_ID="your_user_id_here"

# Linux/Mac
export LINE_CHANNEL_ACCESS_TOKEN="your_token_here"
export LINE_USER_ID="your_user_id_here"
```

### Run Locally
```bash
python main.py
```

---

## 📱 LINE Official Account Setup

### วิธีสร้าง LINE OA และรับ Token

1. **สร้าง Provider**
   - ไปที่ https://developers.line.biz/
   - Login ด้วย LINE Account
   - กด Create → Provider

2. **สร้าง Messaging API Channel**
   - เลือก Provider ที่สร้าง
   - กด Create a Messaging API channel
   - กรอกข้อมูล Channel

3. **รับ Channel Access Token**
   - ไปที่ Messaging API tab
   - เลื่อนลงหา "Channel access token"
   - กด "Issue" จะได้ Token ยาวๆ

4. **รับ Your User ID**
   - ไปที่ Basic settings tab
   - ดูที่ "Your user ID" (ขึ้นต้นด้วย U)

5. **Add LINE OA เป็นเพื่อน**
   - Scan QR Code ใน Messaging API tab
   - **สำคัญ!** ต้อง Add เป็นเพื่อนก่อนจึงจะรับข้อความได้

---

## 💰 LINE Messaging API Pricing

| Plan | ข้อความ/เดือน | ราคา |
|------|--------------|------|
| **Free** | 200 | ฟรี |
| Light | 5,000 | ฿400/เดือน |
| Standard | 30,000 | ฿2,000/เดือน |

> 💡 **Tip:** ระบบนี้ออกแบบมาให้ส่งข้อความเฉพาะเมื่อราคาถึงเป้า ทำให้ใช้ Free Tier ได้สบายๆ!

---

## 🏗️ Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions (Scheduler)                │
│  ┌─────────────┐   Cron Trigger   ┌─────────────────────┐   │
│  │ scheduler.yml│ ──────────────► │ Ubuntu Runner       │   │
│  └─────────────┘   Every Hour     │ (Free Tier)         │   │
│                                   └──────────┬──────────┘   │
└──────────────────────────────────────────────┼──────────────┘
                                               │
                                               ▼
┌──────────────────────────────────────────────────────────────┐
│                     main.py (Orchestrator)                   │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ 1. Load Config    2. Fetch Prices   3. Check Conditions │ │
│  │ 4. Send Alerts (only when price hits target)            │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌─────────────────┐           ┌─────────────────┐
│  Yahoo Finance  │           │ LINE Messaging  │
│  (yfinance API) │           │    API (Push)   │
└─────────────────┘           └─────────────────┘
```

---

## 📝 Technical Highlights (For Portfolio)

- **Serverless Architecture**: Zero infrastructure, pay-per-use model
- **Modular Design**: Separation of Concerns (Config, Service, Logic)
- **Event-Driven**: Cron-triggered execution
- **Stateless Processing**: No database required
- **CI/CD Integration**: GitHub Actions as compute layer
- **API Integration**: Yahoo Finance + LINE Messaging API
- **Cost Optimization**: Smart alerts to stay within free tier limits

---

## 📄 License

MIT License - Free to use for personal and commercial projects.

---

<p align="center">
  Made with ❤️ for learning and investing
</p>
