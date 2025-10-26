import requests
from typing import List, Dict, Optional


class ModelService:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def create_model(self, model_name: str, model_type: str, provider: str, token: str) -> Dict:
        """Tạo model mới"""
        try:
            response = requests.post(
                f"{self.base_url}/rag-configs/models/",
                json={
                    "model_name": model_name,
                    "model_type": model_type,
                    "provider": provider
                },
                headers={"Authorization": f"Bearer {token}"}
            )

            if response.status_code == 201:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "message": response.json().get("detail", "Failed to create model")}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def list_models(self, token: str, model_type: Optional[str] = None, provider: Optional[str] = None) -> Dict:
        """Lấy danh sách models, có thể filter theo model_type hoặc provider"""
        try:
            params = {}
            if model_type:
                params["model_type"] = model_type
            if provider:
                params["provider"] = provider

            response = requests.get(
                f"{self.base_url}/rag-configs/models/",
                params=params,
                headers={"Authorization": f"Bearer {token}"}
            )

            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "message": response.json().get("detail", "Failed to fetch models")}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_model(self, model_id: int, token: str) -> Dict:
        """Lấy thông tin model theo ID"""
        try:
            response = requests.get(
                f"{self.base_url}/rag-configs/models/{model_id}",
                headers={"Authorization": f"Bearer {token}"}
            )

            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "message": response.json().get("detail", "Model not found")}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def update_model(self, model_id: int, token: str, **kwargs) -> Dict:
        """Cập nhật thông tin model"""
        try:
            response = requests.put(
                f"{self.base_url}/rag-configs/models/{model_id}",
                json=kwargs,
                headers={"Authorization": f"Bearer {token}"}
            )

            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "message": response.json().get("detail", "Failed to update model")}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def delete_model(self, model_id: int, token: str) -> Dict:
        """Xóa model"""
        try:
            response = requests.delete(
                f"{self.base_url}/rag-configs/models/{model_id}",
                headers={"Authorization": f"Bearer {token}"}
            )

            if response.status_code == 200:
                return {"success": True, "message": "Model deleted successfully"}
            else:
                return {"success": False, "message": response.json().get("detail", "Failed to delete model")}
        except Exception as e:
            return {"success": False, "message": str(e)}
