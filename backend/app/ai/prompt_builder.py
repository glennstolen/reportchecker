from app.models.agent_configuration import AgentConfiguration

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
Gi en score fra 0 til {max_score} og konkret, konstruktiv tilbakemelding.

Svar KUN med gyldig JSON i følgende format (ingen annen tekst):
{{
  "score": <tall mellom 0 og {max_score}>,
  "feedback": "<hovedtilbakemelding på 2-3 setninger>",
  "details": [
    {{"criterion": "<kriterienavn>", "passed": <true/false>, "comment": "<kort kommentar>"}}
  ]
}}
"""


def build_evaluation_prompt(
    report_text: str,
    agent: AgentConfiguration,
) -> str:
    """Build the evaluation prompt for a specific agent."""
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
