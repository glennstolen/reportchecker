from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ReportCreate(BaseModel):
    title: str


class ReportResponse(BaseModel):
    id: int
    title: str
    filename: str
    status: str
    content_text: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    id: int
    title: str
    filename: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
