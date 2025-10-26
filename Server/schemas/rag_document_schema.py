from pydantic import BaseModel
from datetime import datetime
from typing import List


class RagDocumentCreate(BaseModel):
    """Schema để tạo rag_document association"""
    rag_config_id: int
    document_id: int


class RagDocumentBatchCreate(BaseModel):
    """Schema để tạo nhiều associations cùng lúc"""
    rag_config_id: int
    document_ids: List[int]


class RagDocumentOut(BaseModel):
    """Schema để trả về rag_document"""
    id: int
    rag_config_id: int
    document_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class RagDocumentWithDetails(BaseModel):
    """Schema trả về với thông tin chi tiết của document"""
    id: int
    rag_config_id: int
    document_id: int
    document_file_name: str
    document_title: str
    created_at: datetime

    class Config:
        from_attributes = True
