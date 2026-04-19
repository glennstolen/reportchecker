from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class EvaluationStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    status = Column(Enum(EvaluationStatus), default=EvaluationStatus.PENDING)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Aggregated results
    total_score = Column(Float, nullable=True)
    max_possible_score = Column(Float, nullable=True)
    summary = Column(Text, nullable=True)
    instructor_total_score = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    report = relationship("Report", back_populates="evaluations")
    user = relationship("User", back_populates="evaluations")
    agent_results = relationship("AgentResult", back_populates="evaluation", cascade="all, delete-orphan")


class AgentResult(Base):
    __tablename__ = "agent_results"

    id = Column(Integer, primary_key=True, index=True)
    evaluation_id = Column(Integer, ForeignKey("evaluations.id"), nullable=False)
    agent_config_id = Column(Integer, ForeignKey("agent_configurations.id"), nullable=False)

    score = Column(Float, nullable=True)
    max_score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    instructor_score = Column(Float, nullable=True)
    instructor_comment = Column(Text, nullable=True)

    # Detailed results per criterion
    details = Column(JSON, nullable=True)

    # Store prompt and response for transparency
    prompt_used = Column(Text, nullable=True)
    raw_response = Column(Text, nullable=True)

    # Status for this specific agent
    status = Column(Enum(EvaluationStatus), default=EvaluationStatus.PENDING)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    evaluation = relationship("Evaluation", back_populates="agent_results")
    agent_configuration = relationship("AgentConfiguration", back_populates="agent_results")
