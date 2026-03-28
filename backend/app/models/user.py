from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(50), default="lecturer")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    reports = relationship("Report", back_populates="user")
    agent_configurations = relationship("AgentConfiguration", back_populates="user")
    evaluations = relationship("Evaluation", back_populates="user")
