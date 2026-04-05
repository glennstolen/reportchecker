import asyncio
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.report import Report
from app.models.agent_configuration import AgentConfiguration
from app.models.evaluation import Evaluation, AgentResult, EvaluationStatus
from app.ai.evaluation_orchestrator import EvaluationOrchestrator


class EvaluationService:
    def __init__(self, db: Session):
        self.db = db

    async def create_and_run_evaluation(
        self,
        report: Report,
        agents: list[AgentConfiguration],
    ) -> Evaluation:
        """Create an evaluation and run all agent evaluations."""
        # Create evaluation record
        evaluation = Evaluation(
            report_id=report.id,
            status=EvaluationStatus.PENDING,
        )
        self.db.add(evaluation)
        self.db.commit()
        self.db.refresh(evaluation)

        # Create agent result records
        for agent in agents:
            agent_result = AgentResult(
                evaluation_id=evaluation.id,
                agent_config_id=agent.id,
                max_score=agent.max_score,
                status=EvaluationStatus.PENDING,
            )
            self.db.add(agent_result)
        self.db.commit()
        self.db.refresh(evaluation)

        # Start evaluation
        evaluation.status = EvaluationStatus.RUNNING
        evaluation.started_at = datetime.utcnow()
        self.db.commit()

        # Run evaluations in parallel
        orchestrator = EvaluationOrchestrator()

        try:
            results = await orchestrator.evaluate_report(
                report_text=report.content_text,
                agents=agents,
            )

            # Update agent results
            for agent_result in evaluation.agent_results:
                agent_id = agent_result.agent_config_id
                if agent_id in results:
                    result_data = results[agent_id]
                    agent_result.score = result_data.get("score")
                    agent_result.feedback = result_data.get("feedback")
                    agent_result.details = result_data.get("details")
                    agent_result.status = EvaluationStatus.COMPLETED
                else:
                    agent_result.status = EvaluationStatus.ERROR
                    agent_result.error_message = "No result returned"

            # Claude scores 0-100 per agent. Contribution = (score/100) * agent.max_score (percentage weight).
            total_score = sum(
                (r.score / 100) * r.max_score
                for r in evaluation.agent_results
                if r.score is not None and r.max_score is not None
            )
            evaluation.total_score = round(total_score, 1)
            evaluation.max_possible_score = 100.0
            evaluation.status = EvaluationStatus.COMPLETED
            evaluation.completed_at = datetime.utcnow()

            # Generate summary
            evaluation.summary = self._generate_summary(evaluation)

        except Exception as e:
            evaluation.status = EvaluationStatus.ERROR
            evaluation.summary = f"Evaluation failed: {str(e)}"

        self.db.commit()
        self.db.refresh(evaluation)

        return evaluation

    def _generate_summary(self, evaluation: Evaluation) -> str:
        """Generate a summary of the evaluation results."""
        if not evaluation.agent_results:
            return "No evaluation results."

        completed = [r for r in evaluation.agent_results if r.status == EvaluationStatus.COMPLETED]
        if not completed:
            return "No completed evaluations."

        lines = []
        for result in completed:
            agent_name = result.agent_configuration.name
            score_str = f"{result.score:.1f}/{result.max_score:.1f}" if result.score is not None else "N/A"
            lines.append(f"- {agent_name}: {score_str}")

        # total_score is already normalized to 100
        return f"Total: {evaluation.total_score:.1f}/100 ({evaluation.total_score:.0f}%)\n\n" + "\n".join(lines)
