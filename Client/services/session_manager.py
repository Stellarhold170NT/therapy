import json
from typing import Optional, Dict, Any
from datetime import datetime


class SessionManager:
    """Quản lý JWT token - lưu vào cookies của browser"""

    def __init__(self, cookies_manager):
        self.cookies = cookies_manager
        self.storage_key = "therapy_session"

    def save_token(self, token: str, username: str, role: str = "user") -> None:
        """Lưu token vào cookies"""
        session_data = {
            "token": token,
            "username": username,
            "role": role,
            "timestamp": datetime.now().isoformat()
        }

        # Lưu vào cookies
        self.cookies[self.storage_key] = json.dumps(session_data)
        self.cookies.save()

    def load_token(self) -> Optional[Dict[str, Any]]:
        """Load token từ cookies"""
        try:
            session_json = self.cookies.get(self.storage_key)
            if session_json:
                return json.loads(session_json)
        except Exception:
            pass
        return None

    def clear_token(self) -> None:
        """Xóa token từ cookies"""
        if self.storage_key in self.cookies:
            del self.cookies[self.storage_key]
            self.cookies.save()
