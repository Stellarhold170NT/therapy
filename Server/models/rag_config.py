from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from database.connection import Base


class RAGConfig(Base):
    __tablename__ = "ragconfig"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    config_name = Column(String(255), nullable=False)
    llm_id = Column(Integer, nullable=False)
    embedding_model_id = Column(Integer, nullable=False)
    chunk_size = Column(Integer, nullable=False, default=1000)
    chunk_overlap = Column(Integer, nullable=False, default=200)
    search_type = Column(String(50), nullable=False, default="similarity")
    k_value = Column(Integer, nullable=False, default=3)
    prompt_template = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
