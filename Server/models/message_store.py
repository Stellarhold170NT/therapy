from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database.connection import Base

class MessageStore(Base):
    __tablename__ = "message_store"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100))
    role = Column(String(20))  # 'user' / 'assistant'
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", primaryjoin="MessageStore.session_id==ChatSession.session_id", viewonly=True)
