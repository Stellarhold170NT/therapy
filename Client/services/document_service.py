import requests
from typing import Dict, Any, Optional


class DocumentService:
    """Service xử lý Document Management với Server API"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def list_documents(self, token: str, search: Optional[str] = None) -> Dict[str, Any]:
        """Lấy danh sách documents"""
        try:
            params = {"search": search} if search else {}
            response = requests.get(
                f"{self.base_url}/rag-configs/documents/",
                headers={"Authorization": f"Bearer {token}"},
                params=params
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}

    def upload_document(
        self,
        file_data: bytes,
        filename: str,
        title: Optional[str],
        author: Optional[str],
        total_pages: Optional[int],
        creation_date: Optional[str],
        token: str
    ) -> Dict[str, Any]:
        """Upload document lên server"""
        try:
            files = {"file": (filename, file_data, "application/pdf")}
            data = {}
            if title:
                data["title"] = title
            if author:
                data["author"] = author
            if total_pages:
                data["total_pages"] = total_pages
            if creation_date:
                data["creation_date"] = creation_date

            response = requests.post(
                f"{self.base_url}/rag-configs/documents/upload",
                files=files,
                data=data,
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}

    def delete_document(self, doc_id: int, token: str) -> Dict[str, Any]:
        """Xóa document"""
        try:
            response = requests.delete(
                f"{self.base_url}/rag-configs/documents/{doc_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}

    def get_document(self, doc_id: int, token: str) -> Dict[str, Any]:
        """Lấy chi tiết document"""
        try:
            response = requests.get(
                f"{self.base_url}/rag-configs/documents/{doc_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
