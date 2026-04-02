from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AgentConfigResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    criteria: dict
    max_score: float
    created_at: datetime

    class Config:
        from_attributes = True
