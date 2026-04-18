from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional


class ReportCreate(BaseModel):
    title: str


class MappingRow(BaseModel):
    candidate_number: str
    name: str
    initials: str


class ExtractInfoAuthor(BaseModel):
    name: str
    initials: str
    candidate_number: str


class ExtractInfoResponse(BaseModel):
    authors: list[ExtractInfoAuthor]
    medforfatterbidrag: dict[str, list[str]]
    ki_brukt: bool
    total_pages: int
    suggested_pages_to_remove: list[int]
    title: str
    oppgave: Optional[str]
    dato: Optional[str]


class AuthorMappingResponse(BaseModel):
    name: str
    initials: str
    candidate_number: str


class AnonymizeRequest(BaseModel):
    mappings: list[MappingRow]
    pages_to_remove: list[int]  # 0-indexed page numbers
    medforfatterbidrag: Optional[dict[str, list[str]]] = None
    ki_brukt: bool = False
    title: Optional[str] = None
    dato: Optional[str] = None
    oppgave: Optional[str] = None


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
