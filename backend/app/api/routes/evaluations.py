from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.evaluation import Evaluation, EvaluationStatus
from app.models.report import Report
from app.models.agent_configuration import AgentConfiguration
from app.schemas.evaluation import EvaluationCreate, EvaluationResponse, AgentResultResponse
from app.services.evaluation_service import EvaluationService

router = APIRouter()


@router.post("", response_model=EvaluationResponse)
async def create_evaluation(
    evaluation: EvaluationCreate,
    db: Session = Depends(get_db),
):
    """Start a new evaluation of a report with selected agents."""
    # Validate report exists
    report = db.query(Report).filter(Report.id == evaluation.report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if not report.content_text:
        raise HTTPException(
            status_code=400,
            detail="Report has not been processed yet. Please wait for processing to complete.",
        )

    # Validate all agent configs exist
    agents = (
        db.query(AgentConfiguration)
        .filter(AgentConfiguration.id.in_(evaluation.agent_config_ids))
        .all()
    )
    if len(agents) != len(evaluation.agent_config_ids):
        raise HTTPException(status_code=404, detail="One or more agent configurations not found")

    service = EvaluationService(db)
    db_evaluation = await service.create_and_run_evaluation(report, agents)

    return _build_evaluation_response(db_evaluation)


@router.get("/{evaluation_id}", response_model=EvaluationResponse)
def get_evaluation(evaluation_id: int, db: Session = Depends(get_db)):
    """Get evaluation results."""
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    return _build_evaluation_response(evaluation)


@router.get("/{evaluation_id}/status")
def get_evaluation_status(evaluation_id: int, db: Session = Depends(get_db)):
    """Get evaluation status (for polling)."""
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    completed_agents = sum(
        1 for r in evaluation.agent_results if r.status == EvaluationStatus.COMPLETED
    )
    total_agents = len(evaluation.agent_results)

    return {
        "status": evaluation.status,
        "progress": {
            "completed": completed_agents,
            "total": total_agents,
        },
    }


@router.get("/report/{report_id}", response_model=list[EvaluationResponse])
def list_evaluations_for_report(report_id: int, db: Session = Depends(get_db)):
    """List all evaluations for a specific report."""
    evaluations = (
        db.query(Evaluation)
        .filter(Evaluation.report_id == report_id)
        .order_by(Evaluation.created_at.desc())
        .all()
    )
    return [_build_evaluation_response(e) for e in evaluations]


def _build_evaluation_response(evaluation: Evaluation) -> EvaluationResponse:
    """Build response with agent results including agent names."""
    agent_results = []
    for result in evaluation.agent_results:
        agent_results.append(
            AgentResultResponse(
                id=result.id,
                agent_config_id=result.agent_config_id,
                agent_name=result.agent_configuration.name,
                score=result.score,
                max_score=result.max_score,
                feedback=result.feedback,
                details=result.details,
                status=result.status.value,
            )
        )

    return EvaluationResponse(
        id=evaluation.id,
        report_id=evaluation.report_id,
        status=evaluation.status.value,
        total_score=evaluation.total_score,
        max_possible_score=evaluation.max_possible_score,
        summary=evaluation.summary,
        agent_results=agent_results,
        created_at=evaluation.created_at,
        started_at=evaluation.started_at,
        completed_at=evaluation.completed_at,
    )
