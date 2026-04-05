from dataclasses import dataclass
from app.models.agent_configuration import AgentConfiguration


@dataclass
class EvaluationPrompt:
    """Split prompt for caching - system contains report, user contains agent criteria."""
    system: str  # Report content (cacheable)
    user: str    # Agent-specific criteria
    full: str    # Combined prompt for storage/debugging


SYSTEM_TEMPLATE = """Du er en ekspert på å vurdere akademiske rapporter, spesielt labrapporter i kjemi.

## Rapport-innhold

{report_text}

## Generelle instruksjoner

Du vil motta evalueringskriterier for en spesifikk sjekk. Vurder rapporten basert på disse kriteriene.
Gi en score per kriterium og konkret, konstruktiv tilbakemelding.

Svar KUN med gyldig JSON i følgende format (ingen annen tekst):
{{
  "score": <total score - sum av alle kriterier>,
  "feedback": "<hovedtilbakemelding på 2-3 setninger>",
  "details": [
    {{"criterion": "<kriterienavn>", "score": <oppnådd poeng>, "max_score": <maks poeng for dette kriteriet>, "comment": "<kort kommentar>"}}
  ]
}}

VIKTIG: For hvert kriterium, gi en score fra 0 til kriteriets vekt (max_score). Total score skal være summen av alle kriteriescore.
"""

USER_TEMPLATE = """## Evalueringskriterier

Navn: {agent_name}
Beskrivelse: {agent_description}

Kriterier å sjekke:
{criteria_list}

Vurderingsmal: {scoring_rubric}

Gi en score fra 0 til 100.
"""

# Legacy combined template for backwards compatibility
DEFAULT_PROMPT_TEMPLATE = """Du er en ekspert på å vurdere akademiske rapporter, spesielt labrapporter i kjemi.

## Rapport-innhold

{report_text}

## Evalueringskriterier

Navn: {agent_name}
Beskrivelse: {agent_description}

Kriterier å sjekke:
{criteria_list}

Vurderingsmal: {scoring_rubric}

## Instruksjoner

Vurder rapporten basert på kriteriene over.
Gi en score fra 0 til 100 og konkret, konstruktiv tilbakemelding.

Svar KUN med gyldig JSON i følgende format (ingen annen tekst):
{{
  "score": <total score - sum av alle kriterier>,
  "feedback": "<hovedtilbakemelding på 2-3 setninger>",
  "details": [
    {{"criterion": "<kriterienavn>", "score": <oppnådd poeng>, "max_score": <maks poeng for dette kriteriet>, "comment": "<kort kommentar>"}}
  ]
}}

VIKTIG: For hvert kriterium, gi en score fra 0 til kriteriets vekt (max_score). Total score skal være summen av alle kriteriescore.
"""


def build_system_prompt(report_text: str) -> str:
    """Build the cacheable system prompt containing the report."""
    # Truncate report text if too long (keep ~100k characters)
    max_report_length = 100000
    if len(report_text) > max_report_length:
        report_text = report_text[:max_report_length] + "\n\n[... Teksten er forkortet ...]"

    return SYSTEM_TEMPLATE.format(report_text=report_text)


def build_user_prompt(agent: AgentConfiguration) -> str:
    """Build the agent-specific user prompt."""
    criteria = agent.criteria or {}
    check_items = criteria.get("checkItems", [])
    criteria_list = "\n".join(
        f"- {item.get('label', 'Ukjent')} (vekt: {item.get('weight', 1.0)}): {item.get('description', '')}"
        for item in check_items
    )

    if not criteria_list:
        criteria_list = "Ingen spesifikke kriterier definert. Gjør en generell vurdering."

    scoring_rubric = criteria.get("scoringRubric", "Bruk skjønn basert på kriteriene.")

    return USER_TEMPLATE.format(
        agent_name=agent.name,
        agent_description=agent.description or "Ingen beskrivelse",
        criteria_list=criteria_list,
        scoring_rubric=scoring_rubric,
        max_score=agent.max_score,
    )


def build_evaluation_prompt(
    report_text: str,
    agent: AgentConfiguration,
) -> str:
    """Build the full evaluation prompt for a specific agent (legacy, for storage)."""
    # Use custom prompt template if provided
    template = agent.prompt_template or DEFAULT_PROMPT_TEMPLATE

    # Format criteria list
    criteria = agent.criteria or {}
    check_items = criteria.get("checkItems", [])
    criteria_list = "\n".join(
        f"- {item.get('label', 'Ukjent')} (vekt: {item.get('weight', 1.0)}): {item.get('description', '')}"
        for item in check_items
    )

    if not criteria_list:
        criteria_list = "Ingen spesifikke kriterier definert. Gjør en generell vurdering."

    scoring_rubric = criteria.get("scoringRubric", "Bruk skjønn basert på kriteriene.")

    # Truncate report text if too long (keep ~100k characters)
    max_report_length = 100000
    if len(report_text) > max_report_length:
        report_text = report_text[:max_report_length] + "\n\n[... Teksten er forkortet ...]"

    return template.format(
        report_text=report_text,
        agent_name=agent.name,
        agent_description=agent.description or "Ingen beskrivelse",
        criteria_list=criteria_list,
        scoring_rubric=scoring_rubric,
        max_score=agent.max_score,
    )


def build_evaluation_prompt_cached(
    report_text: str,
    agent: AgentConfiguration,
) -> EvaluationPrompt:
    """Build split prompt for caching - system (report) + user (criteria)."""
    return EvaluationPrompt(
        system=build_system_prompt(report_text),
        user=build_user_prompt(agent),
        full=build_evaluation_prompt(report_text, agent),
    )
