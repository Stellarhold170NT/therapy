import requests
from typing import Generator, Dict, Any


class ChatService:
    """Service xử lý chat với Server API"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def send_message_stream(self, message: str, token: str, session_id: str = "default") -> Generator[str, None, None]:
        """Gửi message và nhận response streaming"""
        try:
            response = requests.post(
                f"{self.base_url}/chat/stream",
                json={"message": message, "session_id": session_id},
                headers={"Authorization": f"Bearer {token}"},
                stream=True
            )
            response.raise_for_status()

            for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                if chunk:
                    yield chunk
        except Exception as e:
            yield f"Error: {str(e)}"

    def get_debug_info(self, session_id: str, token: str) -> Dict[str, Any]:
        """Lấy debug info cho session"""
        try:
            response = requests.get(
                f"{self.base_url}/chat/debug/{session_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def test_search(self, query: str, k: int, token: str) -> Dict[str, Any]:
        """Test search trên vector store"""
        try:
            response = requests.post(
                f"{self.base_url}/chat/test-search",
                json={"query": query, "k": k},
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_vector_store_status(self, token: str) -> Dict[str, Any]:
        """Lấy trạng thái vector store"""
        try:
            response = requests.get(
                f"{self.base_url}/chat/vector-store-status",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"success": False, "message": str(e)}
