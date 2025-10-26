from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database.connection import Base


class Model(Base):
    __tablename__ = "model"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    model_name = Column(String(100), nullable=False, unique=True)
    model_type = Column(String(20), nullable=False)  # 'llm' or 'embedding'
    provider = Column(String(100), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Model(id={self.id}, name={self.model_name}, type={self.model_type}, provider={self.provider})>"
