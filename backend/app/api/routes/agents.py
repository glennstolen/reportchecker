from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.agent_configuration import AgentConfiguration
from app.schemas.agent import AgentConfigResponse, AgentConfigUpdate

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[AgentConfigResponse])
def list_agents(db: Session = Depends(get_db)):
    """List all agent configurations (all are templates)."""
    agents = db.query(AgentConfiguration).order_by(AgentConfiguration.id).all()
    return agents


@router.get("/{agent_id}", response_model=AgentConfigResponse)
def get_agent(agent_id: int, db: Session = Depends(get_db)):
    """Get a specific agent configuration."""
    agent = db.query(AgentConfiguration).filter(AgentConfiguration.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent configuration not found")
    return agent


@router.put("/{agent_id}", response_model=AgentConfigResponse)
def update_agent(agent_id: int, payload: AgentConfigUpdate, db: Session = Depends(get_db)):
    """Update an agent configuration."""
    agent = db.query(AgentConfiguration).filter(AgentConfiguration.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent configuration not found")
    agent.name = payload.name
    agent.description = payload.description
    agent.max_score = payload.max_score
    agent.criteria = payload.criteria
    agent.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(agent)
    return agent
