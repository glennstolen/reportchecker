from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class AgentConfiguration(Base):
    __tablename__ = "agent_configurations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for templates
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Criteria as JSON - flexible structure for different check types
    # Format: {"checkItems": [...], "scoringRubric": "..."}
    criteria = Column(JSON, nullable=False, default=dict)

    # max_score doubles as the percentage weight in the total score (all agents sum to 100)
    max_score = Column(Float, default=10.0)

    # Custom prompt template (optional - uses default if not set)
    prompt_template = Column(Text, nullable=True)

    # Is this a system template available to all users?
    is_template = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="agent_configurations")
    agent_results = relationship("AgentResult", back_populates="agent_configuration")
