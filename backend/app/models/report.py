from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class ReportStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for single-user mode
    title = Column(String(500), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # Path in S3/MinIO
    content_text = Column(Text, nullable=True)  # Extracted text content
    status = Column(Enum(ReportStatus), default=ReportStatus.UPLOADED)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Metadata extracted from first page
    kandidater = Column(JSON, nullable=True)  # List of candidate numbers
    oppgave = Column(String(255), nullable=True)  # Assignment name
    innleveringsdato = Column(Date, nullable=True)  # Submission date

    # Anonymization
    anonymized_file_path = Column(String(500), nullable=True)  # Path to anonymized PDF
    mapping_file_path = Column(String(500), nullable=True)  # Path to mapping file
    candidate_mappings = Column(JSON, nullable=True)  # [{"name": "...", "initials": "...", "candidate_number": "..."}]

    # Relationships
    user = relationship("User", back_populates="reports")
    evaluations = relationship("Evaluation", back_populates="report", cascade="all, delete-orphan")
