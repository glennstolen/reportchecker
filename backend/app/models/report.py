from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
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

    # Relationships
    user = relationship("User", back_populates="reports")
    evaluations = relationship("Evaluation", back_populates="report")
