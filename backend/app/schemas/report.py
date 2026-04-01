from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional


class ReportCreate(BaseModel):
    title: str


class ReportResponse(BaseModel):
    id: int
    title: str
    filename: str
    status: str
    content_text: Optional[str] = None
    kandidater: Optional[list[int]] = None
    oppgave: Optional[str] = None
    innleveringsdato: Optional[date] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    id: int
    title: str
    filename: str
    status: str
    created_at: datetime
    kandidater: Optional[list[int]] = None
    oppgave: Optional[str] = None
    innleveringsdato: Optional[date] = None
    latest_score: Optional[float] = None
    latest_max_score: Optional[float] = None

    class Config:
        from_attributes = True
