from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class CriterionItem(BaseModel):
    id: str
    label: str
    weight: float = 1.0
    description: Optional[str] = None


class CriteriaSchema(BaseModel):
    checkItems: list[CriterionItem] = []
    scoringRubric: Optional[str] = None


class AgentConfigCreate(BaseModel):
    name: str
    description: Optional[str] = None
    criteria: CriteriaSchema
    max_score: float = 10.0
    prompt_template: Optional[str] = None


class AgentConfigUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    criteria: Optional[CriteriaSchema] = None
    max_score: Optional[float] = None
    prompt_template: Optional[str] = None


class AgentConfigResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    criteria: dict
    max_score: float
    prompt_template: Optional[str]
    is_template: bool
    created_at: datetime

    class Config:
        from_attributes = True
