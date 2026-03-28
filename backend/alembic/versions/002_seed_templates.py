"""Seed default agent templates

Revision ID: 002
Revises: 001
Create Date: 2024-01-01

"""
from typing import Sequence, Union
import json

from alembic import op
import sqlalchemy as sa

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TEMPLATES = [
    {
        "name": "Formalitetssjekker",
        "description": "Sjekker at rapporten har korrekt struktur og formaliteter",
        "max_score": 10.0,
        "criteria": {
            "checkItems": [
                {"id": "title_page", "label": "Tittelside med alle nødvendige elementer", "weight": 1.0, "description": "Tittel, forfatternavn, dato, institutt/emne"},
                {"id": "structure", "label": "Korrekt seksjonsstruktur", "weight": 2.0, "description": "Sammendrag, Introduksjon, Metode, Resultater, Diskusjon, Konklusjon"},
                {"id": "page_numbers", "label": "Sidetall på alle sider", "weight": 0.5},
                {"id": "font_formatting", "label": "Konsistent formatering", "weight": 0.5, "description": "Lesbar font, passende størrelse, god lesbarhet"},
                {"id": "length", "label": "Passende lengde", "weight": 1.0, "description": "Ikke for kort eller for lang for oppgavens omfang"},
            ],
            "scoringRubric": "0-2 poeng per kriterie basert på hvor godt det er oppfylt. Trekk for manglende elementer."
        }
    },
    {
        "name": "Kildesjekker",
        "description": "Evaluerer bruk av kilder og referanser",
        "max_score": 10.0,
        "criteria": {
            "checkItems": [
                {"id": "citation_format", "label": "Korrekt referanseformat", "weight": 2.0, "description": "Konsistent bruk av APA, Vancouver eller annet format"},
                {"id": "in_text", "label": "Korrekte in-text referanser", "weight": 2.0, "description": "Alle påstander støttes av referanser der det trengs"},
                {"id": "reference_list", "label": "Komplett referanseliste", "weight": 1.5, "description": "Alle siterte kilder er listet"},
                {"id": "source_quality", "label": "Kvalitet på kilder", "weight": 2.0, "description": "Vitenskapelige, fagfellevurderte kilder prioritert"},
                {"id": "source_quantity", "label": "Tilstrekkelig antall kilder", "weight": 1.0},
            ],
            "scoringRubric": "Vurder kvalitet og konsistens i referansebruk. Fullt poeng krever feilfri referansebruk."
        }
    },
    {
        "name": "Figursjekker",
        "description": "Evaluerer kvalitet på figurer, tabeller og visualiseringer",
        "max_score": 10.0,
        "criteria": {
            "checkItems": [
                {"id": "figure_captions", "label": "Beskrivende figurtekster", "weight": 2.0, "description": "Alle figurer har informative undertekster"},
                {"id": "table_captions", "label": "Beskrivende tabelltekster", "weight": 2.0, "description": "Alle tabeller har informative overskrifter"},
                {"id": "references_in_text", "label": "Referanser til figurer i tekst", "weight": 1.5, "description": "Alle figurer og tabeller omtales i teksten"},
                {"id": "quality", "label": "Visuell kvalitet", "weight": 1.5, "description": "Lesbare akser, tydelige labels, god oppløsning"},
                {"id": "relevance", "label": "Relevante visualiseringer", "weight": 1.5, "description": "Figurene støtter og illustrerer poengene i teksten"},
            ],
            "scoringRubric": "Vurder om figurer og tabeller er profesjonelle og støtter rapporten."
        }
    },
    {
        "name": "Språksjekker",
        "description": "Evaluerer språk, grammatikk og fagterminologi",
        "max_score": 10.0,
        "criteria": {
            "checkItems": [
                {"id": "spelling", "label": "Rettskriving", "weight": 2.0, "description": "Ingen eller svært få skrivefeil"},
                {"id": "grammar", "label": "Grammatikk", "weight": 2.0, "description": "Korrekt setningsbygging og grammatikk"},
                {"id": "terminology", "label": "Fagterminologi", "weight": 2.0, "description": "Korrekt bruk av faglige begreper"},
                {"id": "clarity", "label": "Klarhet og presisjon", "weight": 2.0, "description": "Tydelig og presis formulering"},
                {"id": "academic_tone", "label": "Akademisk tone", "weight": 1.5, "description": "Passende formelt og objektivt språk"},
            ],
            "scoringRubric": "Trekk for gjentatte feil. Fullt poeng krever profesjonelt akademisk språk."
        }
    },
    {
        "name": "Sammendragssjekker",
        "description": "Evaluerer kvaliteten på sammendraget/abstract",
        "max_score": 10.0,
        "criteria": {
            "checkItems": [
                {"id": "length", "label": "Passende lengde (150-300 ord)", "weight": 1.0},
                {"id": "background", "label": "Kort bakgrunn/kontekst", "weight": 1.5, "description": "Hvorfor er dette viktig?"},
                {"id": "objective", "label": "Tydelig formål/problemstilling", "weight": 2.0},
                {"id": "methods", "label": "Kort metodebeskrivelse", "weight": 1.5},
                {"id": "results", "label": "Hovedresultater nevnt", "weight": 2.0},
                {"id": "conclusion", "label": "Hovedkonklusjon", "weight": 1.5},
            ],
            "scoringRubric": "Et godt sammendrag gir leseren full oversikt over rapporten uten å lese resten."
        }
    },
]


def upgrade() -> None:
    conn = op.get_bind()

    for template in TEMPLATES:
        conn.execute(
            sa.text("""
                INSERT INTO agent_configurations (name, description, criteria, max_score, is_template)
                VALUES (:name, :description, :criteria, :max_score, true)
            """),
            {
                "name": template["name"],
                "description": template["description"],
                "criteria": json.dumps(template["criteria"]),
                "max_score": template["max_score"],
            }
        )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM agent_configurations WHERE is_template = true"))
