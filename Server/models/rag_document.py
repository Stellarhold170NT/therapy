from sqlalchemy import Column, Integer, ForeignKey, DateTime
from datetime import datetime
from database.connection import Base


class RagDocument(Base):
    """Model cho relationship giữa RAG Config và Document"""
    __tablename__ = "rag_document"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    rag_config_id = Column(Integer, ForeignKey("ragconfig.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(Integer, ForeignKey("document.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<RagDocument(id={self.id}, rag_config_id={self.rag_config_id}, document_id={self.document_id})>"
