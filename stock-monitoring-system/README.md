# 📈 Stock Monitoring System

> **Serverless Stock Price Alert via LINE Notify**  
> ระบบแจ้งเตือนราคาหุ้นอัตโนมัติผ่าน LINE โดยใช้ GitHub Actions เป็น Serverless Infrastructure

[![GitHub Actions](https://img.shields.io/badge/Powered%20by-GitHub%20Actions-2088FF?logo=github-actions&logoColor=white)](https://github.com/features/actions)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org)
[![LINE Notify](https://img.shields.io/badge/LINE-Notify-00B900?logo=line&logoColor=white)](https://notify-bot.line.me/)

---

## 🌟 Features

- ✅ **Real-time Monitoring** - ดึงราคาหุ้นล่าสุดจาก Yahoo Finance
- 🔔 **Instant Alerts** - แจ้งเตือนผ่าน LINE เมื่อราคาถึงเป้าหมาย
- ⏰ **Scheduled Runs** - ทำงานอัตโนมัติทุกชั่วโมงในเวลาตลาด
- 💰 **$0 Cost** - ใช้ GitHub Actions ฟรี (2,000 นาที/เดือน)
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
│   └── line_service.py      # LINE Notify Integration
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
- LINE Notify Token ([Get it here](https://notify-bot.line.me/))

### Step 1: Fork & Clone
```bash
git clone https://github.com/YOUR_USERNAME/stock-monitoring-system.git
cd stock-monitoring-system
```

### Step 2: Configure Stock Targets
Edit `src/config.py`:
```python
TARGETS = [
    {"symbol": "AAPL", "name": "Apple Inc.", "target_price": 170.00},
    {"symbol": "TSLA", "name": "Tesla Inc.", "target_price": 180.00},
    # Add more stocks...
]
```

### Step 3: Add LINE Token to GitHub Secrets
1. Go to your repo → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `LINE_TOKEN`
4. Value: Your LINE Notify Token

### Step 4: Enable GitHub Actions
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

### Set Environment Variable
```bash
export LINE_TOKEN="your_token_here"  # Windows: set LINE_TOKEN=your_token_here
```

### Run Locally
```bash
python main.py
```

---

## 📱 LINE Notify Setup

1. Go to [LINE Notify](https://notify-bot.line.me/)
2. Log in with your LINE account
3. Click **Generate Token**
4. Select a chat room or create a new group
5. Copy the generated token

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
│  │ 4. Send Alerts    5. Generate Summary                   │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌─────────────────┐           ┌─────────────────┐
│  Yahoo Finance  │           │   LINE Notify   │
│  (yfinance API) │           │   (REST API)    │
└─────────────────┘           └─────────────────┘
```

---

## 🎨 Customization

### Add Upper Limit Alert
Modify `src/config.py`:
```python
TARGETS = [
    {
        "symbol": "AAPL",
        "target_price": 170.00,      # Buy alert
        "upper_limit": 200.00        # Sell alert
    }
]
```

### Add Discord Notification
Create `src/discord_service.py` and import in `main.py`

---

## 📝 Technical Highlights (For Portfolio)

- **Serverless Architecture**: Zero infrastructure, pay-per-use model
- **Modular Design**: Separation of Concerns (Config, Service, Logic)
- **Event-Driven**: Cron-triggered execution
- **Stateless Processing**: No database required
- **CI/CD Integration**: GitHub Actions as compute layer
- **API Integration**: Yahoo Finance + LINE Notify

---

## 📄 License

MIT License - Free to use for personal and commercial projects.

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first.

---

<p align="center">
  Made with ❤️ for learning and investing
</p>
