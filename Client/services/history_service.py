import requests
from typing import List, Dict, Any, Optional


class HistoryService:
    """Service xử lý lịch sử chat với Server API"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def create_chat_session(
        self,
        session_id: str,
        session_name: Optional[str],
        token: str
    ) -> Dict[str, Any]:
        """Tạo chat session mới với UUID"""
        try:
            response = requests.post(
                f"{self.base_url}/history/chat-sessions/",
                json={
                    "session_id": session_id,
                    "session_name": session_name
                },
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_chat_sessions(self, token: str) -> Dict[str, Any]:
        """Lấy danh sách tất cả chat sessions của user"""
        try:
            response = requests.get(
                f"{self.base_url}/history/chat-sessions/",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_chat_session(self, session_id: str, token: str) -> Dict[str, Any]:
        """Lấy thông tin chi tiết của một chat session"""
        try:
            response = requests.get(
                f"{self.base_url}/history/chat-sessions/{session_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def update_chat_session(
        self,
        session_id: str,
        session_name: str,
        token: str
    ) -> Dict[str, Any]:
        """Cập nhật tên chat session"""
        try:
            response = requests.put(
                f"{self.base_url}/history/chat-sessions/{session_id}",
                json={"session_name": session_name},
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def delete_chat_session(self, session_id: str, token: str) -> Dict[str, Any]:
        """Xóa chat session"""
        try:
            response = requests.delete(
                f"{self.base_url}/history/chat-sessions/{session_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def touch_chat_session(self, session_id: str, token: str) -> Dict[str, Any]:
        """Cập nhật timestamp của chat session (khi có activity mới)"""
        try:
            response = requests.post(
                f"{self.base_url}/history/chat-sessions/{session_id}/touch",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except Exception as e:
            return {"success": False, "message": str(e)}
