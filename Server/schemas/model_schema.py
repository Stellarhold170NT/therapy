from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ModelCreate(BaseModel):
    model_name: str
    model_type: str  # "llm" or "embedding"
    provider: str


class ModelUpdate(BaseModel):
    model_name: Optional[str] = None
    model_type: Optional[str] = None
    provider: Optional[str] = None


class ModelOut(BaseModel):
    id: int
    model_name: str
    model_type: str
    provider: str
    added_at: datetime

    class Config:
        from_attributes = True
