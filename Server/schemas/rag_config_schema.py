from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class RAGConfigCreate(BaseModel):
    """Schema để tạo RAG configuration mới"""
    config_name: str
    llm_id: int
    embedding_model_id: int
    chunk_size: int = 1000
    chunk_overlap: int = 200
    search_type: str = "similarity"
    k_value: int = 3
    prompt_template: str


class RAGConfigUpdate(BaseModel):
    """Schema để update RAG configuration"""
    config_name: Optional[str] = None
    llm_id: Optional[int] = None
    embedding_model_id: Optional[int] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    search_type: Optional[str] = None
    k_value: Optional[int] = None
    prompt_template: Optional[str] = None


class RAGConfigOut(BaseModel):
    """Schema để trả về RAG configuration"""
    id: int
    config_name: str
    llm_id: int
    embedding_model_id: int
    chunk_size: int
    chunk_overlap: int
    search_type: str
    k_value: int
    prompt_template: str
    created_at: datetime

    class Config:
        from_attributes = True  # Thay orm_mode = True (deprecated)
