import asyncio
import json
import re
from typing import Any

from app.models.agent_configuration import AgentConfiguration
from app.ai.claude_client import ClaudeClient
from app.ai.prompt_builder import build_evaluation_prompt


class EvaluationOrchestrator:
    """Orchestrates parallel evaluation of a report by multiple agents."""

    def __init__(self):
        self.client = ClaudeClient()

    async def evaluate_report(
        self,
        report_text: str,
        agents: list[AgentConfiguration],
    ) -> dict[int, dict[str, Any]]:
        """
        Evaluate a report using multiple agents in parallel.

        Returns a dict mapping agent_config_id to result dict.
        """
        # Create evaluation tasks for all agents
        tasks = [
            self._evaluate_with_agent(report_text, agent)
            for agent in agents
        ]

        # Run all evaluations in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Map results to agent IDs
        result_dict = {}
        for agent, result in zip(agents, results):
            if isinstance(result, Exception):
                result_dict[agent.id] = {
                    "score": None,
                    "feedback": f"Evaluering feilet: {str(result)}",
                    "details": [],
                }
            else:
                result_dict[agent.id] = result

        return result_dict

    async def _evaluate_with_agent(
        self,
        report_text: str,
        agent: AgentConfiguration,
    ) -> dict[str, Any]:
        """Evaluate a report with a single agent."""
        prompt = build_evaluation_prompt(report_text, agent)

        response = await self.client.evaluate(prompt)

        # Parse JSON response
        return self._parse_response(response, agent.max_score)

    def _parse_response(self, response: str, max_score: float) -> dict[str, Any]:
        """Parse the JSON response from Claude."""
        # Try to extract JSON from the response
        # Claude might include some text before/after the JSON
        json_match = re.search(r'\{[\s\S]*\}', response)

        if not json_match:
            return {
                "score": None,
                "feedback": "Kunne ikke parse respons fra AI",
                "details": [],
            }

        try:
            data = json.loads(json_match.group())

            # Validate and clamp score
            score = data.get("score")
            if score is not None:
                score = max(0, min(float(score), max_score))

            return {
                "score": score,
                "feedback": data.get("feedback", ""),
                "details": data.get("details", []),
            }
        except json.JSONDecodeError:
            return {
                "score": None,
                "feedback": "Kunne ikke parse JSON-respons fra AI",
                "details": [],
            }
