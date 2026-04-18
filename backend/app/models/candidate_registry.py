from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.core.database import Base


class CandidateRegistry(Base):
    __tablename__ = "candidate_registry"

    id = Column(Integer, primary_key=True)
    name_normalized = Column(String(500), nullable=False, unique=True, index=True)
    candidate_number = Column(String(6), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
