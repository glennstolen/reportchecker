from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.agent_configuration import AgentConfiguration
from app.schemas.agent import AgentConfigResponse

router = APIRouter()


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
