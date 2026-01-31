"""
Firebase Service Module - src/firebase_service.py
==================================================
จัดการ Firestore Database สำหรับเก็บ Watchlist และ Alerts

Collections:
- users/{userId}/watchlist - หุ้นที่ติดตาม
- users/{userId}/alerts - การแจ้งเตือน
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

# Firebase Admin SDK
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
_db = None

def _get_db():
    """Get Firestore database instance (lazy initialization)"""
    global _db
    
    if _db is not None:
        return _db
    
    # Try to initialize Firebase
    try:
        # Check if already initialized
        firebase_admin.get_app()
    except ValueError:
        # Not initialized - do it now
        cred_json = os.getenv("FIREBASE_CREDENTIALS")
        
        if cred_json:
            # Parse JSON string from environment variable
            cred_dict = json.loads(cred_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        else:
            # Try to use default credentials or local file
            cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "firebase-credentials.json")
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            else:
                print("⚠️ Firebase credentials not found. Using mock mode.")
                return None
    
    _db = firestore.client()
    return _db


# ============================================
# Watchlist Functions
# ============================================

def add_to_watchlist(user_id: str, symbol: str, current_price: float) -> bool:
    """
    เพิ่มหุ้นใน Watchlist ของผู้ใช้
    """
    db = _get_db()
    if not db:
        print(f"[MOCK] Add {symbol} to watchlist for user {user_id}")
        return True
    
    try:
        doc_ref = db.collection("users").document(user_id).collection("watchlist").document(symbol)
        doc_ref.set({
            "symbol": symbol,
            "added_price": current_price,
            "added_at": datetime.now(),
            "updated_at": datetime.now()
        })
        return True
    except Exception as e:
        print(f"❌ Firebase Error (add_to_watchlist): {e}")
        return False


def remove_from_watchlist(user_id: str, symbol: str) -> bool:
    """
    ลบหุ้นออกจาก Watchlist
    """
    db = _get_db()
    if not db:
        print(f"[MOCK] Remove {symbol} from watchlist for user {user_id}")
        return True
    
    try:
        db.collection("users").document(user_id).collection("watchlist").document(symbol).delete()
        return True
    except Exception as e:
        print(f"❌ Firebase Error (remove_from_watchlist): {e}")
        return False


def get_watchlist(user_id: str) -> List[Dict[str, Any]]:
    """
    ดึงรายการ Watchlist ของผู้ใช้
    """
    db = _get_db()
    if not db:
        print(f"[MOCK] Get watchlist for user {user_id}")
        return []
    
    try:
        docs = db.collection("users").document(user_id).collection("watchlist").stream()
        watchlist = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            watchlist.append(data)
        return watchlist
    except Exception as e:
        print(f"❌ Firebase Error (get_watchlist): {e}")
        return []


def get_all_watchlists() -> List[Dict[str, Any]]:
    """
    ดึง Watchlist ของทุก User (สำหรับ daily summary)
    Returns: [{"user_id": "xxx", "stocks": [{"symbol": "AAPL", ...}]}]
    """
    db = _get_db()
    if not db:
        return []
    
    try:
        all_watchlists = []
        users_ref = db.collection("users").stream()
        
        for user_doc in users_ref:
            user_id = user_doc.id
            watchlist_docs = db.collection("users").document(user_id).collection("watchlist").stream()
            
            stocks = []
            for watch_doc in watchlist_docs:
                data = watch_doc.to_dict()
                data["symbol"] = watch_doc.id
                stocks.append(data)
            
            if stocks:  # Only include users with watchlist items
                all_watchlists.append({
                    "user_id": user_id,
                    "stocks": stocks
                })
        
        return all_watchlists
    except Exception as e:
        print(f"❌ Firebase Error (get_all_watchlists): {e}")
        return []


# ============================================
# Alert Functions
# ============================================

def add_alert(user_id: str, symbol: str, entry_price: float, take_profit: float, stop_loss: float) -> bool:
    """
    เพิ่มการแจ้งเตือนสำหรับหุ้น
    """
    db = _get_db()
    if not db:
        print(f"[MOCK] Add alert for {symbol}")
        return True
    
    try:
        doc_ref = db.collection("users").document(user_id).collection("alerts").document(symbol)
        doc_ref.set({
            "symbol": symbol,
            "entry_price": entry_price,
            "take_profit": take_profit,
            "stop_loss": stop_loss,
            "active": True,
            "created_at": datetime.now(),
            "triggered_at": None
        })
        return True
    except Exception as e:
        print(f"❌ Firebase Error (add_alert): {e}")
        return False


def get_user_alerts(user_id: str) -> List[Dict[str, Any]]:
    """
    ดึงรายการแจ้งเตือนของผู้ใช้
    """
    db = _get_db()
    if not db:
        return []
    
    try:
        docs = db.collection("users").document(user_id).collection("alerts").where("active", "==", True).stream()
        alerts = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            alerts.append(data)
        return alerts
    except Exception as e:
        print(f"❌ Firebase Error (get_user_alerts): {e}")
        return []


def get_all_active_alerts() -> List[Dict[str, Any]]:
    """
    ดึงการแจ้งเตือนทั้งหมดที่ยังเปิดใช้งาน (สำหรับ background job)
    """
    db = _get_db()
    if not db:
        return []
    
    try:
        all_alerts = []
        users_ref = db.collection("users").stream()
        
        for user_doc in users_ref:
            user_id = user_doc.id
            alerts = db.collection("users").document(user_id).collection("alerts").where("active", "==", True).stream()
            
            for alert_doc in alerts:
                data = alert_doc.to_dict()
                data["user_id"] = user_id
                data["alert_id"] = alert_doc.id
                all_alerts.append(data)
        
        return all_alerts
    except Exception as e:
        print(f"❌ Firebase Error (get_all_active_alerts): {e}")
        return []


def mark_alert_triggered(user_id: str, symbol: str) -> bool:
    """
    ทำเครื่องหมายว่าแจ้งเตือนแล้ว
    """
    db = _get_db()
    if not db:
        return True
    
    try:
        doc_ref = db.collection("users").document(user_id).collection("alerts").document(symbol)
        doc_ref.update({
            "active": False,
            "triggered_at": datetime.now()
        })
        return True
    except Exception as e:
        print(f"❌ Firebase Error (mark_alert_triggered): {e}")
        return False
