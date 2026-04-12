from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional


class ReportCreate(BaseModel):
    title: str


class AuthorInput(BaseModel):
    name: str
    initials: str


class AuthorMappingResponse(BaseModel):
    name: str
    initials: str
    candidate_number: str


class AnonymizeRequest(BaseModel):
    authors: list[AuthorInput]
    pages_to_remove: list[int]  # 0-indexed page numbers
    medforfatterbidrag: Optional[dict[str, list[str]]] = None  # section -> list of initials
    ki_brukt: bool = False
    title: Optional[str] = None  # Report title for cover page
    dato: Optional[str] = None  # Date for cover page (DD.MM.YYYY)
    oppgave: Optional[str] = None  # Assignment name for cover page


class AnonymizeResponse(BaseModel):
    anonymized_file_path: str
    mapping_file_path: str
    mappings: list[AuthorMappingResponse]
    message: str


class ReportResponse(BaseModel):
    id: int
    title: str
    filename: str
    status: str
    content_text: Optional[str] = None
    kandidater: Optional[list[int]] = None
    oppgave: Optional[str] = None
    innleveringsdato: Optional[date] = None
    anonymized_file_path: Optional[str] = None
    mapping_file_path: Optional[str] = None
    candidate_mappings: Optional[list[dict]] = None
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
    is_anonymized: bool = False
    candidate_mappings: Optional[list[dict]] = None

    class Config:
        from_attributes = True
