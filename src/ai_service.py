"""
AI Analysis Service Module - src/ai_service.py
===============================================
ใช้ Gemini AI วิเคราะห์หุ้นและแนะนำจุดซื้อ/ขาย/ตัดกำไร/ตัดขาดทุน

Features:
- วิเคราะห์ข้อมูลราคาหุ้นย้อนหลัง
- แนะนำ Entry Point (จุดเข้าซื้อ)
- แนะนำ Take Profit (จุดขายทำกำไร)
- แนะนำ Stop Loss (จุดตัดขาดทุน)
- Rate limiting และ Caching ป้องกัน quota หมด
"""

import os
import json
import time
import google.generativeai as genai
from typing import Optional, Dict, Any


# ===== RATE LIMITING & CACHING =====
# Cache: เก็บผลวิเคราะห์ไว้ 5 นาที ไม่ต้องเรียก API ซ้ำ
_analysis_cache: Dict[str, Dict] = {}
CACHE_TTL_SECONDS = 300  # 5 นาที

# Rate limit: จำกัด 10 requests ต่อนาที
_request_times: list = []
MAX_REQUESTS_PER_MINUTE = 10


def _is_rate_limited() -> bool:
    """เช็คว่าเกิน rate limit หรือยัง"""
    global _request_times
    now = time.time()
    # ลบ request เก่ากว่า 1 นาที
    _request_times = [t for t in _request_times if now - t < 60]
    return len(_request_times) >= MAX_REQUESTS_PER_MINUTE


def _record_request():
    """บันทึกเวลา request"""
    _request_times.append(time.time())


def _get_cached_analysis(symbol: str) -> Optional[Dict]:
    """ดึงผลวิเคราะห์จาก cache ถ้ายังไม่หมดอายุ"""
    if symbol in _analysis_cache:
        cached = _analysis_cache[symbol]
        if time.time() - cached["timestamp"] < CACHE_TTL_SECONDS:
            print(f"📦 Using cached analysis for {symbol}")
            return cached["data"]
    return None


def _cache_analysis(symbol: str, data: Dict):
    """เก็บผลวิเคราะห์ลง cache"""
    _analysis_cache[symbol] = {
        "timestamp": time.time(),
        "data": data
    }


def analyze_stock_with_ai(
    symbol: str,
    current_price: float,
    price_history: list,
    company_name: str = ""
) -> Optional[Dict[str, Any]]:
    """
    ใช้ Gemini AI วิเคราะห์หุ้นและแนะนำจุดซื้อ/ขาย
    
    Args:
        symbol: ชื่อหุ้น (e.g., "AAPL")
        current_price: ราคาปัจจุบัน
        price_history: ราคาย้อนหลัง 30 วัน [{"date": "2024-01-01", "close": 180.5, "high": 182, "low": 179}, ...]
        company_name: ชื่อบริษัท
    
    Returns:
        dict: {
            "recommendation": "BUY" | "SELL" | "HOLD",
            "entry_price": float,      # จุดเข้าซื้อ
            "take_profit": float,      # จุดขายทำกำไร
            "stop_loss": float,        # จุดตัดขาดทุน
            "analysis": str,           # คำอธิบาย
            "confidence": float        # ความมั่นใจ 0-100
        }
    """
    # Check cache first
    cached = _get_cached_analysis(symbol)
    if cached:
        return cached
    
    # Check rate limit
    if _is_rate_limited():
        print(f"⚠️ Rate limited! Using default analysis for {symbol}")
        return _default_analysis(current_price)
    
    # Get API key
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("⚠️ GEMINI_API_KEY not found, using default analysis")
        return _default_analysis(current_price)
    
    try:
        # Record this request for rate limiting
        _record_request()
        
        # Configure genai with fresh key
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # สร้าง prompt สำหรับวิเคราะห์
        prompt = f"""
คุณเป็นนักวิเคราะห์หุ้นมืออาชีพ วิเคราะห์หุ้นนี้และแนะนำจุดซื้อ/ขาย:

หุ้น: {symbol} ({company_name})
ราคาปัจจุบัน: ${current_price}

ข้อมูลราคาย้อนหลัง 30 วัน:
{json.dumps(price_history[-10:], indent=2)}

กรุณาวิเคราะห์และตอบเป็น JSON format เท่านั้น:
{{
    "recommendation": "BUY" หรือ "SELL" หรือ "HOLD",
    "entry_price": ราคาที่แนะนำเข้าซื้อ (ถ้า recommendation เป็น BUY),
    "take_profit": ราคาขายทำกำไร (สูงกว่า entry 5-15%),
    "stop_loss": ราคาตัดขาดทุน (ต่ำกว่า entry 3-7%),
    "analysis": "คำอธิบายสั้นๆ ภาษาไทย ไม่เกิน 2 บรรทัด",
    "confidence": ความมั่นใจ 0-100
}}

ตอบเป็น JSON เท่านั้น ไม่ต้องมี markdown code block
"""
        
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        # ลบ markdown code block ถ้ามี
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
        
        result = json.loads(result_text)
        
        # Validate และ clean data
        analysis_result = {
            "recommendation": result.get("recommendation", "HOLD"),
            "entry_price": float(result.get("entry_price", current_price)),
            "take_profit": float(result.get("take_profit", current_price * 1.10)),
            "stop_loss": float(result.get("stop_loss", current_price * 0.95)),
            "analysis": result.get("analysis", "ไม่มีข้อมูลเพิ่มเติม"),
            "confidence": float(result.get("confidence", 50))
        }
        
        # Cache the result for future use
        _cache_analysis(symbol, analysis_result)
        
        return analysis_result
    
    except json.JSONDecodeError as e:
        print(f"❌ AI response parsing error: {e}")
        return _default_analysis(current_price)
    
    except Exception as e:
        print(f"❌ AI analysis error for {symbol}: {e}")
        return _default_analysis(current_price)


def _default_analysis(current_price: float) -> Dict[str, Any]:
    """
    Default analysis เมื่อ AI ไม่พร้อมใช้งาน
    ใช้ Simple Technical Analysis (STA)
    """
    return {
        "recommendation": "HOLD",
        "entry_price": round(current_price * 0.97, 2),    # ซื้อเมื่อลง 3%
        "take_profit": round(current_price * 1.10, 2),    # ขายเมื่อขึ้น 10%
        "stop_loss": round(current_price * 0.93, 2),      # ตัดขาดทุนที่ 7%
        "analysis": "ใช้การวิเคราะห์เบื้องต้น (AI ไม่พร้อม)",
        "confidence": 30
    }


def format_ai_analysis_message(
    symbol: str,
    name: str,
    current_price: float,
    analysis: Dict[str, Any]
) -> str:
    """
    สร้างข้อความสรุปการวิเคราะห์สำหรับส่ง LINE
    """
    rec = analysis["recommendation"]
    rec_emoji = "🟢" if rec == "BUY" else ("🔴" if rec == "SELL" else "🟡")
    
    message = f"""🤖 AI วิเคราะห์หุ้น

📈 {symbol} - {name}
💰 ราคาปัจจุบัน: ${current_price:,.2f}

{rec_emoji} คำแนะนำ: {rec}
📍 จุดเข้าซื้อ: ${analysis['entry_price']:,.2f}
🎯 Take Profit: ${analysis['take_profit']:,.2f}
🛑 Stop Loss: ${analysis['stop_loss']:,.2f}

📊 ความมั่นใจ: {analysis['confidence']}%
💡 {analysis['analysis']}"""
    
    return message
