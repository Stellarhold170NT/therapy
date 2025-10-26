from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from datetime import datetime
from database.connection import Base


class Document(Base):
    """Model cho document/tài liệu PDF"""
    __tablename__ = "document"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False, unique=True)
    title = Column(String(255), nullable=True)
    author = Column(String(255), nullable=True)
    total_pages = Column(Integer, nullable=True)
    creation_date = Column(DateTime, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Document(id={self.id}, file_name='{self.file_name}', title='{self.title}')>"
