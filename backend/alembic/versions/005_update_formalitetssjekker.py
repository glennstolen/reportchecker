"""Update Formalitetssjekker for anonymized reports

Revision ID: 005
Revises: 004
Create Date: 2026-03-31

"""
from typing import Sequence, Union
import json

from alembic import op
import sqlalchemy as sa


revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NEW_CRITERIA = {
    "checkItems": [
        {
            "id": "report_title",
            "label": "Rapporttittel",
            "weight": 2.0,
            "description": "Rapporten har en beskrivende tittel (f.eks. 'Bestemmelse av syreinnhold i eddik')"
        },
        {
            "id": "kandidat",
            "label": "Kandidatnummer",
            "weight": 1.5,
            "description": "Kandidat: er fylt inn med kandidatnummer (ikke navn)"
        },
        {
            "id": "oppgave",
            "label": "Oppgavenavn",
            "weight": 1.5,
            "description": "Oppgave: er fylt inn med oppgavenavn/lab-nummer"
        },
        {
            "id": "dato",
            "label": "Innleveringsdato",
            "weight": 1.0,
            "description": "Dato: er fylt inn med innleveringsdato"
        },
        {
            "id": "structure",
            "label": "Korrekt seksjonsstruktur",
            "weight": 2.0,
            "description": "Sammendrag, Introduksjon, Metode, Resultater, Diskusjon, Konklusjon"
        },
        {
            "id": "page_numbers",
            "label": "Sidetall på alle sider",
            "weight": 0.5
        },
        {
            "id": "font_formatting",
            "label": "Konsistent formatering",
            "weight": 0.5,
            "description": "Lesbar font, passende størrelse, god lesbarhet"
        },
        {
            "id": "length",
            "label": "Passende lengde",
            "weight": 1.0,
            "description": "Ikke for kort eller for lang for oppgavens omfang"
        },
    ],
    "scoringRubric": "Gi poeng basert på hvor godt hvert kriterie er oppfylt. Merk: Rapporten skal IKKE inneholde studentens navn - kun kandidatnummer."
}


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("""
            UPDATE agent_configurations
            SET criteria = :criteria
            WHERE name = 'Formalitetssjekker' AND is_template = true
        """),
        {"criteria": json.dumps(NEW_CRITERIA)}
    )


def downgrade() -> None:
    # Revert to original criteria
    old_criteria = {
        "checkItems": [
            {"id": "title_page", "label": "Tittelside med alle nødvendige elementer", "weight": 1.0, "description": "Tittel, forfatternavn, dato, institutt/emne"},
            {"id": "structure", "label": "Korrekt seksjonsstruktur", "weight": 2.0, "description": "Sammendrag, Introduksjon, Metode, Resultater, Diskusjon, Konklusjon"},
            {"id": "page_numbers", "label": "Sidetall på alle sider", "weight": 0.5},
            {"id": "font_formatting", "label": "Konsistent formatering", "weight": 0.5, "description": "Lesbar font, passende størrelse, god lesbarhet"},
            {"id": "length", "label": "Passende lengde", "weight": 1.0, "description": "Ikke for kort eller for lang for oppgavens omfang"},
        ],
        "scoringRubric": "0-2 poeng per kriterie basert på hvor godt det er oppfylt. Trekk for manglende elementer."
    }
    conn = op.get_bind()
    conn.execute(
        sa.text("""
            UPDATE agent_configurations
            SET criteria = :criteria
            WHERE name = 'Formalitetssjekker' AND is_template = true
        """),
        {"criteria": json.dumps(old_criteria)}
    )
