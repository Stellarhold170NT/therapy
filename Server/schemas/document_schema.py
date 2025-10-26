from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DocumentCreate(BaseModel):
    """Schema để tạo document mới"""
    file_name: str
    file_path: str
    title: Optional[str] = None
    author: Optional[str] = None
    total_pages: Optional[int] = None
    creation_date: Optional[datetime] = None


class DocumentUpdate(BaseModel):
    """Schema để update document"""
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    total_pages: Optional[int] = None
    creation_date: Optional[datetime] = None


class DocumentOut(BaseModel):
    """Schema để trả về document"""
    id: int
    file_name: str
    file_path: str
    title: Optional[str] = None
    author: Optional[str] = None
    total_pages: Optional[int] = None
    creation_date: Optional[datetime] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True  # Thay orm_mode = True (deprecated)
