from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.agent_configuration import AgentConfiguration
from app.schemas.agent import AgentConfigCreate, AgentConfigUpdate, AgentConfigResponse

router = APIRouter()


@router.post("", response_model=AgentConfigResponse)
def create_agent(agent: AgentConfigCreate, db: Session = Depends(get_db)):
    """Create a new agent configuration."""
    db_agent = AgentConfiguration(
        name=agent.name,
        description=agent.description,
        criteria=agent.criteria.model_dump(),
        max_score=agent.max_score,
        prompt_template=agent.prompt_template,
        is_template=False,
    )
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent


@router.get("", response_model=list[AgentConfigResponse])
def list_agents(include_templates: bool = True, db: Session = Depends(get_db)):
    """List all agent configurations."""
    query = db.query(AgentConfiguration)
    if not include_templates:
        query = query.filter(AgentConfiguration.is_template == False)
    agents = query.order_by(AgentConfiguration.created_at.desc()).all()
    return agents


@router.get("/templates", response_model=list[AgentConfigResponse])
def list_templates(db: Session = Depends(get_db)):
    """List only template agent configurations."""
    templates = (
        db.query(AgentConfiguration)
        .filter(AgentConfiguration.is_template == True)
        .all()
    )
    return templates


@router.get("/{agent_id}", response_model=AgentConfigResponse)
def get_agent(agent_id: int, db: Session = Depends(get_db)):
    """Get a specific agent configuration."""
    agent = db.query(AgentConfiguration).filter(AgentConfiguration.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent configuration not found")
    return agent


@router.put("/{agent_id}", response_model=AgentConfigResponse)
def update_agent(agent_id: int, update: AgentConfigUpdate, db: Session = Depends(get_db)):
    """Update an agent configuration."""
    agent = db.query(AgentConfiguration).filter(AgentConfiguration.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent configuration not found")

    if update.name is not None:
        agent.name = update.name
    if update.description is not None:
        agent.description = update.description
    if update.criteria is not None:
        agent.criteria = update.criteria.model_dump()
    if update.max_score is not None:
        agent.max_score = update.max_score
    if update.prompt_template is not None:
        agent.prompt_template = update.prompt_template

    db.commit()
    db.refresh(agent)
    return agent


@router.delete("/{agent_id}")
def delete_agent(agent_id: int, db: Session = Depends(get_db)):
    """Delete an agent configuration."""
    agent = db.query(AgentConfiguration).filter(AgentConfiguration.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent configuration not found")

    if agent.is_template:
        raise HTTPException(status_code=400, detail="Cannot delete template agents")

    db.delete(agent)
    db.commit()
    return {"message": "Agent configuration deleted"}
