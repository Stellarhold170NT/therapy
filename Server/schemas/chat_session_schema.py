from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ChatSessionCreate(BaseModel):
    session_id: str  # UUID from client
    session_name: Optional[str] = None


class ChatSessionUpdate(BaseModel):
    session_name: Optional[str] = None


class ChatSessionOut(BaseModel):
    chat_id: int
    user_id: int
    session_id: str
    session_name: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
