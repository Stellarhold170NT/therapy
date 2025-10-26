import requests
from typing import Dict, Any


class AuthService:
    """Service xử lý authentication với Server API"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def register(self, username: str, password: str, role: str = "user") -> Dict[str, Any]:
        """Đăng ký user mới"""
        try:
            response = requests.post(
                f"{self.base_url}/users/register",
                json={
                    "username": username,
                    "password": password,
                    "role": role
                }
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """Đăng nhập và lấy JWT token"""
        try:
            response = requests.post(
                f"{self.base_url}/users/login",
                json={
                    "username": username,
                    "password": password
                }
            )
            response.raise_for_status()
            data = response.json()
            return {
                "success": True,
                "token": data["access_token"],
                "username": data.get("username", username),
                "role": data.get("role", "user")
            }
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}

    def verify_token(self, token: str) -> bool:
        """Verify token có hợp lệ không"""
        try:
            response = requests.get(
                f"{self.base_url}/users/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            return response.status_code == 200
        except:
            return False

    def list_users(self, token: str) -> Dict[str, Any]:
        """Lấy danh sách tất cả users"""
        try:
            response = requests.get(
                f"{self.base_url}/users/",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}

    def register_user(self, username: str, password: str, role: str, token: str) -> Dict[str, Any]:
        """Đăng ký user mới (từ admin)"""
        try:
            response = requests.post(
                f"{self.base_url}/users/register",
                json={
                    "username": username,
                    "password": password,
                    "role": role
                },
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
