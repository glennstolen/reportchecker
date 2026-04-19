import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.evaluation import Evaluation, AgentResult, EvaluationStatus
from app.models.report import Report
from app.models.agent_configuration import AgentConfiguration
from app.schemas.evaluation import EvaluationCreate, EvaluationResponse, AgentResultResponse, InstructorOverrideRequest
from app.services.evaluation_service import EvaluationService
from app.ai.claude_client import ClaudeClient
from app.ai.prompt_builder import build_evaluation_prompt, build_system_prompt, build_user_prompt, build_user_prompt_with_images
from app.ai.evaluation_orchestrator import EvaluationOrchestrator
from app.document_processing.text_extractor import extract_images_from_pdf
from app.core.storage import StorageClient

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/count")
def get_evaluation_count(db: Session = Depends(get_db)):
    """Get total number of evaluations."""
    count = db.query(Evaluation).count()
    return {"count": count}


@router.post("", response_model=EvaluationResponse)
async def create_evaluation(
    evaluation: EvaluationCreate,
    db: Session = Depends(get_db),
):
    """Start a new evaluation of a report using all agents."""
    report = db.query(Report).filter(Report.id == evaluation.report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if not report.content_text:
        raise HTTPException(
            status_code=400,
            detail="Report has not been processed yet. Please wait for processing to complete.",
        )

    query = db.query(AgentConfiguration)
    if evaluation.agent_ids:
        query = query.filter(AgentConfiguration.id.in_(evaluation.agent_ids))
    agents = query.order_by(AgentConfiguration.id).all()

    service = EvaluationService(db)
    db_evaluation = await service.create_and_run_evaluation(report, agents)

    return _build_evaluation_response(db_evaluation)


@router.post("/stream", response_class=StreamingResponse)
async def create_evaluation_stream(
    evaluation: EvaluationCreate,
    db: Session = Depends(get_db),
):
    """Start a new evaluation with streaming updates via SSE."""
    report = db.query(Report).filter(Report.id == evaluation.report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if not report.content_text:
        raise HTTPException(
            status_code=400,
            detail="Report has not been processed yet.",
        )

    query = db.query(AgentConfiguration)
    if evaluation.agent_ids:
        query = query.filter(AgentConfiguration.id.in_(evaluation.agent_ids))
    agents = query.order_by(AgentConfiguration.id).all()

    async def generate_stream():
        import asyncio

        # Create evaluation record
        db_evaluation = Evaluation(
            report_id=report.id,
            status=EvaluationStatus.RUNNING,
            started_at=datetime.utcnow(),
        )
        db.add(db_evaluation)
        db.commit()
        db.refresh(db_evaluation)

        # Create agent result records
        agent_results = {}
        for agent in agents:
            agent_result = AgentResult(
                evaluation_id=db_evaluation.id,
                agent_config_id=agent.id,
                max_score=agent.max_score,
                status=EvaluationStatus.PENDING,
            )
            db.add(agent_result)
            db.commit()
            db.refresh(agent_result)
            agent_results[agent.id] = agent_result

        # Send initial event with evaluation ID and all agents info
        agents_info = [
            {'id': a.id, 'name': a.name, 'description': a.description, 'max_score': a.max_score}
            for a in agents
        ]
        yield f"data: {json.dumps({'type': 'start', 'evaluation_id': db_evaluation.id, 'agents': agents_info})}\n\n"

        client = ClaudeClient()
        orchestrator = EvaluationOrchestrator()

        # Build system prompt once (contains report) - this will be cached by Anthropic
        system_prompt = build_system_prompt(report.content_text)

        # Extract images once for the whole evaluation (PDF only)
        _IMAGE_AGENTS = {"innhold", "figur"}
        report_images: list[dict] = []
        pdf_path = report.anonymized_file_path or report.file_path
        if pdf_path and pdf_path.lower().endswith(".pdf"):
            try:
                storage = StorageClient()
                pdf_bytes = storage.download_file(pdf_path)
                report_images = extract_images_from_pdf(pdf_bytes)
                if report_images:
                    print(f"Ekstraherte {len(report_images)} bilde(r) fra {pdf_path}")
            except Exception as e:
                print(f"Bildeekstraksjon feilet (fortsetter uten bilder): {e}")

        # Queue for collecting results from parallel tasks
        result_queue = asyncio.Queue()

        async def evaluate_agent(agent):
            """Evaluate a single agent and put result in queue."""
            agent_result = agent_results[agent.id]

            # Build user prompt (agent-specific criteria)
            user_prompt = build_user_prompt(agent)
            # Store full prompt for transparency
            agent_result.prompt_used = build_evaluation_prompt(report.content_text, agent)

            # Notify that agent started
            await result_queue.put({
                'type': 'agent_start',
                'agent_id': agent.id,
                'agent_name': agent.name,
            })

            # Build multimodal content for image-capable agents
            if report_images and any(kw in agent.name.lower() for kw in _IMAGE_AGENTS):
                import base64
                user_content: str | list = [
                    {"type": "text", "text": build_user_prompt_with_images(agent, len(report_images))},
                    *[
                        {"type": "image", "source": {"type": "base64", "media_type": img["media_type"], "data": base64.standard_b64encode(img["data"]).decode()}}
                        for img in report_images
                    ],
                ]
            else:
                user_content = user_prompt

            full_response = ""
            try:
                # Use cached evaluation - system prompt (report) is cached across agents
                async for token in client.evaluate_with_cache(system_prompt, user_content):
                    full_response += token

                # Parse the complete response
                agent_result.raw_response = full_response
                parsed = orchestrator._parse_response(full_response, agent.max_score)

                agent_result.score = parsed.get("score")
                agent_result.feedback = parsed.get("feedback")
                agent_result.details = parsed.get("details")
                agent_result.status = EvaluationStatus.COMPLETED

                await result_queue.put({
                    'type': 'agent_complete',
                    'agent_id': agent.id,
                    'score': agent_result.score,
                    'max_score': agent_result.max_score,
                    'feedback': agent_result.feedback,
                    'details': agent_result.details,
                })

            except Exception as e:
                import traceback
                error_detail = f"{type(e).__name__}: {str(e)}"
                print(f"Agent {agent.name} failed: {error_detail}")
                print(traceback.format_exc())

                agent_result.status = EvaluationStatus.ERROR
                agent_result.error_message = error_detail
                agent_result.raw_response = full_response

                await result_queue.put({
                    'type': 'agent_error',
                    'agent_id': agent.id,
                    'error': error_detail,
                })

        # Run agent evaluations sequentially to avoid rate limiting
        # (30,000 input tokens per minute limit)
        for agent in agents:
            # Start the evaluation
            task = asyncio.create_task(evaluate_agent(agent))

            # Wait for the agent_start event
            while True:
                try:
                    result = await asyncio.wait_for(result_queue.get(), timeout=0.1)
                    yield f"data: {json.dumps(result)}\n\n"
                    if result['type'] == 'agent_start':
                        break
                except asyncio.TimeoutError:
                    continue

            # Wait for this agent to complete before starting next
            await task

            # Get the completion/error result
            while True:
                try:
                    result = await asyncio.wait_for(result_queue.get(), timeout=0.1)
                    yield f"data: {json.dumps(result)}\n\n"
                    if result['type'] in ('agent_complete', 'agent_error'):
                        break
                except asyncio.TimeoutError:
                    continue

        # Commit all results to database
        db.commit()

        # Claude scores 0-100 per agent. Contribution = (score/100) * agent.max_score (percentage weight).
        total_score = sum(
            (r.score / 100) * r.max_score
            for r in agent_results.values()
            if r.score is not None
        )

        db_evaluation.total_score = round(total_score, 1)
        db_evaluation.max_possible_score = 100.0
        db_evaluation.status = EvaluationStatus.COMPLETED
        db_evaluation.completed_at = datetime.utcnow()

        # Generate summary
        service = EvaluationService(db)
        db_evaluation.summary = service._generate_summary(db_evaluation)
        db.commit()

        # Send complete event
        yield f"data: {json.dumps({'type': 'complete', 'evaluation_id': db_evaluation.id, 'total_score': db_evaluation.total_score, 'max_possible_score': db_evaluation.max_possible_score})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


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


@router.get("/{evaluation_id}", response_model=EvaluationResponse)
def get_evaluation(evaluation_id: int, db: Session = Depends(get_db)):
    """Get evaluation results."""
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    return _build_evaluation_response(evaluation)


@router.patch("/{evaluation_id}/agent-results/{agent_result_id}", response_model=EvaluationResponse)
def update_instructor_override(
    evaluation_id: int,
    agent_result_id: int,
    body: InstructorOverrideRequest,
    db: Session = Depends(get_db),
):
    """Set or clear instructor score/comment for a single agent result."""
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    agent_result = db.query(AgentResult).filter(
        AgentResult.id == agent_result_id,
        AgentResult.evaluation_id == evaluation_id,
    ).first()
    if not agent_result:
        raise HTTPException(status_code=404, detail="Agent result not found")

    if body.instructor_score is not None and not (0 <= body.instructor_score <= 100):
        raise HTTPException(status_code=400, detail="instructor_score must be between 0 and 100")

    agent_result.instructor_score = body.instructor_score
    agent_result.instructor_comment = body.instructor_comment

    # Recalculate instructor total: use instructor_score if set, else fall back to AI score
    all_results = evaluation.agent_results
    has_any_override = any(r.instructor_score is not None for r in all_results)

    if has_any_override:
        instructor_total = sum(
            ((r.instructor_score if r.instructor_score is not None else r.score) / 100) * r.max_score
            for r in all_results
            if r.score is not None and r.max_score is not None
        )
        evaluation.instructor_total_score = round(instructor_total, 1)
    else:
        evaluation.instructor_total_score = None

    db.commit()
    db.refresh(evaluation)
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
                prompt_used=result.prompt_used,
                raw_response=result.raw_response,
                instructor_score=result.instructor_score,
                instructor_comment=result.instructor_comment,
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
        instructor_total_score=evaluation.instructor_total_score,
    )
