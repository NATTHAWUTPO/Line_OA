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
        print(f"⚠️ Rate limited! Using technical analysis for {symbol}")
        return _default_analysis(current_price, price_history)
    
    # Get API keys - try Groq first, then Gemini
    groq_key = os.getenv("GROQ_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    if not groq_key and not gemini_key:
        print("⚠️ No AI API key found, using technical analysis")
        return _default_analysis(current_price, price_history)
    
    # Use Gemini if no Groq key
    if not groq_key and gemini_key:
        return _analyze_with_gemini(symbol, current_price, price_history, company_name, gemini_key)
    
    try:
        # Record this request for rate limiting
        _record_request()
        
        # === Calculate Technical Indicators for AI ===
        closes = []
        if price_history and len(price_history) >= 14:
            closes = [p.get("close", p.get("price", current_price)) for p in price_history]
        
        # Calculate indicators (or use defaults)
        if len(closes) >= 14:
            rsi = _calculate_rsi(closes, 14)
            sma_10 = sum(closes[-10:]) / 10 if len(closes) >= 10 else current_price
            sma_20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else current_price
            bb_upper, bb_middle, bb_lower = _calculate_bollinger_bands(closes, 20, 2)
            macd_line, signal_line, macd_histogram = _calculate_macd(closes)
            
            # Determine trend signals
            ma_trend = "BULLISH (Golden Cross)" if sma_10 > sma_20 else "BEARISH (Death Cross)"
            rsi_signal = "OVERSOLD (BUY Signal)" if rsi < 30 else ("OVERBOUGHT (SELL Signal)" if rsi > 70 else "NEUTRAL")
            bb_position = "NEAR LOWER (BUY Zone)" if current_price < bb_lower else ("NEAR UPPER (SELL Zone)" if current_price > bb_upper else "MIDDLE")
            macd_signal = "BULLISH" if macd_histogram > 0 else "BEARISH"
            
            indicators_text = f"""
=== TECHNICAL INDICATORS ===
RSI (14): {rsi:.1f} - {rsi_signal}
SMA 10: ${sma_10:.2f} | SMA 20: ${sma_20:.2f} - {ma_trend}
Bollinger Bands: Upper ${bb_upper:.2f} | Middle ${bb_middle:.2f} | Lower ${bb_lower:.2f} - Price {bb_position}
MACD: {macd_line:.2f} (Signal: {signal_line:.2f}) - {macd_signal}
"""
        else:
            indicators_text = "\n=== TECHNICAL INDICATORS ===\nInsufficient data for full analysis\n"
        
        # Use Groq API
        from groq import Groq
        client = Groq(api_key=groq_key)
        
        # สร้าง prompt ที่รวม AI + Technical Indicators
        prompt = f"""You are a professional stock analyst combining TECHNICAL ANALYSIS with MARKET SENTIMENT.

Stock: {symbol} ({company_name})
Current Price: ${current_price}
{indicators_text}
Historical prices (last 5 days):
{json.dumps(price_history[-5:] if price_history else [], indent=2)}

ANALYSIS GUIDELINES:
1. Use the technical indicators above to determine trend direction
2. RSI < 30 = oversold (good to buy), RSI > 70 = overbought (consider selling)
3. Price near Lower Bollinger = potential buy, near Upper = potential sell
4. MACD Bullish = uptrend, Bearish = downtrend
5. Combine indicators to form a consensus recommendation

IMPORTANT: Respond ONLY with valid JSON. Use the technical data to calculate realistic entry/TP/SL prices.

Example format:
{{"recommendation": "BUY", "entry_price": {bb_middle * 0.99 if len(closes) >= 14 else current_price * 0.98:.2f}, "take_profit": {bb_upper * 0.98 if len(closes) >= 14 else current_price * 1.10:.2f}, "stop_loss": {bb_lower * 0.98 if len(closes) >= 14 else current_price * 0.93:.2f}, "analysis": "คำอธิบายสั้นๆ รวม sentiment + indicators ภาษาไทย", "confidence": 75}}

Provide your analysis as JSON:"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        
        result_text = response.choices[0].message.content.strip()
        
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
        return _default_analysis(current_price, price_history)
    
    except Exception as e:
        print(f"❌ AI analysis error for {symbol}: {e}")
        return _default_analysis(current_price, price_history)


def _analyze_with_gemini(symbol: str, current_price: float, price_history: list, company_name: str, api_key: str) -> Dict[str, Any]:
    """Gemini AI fallback when Groq is not available"""
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = f"""คุณเป็นนักวิเคราะห์หุ้นมืออาชีพ วิเคราะห์หุ้นนี้:

หุ้น: {symbol} ({company_name})
ราคาปัจจุบัน: ${current_price}
ข้อมูลราคาย้อนหลัง: {json.dumps(price_history[-10:] if price_history else [], indent=2)}

ตอบเป็น JSON (ไม่มี markdown):
{{"recommendation": "BUY/SELL/HOLD", "entry_price": number, "take_profit": number, "stop_loss": number, "analysis": "คำอธิบายภาษาไทย", "confidence": 0-100}}"""

        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
        
        result = json.loads(result_text)
        return {
            "recommendation": result.get("recommendation", "HOLD"),
            "entry_price": float(result.get("entry_price", current_price)),
            "take_profit": float(result.get("take_profit", current_price * 1.10)),
            "stop_loss": float(result.get("stop_loss", current_price * 0.95)),
            "analysis": result.get("analysis", "ไม่มีข้อมูลเพิ่มเติม"),
            "confidence": float(result.get("confidence", 50))
        }
    except Exception as e:
        print(f"❌ Gemini fallback error: {e}")
        return _default_analysis(current_price, price_history)


def _default_analysis(current_price: float, price_history: list = None) -> Dict[str, Any]:
    """
    Technical Analysis เมื่อ AI ไม่พร้อมใช้งาน
    ใช้ RSI, Moving Average, Bollinger Bands, MACD
    """
    # ถ้าไม่มี price history ให้ใช้สูตรเดิม
    if not price_history or len(price_history) < 14:
        return {
            "recommendation": "HOLD",
            "entry_price": round(current_price * 0.97, 2),
            "take_profit": round(current_price * 1.10, 2),
            "stop_loss": round(current_price * 0.93, 2),
            "analysis": "ข้อมูลไม่เพียงพอสำหรับวิเคราะห์",
            "confidence": 20
        }
    
    # Extract close prices
    closes = [p.get("close", p.get("price", current_price)) for p in price_history]
    
    # === Calculate Technical Indicators ===
    
    # 1. RSI (Relative Strength Index) - 14 periods
    rsi = _calculate_rsi(closes, 14)
    
    # 2. Moving Averages
    sma_10 = sum(closes[-10:]) / 10 if len(closes) >= 10 else current_price
    sma_20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else current_price
    
    # 3. Bollinger Bands (20 periods, 2 std dev)
    bb_upper, bb_middle, bb_lower = _calculate_bollinger_bands(closes, 20, 2)
    
    # 4. MACD (12, 26, 9)
    macd_line, signal_line, macd_histogram = _calculate_macd(closes)
    
    # === Analyze Signals ===
    signals = []
    buy_score = 0
    sell_score = 0
    
    # RSI Analysis
    if rsi < 30:
        signals.append("RSI Oversold")
        buy_score += 2
    elif rsi > 70:
        signals.append("RSI Overbought")
        sell_score += 2
    elif rsi < 50:
        buy_score += 1
    else:
        sell_score += 1
    
    # Moving Average Crossover
    if sma_10 > sma_20:
        signals.append("MA Golden Cross")
        buy_score += 1
    else:
        signals.append("MA Death Cross")
        sell_score += 1
    
    # Bollinger Bands
    if current_price < bb_lower:
        signals.append("Price < BB Lower")
        buy_score += 2
    elif current_price > bb_upper:
        signals.append("Price > BB Upper")
        sell_score += 2
    
    # MACD
    if macd_histogram > 0 and macd_line > signal_line:
        signals.append("MACD Bullish")
        buy_score += 1
    elif macd_histogram < 0 and macd_line < signal_line:
        signals.append("MACD Bearish")
        sell_score += 1
    
    # === Determine Recommendation ===
    total_score = buy_score - sell_score
    
    if total_score >= 3:
        recommendation = "BUY"
        confidence = min(70 + total_score * 5, 85)
    elif total_score <= -3:
        recommendation = "SELL"
        confidence = min(70 + abs(total_score) * 5, 85)
    else:
        recommendation = "HOLD"
        confidence = 50
    
    # === Calculate Entry/TP/SL based on analysis ===
    volatility = (bb_upper - bb_lower) / bb_middle if bb_middle > 0 else 0.05
    
    if recommendation == "BUY":
        entry_price = min(current_price, bb_lower * 1.01)  # Near lower band
        take_profit = bb_upper * 0.98  # Near upper band
        stop_loss = entry_price * (1 - volatility)  # Based on volatility
    elif recommendation == "SELL":
        entry_price = current_price  # Sell now
        take_profit = bb_lower * 1.02
        stop_loss = bb_upper * 1.02
    else:
        entry_price = bb_middle * 0.98
        take_profit = bb_upper * 0.95
        stop_loss = bb_lower * 0.98
    
    # Build analysis text
    analysis_text = f"RSI:{rsi:.0f} | {', '.join(signals[:2])}"
    
    return {
        "recommendation": recommendation,
        "entry_price": round(entry_price, 2),
        "take_profit": round(take_profit, 2),
        "stop_loss": round(stop_loss, 2),
        "analysis": analysis_text,
        "confidence": confidence
    }


def _calculate_rsi(prices: list, period: int = 14) -> float:
    """คำนวณ RSI (Relative Strength Index)"""
    if len(prices) < period + 1:
        return 50.0  # Neutral
    
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas[-period:]]
    losses = [-d if d < 0 else 0 for d in deltas[-period:]]
    
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def _calculate_bollinger_bands(prices: list, period: int = 20, std_dev: int = 2) -> tuple:
    """คำนวณ Bollinger Bands"""
    if len(prices) < period:
        avg = sum(prices) / len(prices)
        return avg * 1.05, avg, avg * 0.95
    
    recent = prices[-period:]
    middle = sum(recent) / period
    
    # Calculate standard deviation
    variance = sum((p - middle) ** 2 for p in recent) / period
    std = variance ** 0.5
    
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    
    return upper, middle, lower


def _calculate_macd(prices: list, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
    """คำนวณ MACD"""
    if len(prices) < slow:
        return 0, 0, 0
    
    # Calculate EMAs
    ema_fast = _calculate_ema(prices, fast)
    ema_slow = _calculate_ema(prices, slow)
    
    macd_line = ema_fast - ema_slow
    
    # Simplified signal line (would need historical MACD values for proper EMA)
    signal_line = macd_line * 0.9  # Approximation
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def _calculate_ema(prices: list, period: int) -> float:
    """คำนวณ Exponential Moving Average"""
    if len(prices) < period:
        return sum(prices) / len(prices)
    
    multiplier = 2 / (period + 1)
    ema = sum(prices[:period]) / period  # Start with SMA
    
    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema
    
    return ema


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
