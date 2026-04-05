from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any


class EvaluationCreate(BaseModel):
    report_id: int


class AgentResultResponse(BaseModel):
    id: int
    agent_config_id: int
    agent_name: str
    score: Optional[float]
    max_score: Optional[float]
    feedback: Optional[str]
    details: Optional[Any]  # Can be list or dict
    status: str
    prompt_used: Optional[str] = None
    raw_response: Optional[str] = None

    class Config:
        from_attributes = True


class EvaluationResponse(BaseModel):
    id: int
    report_id: int
    status: str
    total_score: Optional[float]
    max_possible_score: Optional[float]
    summary: Optional[str]
    agent_results: list[AgentResultResponse] = []
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True
