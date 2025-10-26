import requests
from typing import Dict, Any, List


class RAGService:
    """Service xử lý RAG Configuration với Server API"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def create_config(self, config_data: Dict[str, Any], token: str) -> Dict[str, Any]:
        """Tạo RAG configuration mới"""
        try:
            response = requests.post(
                f"{self.base_url}/rag-configs/",
                json=config_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}

    def list_configs(self, token: str) -> Dict[str, Any]:
        """Lấy danh sách RAG configurations"""
        try:
            response = requests.get(
                f"{self.base_url}/rag-configs/",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}

    def delete_config(self, config_id: int, token: str) -> Dict[str, Any]:
        """Xóa RAG configuration"""
        try:
            response = requests.delete(
                f"{self.base_url}/rag-configs/{config_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}

    def add_documents_to_config(self, config_id: int, document_ids: List[int], token: str) -> Dict[str, Any]:
        """Thêm documents vào RAG configuration"""
        try:
            response = requests.post(
                f"{self.base_url}/rag-configs/{config_id}/documents",
                json=document_ids,
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}

    def get_config_documents(self, config_id: int, token: str) -> Dict[str, Any]:
        """Lấy danh sách documents của RAG configuration"""
        try:
            response = requests.get(
                f"{self.base_url}/rag-configs/{config_id}/documents",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
