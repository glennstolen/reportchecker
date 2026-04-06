"""Initial schema with all tables and seed data

Revision ID: 001
Revises:
Create Date: 2026-04-06

Flattened from 10 migrations into one. Includes full schema and 7 agent templates.
"""
import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


AGENT_TEMPLATES = [
    {
        "name": "Formalitetssjekker",
        "description": "Sjekker formelle krav til rapporten",
        "max_score": 3.0,
        "criteria": {
            "checkItems": [
                {"id": "tittelside", "label": "Tittelside", "weight": 20,
                 "description": "Egen side (unummerert) med tittel, kandidatnummer, oppgave, dato, emne, institusjon"},
                {"id": "innholdsfortegnelse", "label": "Innholdsfortegnelse", "weight": 15,
                 "description": "Egen side (unummerert)"},
                {"id": "sammendrag_plassering", "label": "Sammendrag-plassering", "weight": 10,
                 "description": (
                     "Rapporten har en innholdsfortegnelse som lister opp seksjoner – dette er IKKE selve seksjonene. "
                     "Den faktiske Sammendrag-seksjonen kjennetegnes ved at den inneholder flere setninger med eksperimentinnhold (hensikt, metoder, resultater). "
                     "Sjekk at denne seksjonen kommer på en egen side (--- Side X ---) etter siden med innholdsfortegnelsen, "
                     "og at Introduksjon-seksjonen starter på en annen side etter sammendraget.")},
                {"id": "kapittelnummerering", "label": "Kapittelnummerering", "weight": 15,
                 "description": "Sammendrag unummerert, Intro-Diskusjon nummerert (1-5), Referanser/Vedlegg unummerert"},
                {"id": "formatering", "label": "Konsistent formatering", "weight": 10,
                 "description": "Lesbar font, passende størrelse, god lesbarhet"},
                {"id": "lengde", "label": "Passende lengde", "weight": 10,
                 "description": "Ikke for kort eller for lang for oppgavens omfang"},
                {"id": "rod_trad", "label": "Rød tråd", "weight": 20,
                 "description": "Logisk sammenheng gjennom hele rapporten"},
            ],
            "scoringRubric": "Gi poeng basert på hvor godt hvert kriterie er oppfylt. Total score 0-100. Rapporten skal inneholde kandidatnummer (IKKE navn)."
        }
    },
    {
        "name": "Kildesjekker",
        "description": "Sjekker kildebruk og referanser",
        "max_score": 3.0,
        "criteria": {
            "checkItems": [
                {"id": "egenprodusert", "label": "Egenprodusert tekst", "weight": 25,
                 "description": "Teksten er skrevet med egne ord, ikke kopiert"},
                {"id": "tillatte_kilder", "label": "Tillatte kilder", "weight": 30,
                 "description": "Bruker lærebok (Clark et al.), vitenskapelige artikler og offentlige nettsider som forventet. Ingen Wikipedia eller Canvas-teori brukt. Forsøksbeskrivelse fra OsloMet er korrekt brukt"},
                {"id": "referansestil", "label": "Konsekvent referansestil", "weight": 15,
                 "description": "IEEE eller APA brukt konsekvent"},
                {"id": "intext", "label": "In-text referanser", "weight": 15,
                 "description": "Korrekte referanser i teksten der påstander/fakta presenteres"},
                {"id": "referanseliste", "label": "Komplett referanseliste", "weight": 10,
                 "description": "Alle siterte kilder er i referanselisten"},
                {"id": "kildekvalitet", "label": "Kildekvalitet", "weight": 5,
                 "description": "Fagfellevurderte kilder prioritert"},
            ],
            "scoringRubric": "Vurder om rapporten bruker egne formuleringer og siterer kilder korrekt. Total score 0-100. Trekk for Wikipedia, Canvas-teori eller manglende referanser."
        }
    },
    {
        "name": "Figur-, tabell- og ligningssjekker",
        "description": "Sjekker formatering av figurer, tabeller og ligninger",
        "max_score": 2.0,
        "criteria": {
            "checkItems": [
                {"id": "tabelltekst", "label": "Tabelltekst", "weight": 15,
                 "description": "Tabelltekst OVER tabellen, i mindre skrift"},
                {"id": "figurtekst", "label": "Figurtekst", "weight": 15,
                 "description": "Figurtekst UNDER figuren, i mindre skrift"},
                {"id": "grafer", "label": "Grafer", "weight": 15,
                 "description": "Uten støttelinjer og overskrifter, aksetitler med benevning"},
                {"id": "tabellformatering", "label": "Tabellformatering", "weight": 10,
                 "description": "Unngå tomme celler, innenfor marginer, ikke delt over sider"},
                {"id": "ligning_nummerering", "label": "Ligningsnummerering", "weight": 15,
                 "description": "Ligninger er nummerert og henvist til i tekst"},
                {"id": "symboler", "label": "Symbolforklaring", "weight": 10,
                 "description": "Symboler i ligninger er forklart"},
                {"id": "stokiometri", "label": "Støkiometrisk formatering", "weight": 5,
                 "description": "Støkiometriske indekser i senket skrift"},
                {"id": "radata", "label": "Rådata plassering", "weight": 15,
                 "description": "Rådata i vedlegg, ikke i hoveddelen"},
            ],
            "scoringRubric": "Vurder formatering av figurer, tabeller og ligninger. Total score 0-100. Sjekk at figur-/tabelltekster er korrekt plassert og at ligninger er nummerert."
        }
    },
    {
        "name": "Språksjekker",
        "description": "Sjekker språk, grammatikk og akademisk tone",
        "max_score": 2.0,
        "criteria": {
            "checkItems": [
                {"id": "rettskriving", "label": "Rettskriving og grammatikk", "weight": 20,
                 "description": "Korrekt norsk rettskriving og grammatikk"},
                {"id": "tid_sammendrag", "label": "Tid i sammendrag", "weight": 10,
                 "description": "Passiv fortid"},
                {"id": "tid_intro", "label": "Tid i introduksjon", "weight": 10,
                 "description": "Passiv fortid + nåtid for teori"},
                {"id": "tid_metode", "label": "Tid i metode", "weight": 10,
                 "description": "Passiv fortid"},
                {"id": "tid_resultat_diskusjon", "label": "Tid i resultat/diskusjon", "weight": 10,
                 "description": "Blanding tillatt, 'vi' tillatt men aldri 'jeg'"},
                {"id": "forkortelser", "label": "Forkortelser", "weight": 10,
                 "description": "Forklares ved første bruk"},
                {"id": "akademisk_tone", "label": "Akademisk tone", "weight": 15,
                 "description": "Unngå adjektiv/adverb (meget, veldig), småord (nok, vel, da), konkrete tidsangivelser"},
                {"id": "fagterminologi", "label": "Fagterminologi", "weight": 15,
                 "description": "Korrekt bruk av fagtermer"},
            ],
            "scoringRubric": "Vurder språklig kvalitet, korrekt bruk av tid i ulike kapitler, og akademisk tone. Total score 0-100. Trekk for 'jeg', vage formuleringer eller feil tid."
        }
    },
    {
        "name": "Sammendragssjekker",
        "description": "Sjekker sammendragets innhold og format",
        "max_score": 2.0,
        "criteria": {
            "checkItems": [
                {"id": "lengde", "label": "Lengde", "weight": 15,
                 "description": "Maks halv side"},
                {"id": "hensikt", "label": "Hensikt", "weight": 15,
                 "description": "Formålet med forsøket er beskrevet"},
                {"id": "metoder", "label": "Metoder", "weight": 15,
                 "description": "Kort beskrivelse av metoder brukt"},
                {"id": "hovedresultater", "label": "Hovedresultater", "weight": 20,
                 "description": "De viktigste resultatene er presentert"},
                {"id": "kvalitet_feil", "label": "Kvalitet og feilkilder", "weight": 15,
                 "description": "Kvalitetsvurdering og feilkilder nevnt"},
                {"id": "konklusjon", "label": "Konklusjon", "weight": 10,
                 "description": "Kort konklusjon inkludert"},
                {"id": "selvstendig", "label": "Selvstendig lesbart", "weight": 5,
                 "description": "Kan leses uavhengig av resten"},
                {"id": "ingen_ref_fig", "label": "Ingen referanser/figurer", "weight": 5,
                 "description": "Inneholder IKKE referanser, figurer eller tabeller"},
            ],
            "scoringRubric": "Vurder om sammendraget gir et komplett bilde av forsøket på maks halv side. Total score 0-100. Trekk for referanser, figurer eller manglende elementer."
        }
    },
    {
        "name": "Innholdssjekker",
        "description": "Sjekker faglig innhold i alle kapitler (Introduksjon 18p, Metode 24p, Resultater 35p, Diskusjon+Konklusjon 23p)",
        "max_score": 85.0,
        "criteria": {
            "checkItems": [
                {"id": "intro_hensikt", "label": "Introduksjon: Hensikt", "weight": 5,
                 "description": "Kort hensikt i fortid"},
                {"id": "intro_teori", "label": "Introduksjon: Bakgrunnsteori", "weight": 8,
                 "description": "Tilstrekkelig bakgrunnsteori og prinsipper for teknikker"},
                {"id": "intro_underkapitler", "label": "Introduksjon: Struktur", "weight": 3,
                 "description": "Tematiske underkapitler, ligninger oppgis fortløpende"},
                {"id": "intro_ikke_eksperiment", "label": "Introduksjon: Ikke eksperimentelt", "weight": 2,
                 "description": "IKKE eksperimentelle opplysninger"},
                {"id": "metode_materialer", "label": "Metode: Materialer", "weight": 8,
                 "description": "Materialer med produsentnavn, artikkelnummer, konsentrasjon"},
                {"id": "metode_utstyr", "label": "Metode: Utstyr", "weight": 5,
                 "description": "Utstyr med produsent og modell, instrumentinnstillinger"},
                {"id": "metode_beskrivelse", "label": "Metode: Beskrivelse", "weight": 8,
                 "description": "Passiv fortid, detaljert nok til å gjenta, henvisning til forsøksbeskrivelse"},
                {"id": "metode_ikke_data", "label": "Metode: Ikke bearbeidede data", "weight": 3,
                 "description": "IKKE bearbeidede måledata"},
                {"id": "resultat_innledning", "label": "Resultater: Innledning", "weight": 9,
                 "description": "Innledende tekst før figurer/tabeller"},
                {"id": "resultat_kronologisk", "label": "Resultater: Kronologisk", "weight": 17,
                 "description": "Kronologisk presentasjon, beskrevet i tekst"},
                {"id": "resultat_ikke", "label": "Resultater: Unngå", "weight": 9,
                 "description": "IKKE forkastede forsøk, metodegjentagelse eller diskusjon"},
                {"id": "diskusjon_oppsummering", "label": "Diskusjon: Oppsummering", "weight": 5,
                 "description": "Kort oppsummering først"},
                {"id": "diskusjon_sammenligning", "label": "Diskusjon: Sammenligning", "weight": 7,
                 "description": "Sammenligning med teori/litteraturverdier"},
                {"id": "diskusjon_feilkilder", "label": "Diskusjon: Feilkilder", "weight": 7,
                 "description": "Feilkilder identifisert og effekt diskutert"},
                {"id": "konklusjon", "label": "Konklusjon", "weight": 4,
                 "description": "Ble hensikten oppnådd? Usikkerhetsvurdering"},
            ],
            "scoringRubric": "Vurder innholdet i hvert hovedkapittel. Total score 0-100 (Introduksjon maks 18, Metode maks 24, Resultater maks 35, Diskusjon+Konklusjon maks 23). Sjekk at hvert kapittel inneholder riktige elementer og unngår feil plassering av innhold."
        }
    },
    {
        "name": "Helhetsvurdering",
        "description": "Gir en helhetsvurdering av rapportens kvalitet",
        "max_score": 3.0,
        "criteria": {
            "checkItems": [
                {"id": "rod_trad", "label": "Rød tråd", "weight": 29,
                 "description": "Logisk sammenheng gjennom hele rapporten"},
                {"id": "lesbarhet", "label": "Lesbarhet", "weight": 21,
                 "description": "Leseren ledes gjennom trinnene på en klar måte"},
                {"id": "kapittelsammenheng", "label": "Kapittelsammenheng", "weight": 21,
                 "description": "Kapitler henger sammen og bygger på hverandre"},
                {"id": "profesjonelt", "label": "Profesjonelt inntrykk", "weight": 14,
                 "description": "Profesjonelt og vitenskapelig helhetsinntrykk"},
                {"id": "malgruppe", "label": "Målgruppe", "weight": 15,
                 "description": "Egnet for en leser med generelle kjemikunnskaper"},
            ],
            "scoringRubric": "Gi en helhetsvurdering av rapportens kvalitet. Total score 0-100. Vurder om rapporten fungerer som en sammenhengende vitenskapelig tekst."
        }
    },
]


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=True, server_default='lecturer'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # Reports table
    op.create_table(
        'reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('content_text', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('UPLOADED', 'PROCESSING', 'READY', 'ERROR', name='reportstatus'),
                  nullable=True, server_default='UPLOADED'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('kandidater', sa.JSON(), nullable=True),
        sa.Column('oppgave', sa.String(255), nullable=True),
        sa.Column('innleveringsdato', sa.Date(), nullable=True),
        sa.Column('anonymized_file_path', sa.String(500), nullable=True),
        sa.Column('mapping_file_path', sa.String(500), nullable=True),
        sa.Column('candidate_mappings', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_reports_id', 'reports', ['id'])

    # Agent configurations table
    op.create_table(
        'agent_configurations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('criteria', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('max_score', sa.Float(), nullable=True, server_default='10.0'),
        sa.Column('prompt_template', sa.Text(), nullable=True),
        sa.Column('is_template', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_agent_configurations_id', 'agent_configurations', ['id'])

    # Evaluations table
    op.create_table(
        'evaluations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'ERROR', name='evaluationstatus'),
                  nullable=True, server_default='PENDING'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_score', sa.Float(), nullable=True),
        sa.Column('max_possible_score', sa.Float(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_evaluations_id', 'evaluations', ['id'])

    # Agent results table
    op.create_table(
        'agent_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('evaluation_id', sa.Integer(), nullable=False),
        sa.Column('agent_config_id', sa.Integer(), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('max_score', sa.Float(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'ERROR',
                                    name='evaluationstatus', create_type=False),
                  nullable=True, server_default='PENDING'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('prompt_used', sa.Text(), nullable=True),
        sa.Column('raw_response', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['evaluation_id'], ['evaluations.id']),
        sa.ForeignKeyConstraint(['agent_config_id'], ['agent_configurations.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_agent_results_id', 'agent_results', ['id'])

    # Seed agent templates
    conn = op.get_bind()
    for agent in AGENT_TEMPLATES:
        conn.execute(
            sa.text(
                "INSERT INTO agent_configurations (name, description, criteria, max_score, is_template) "
                "VALUES (:name, :description, :criteria, :max_score, true)"
            ),
            {
                "name": agent["name"],
                "description": agent["description"],
                "criteria": json.dumps(agent["criteria"]),
                "max_score": agent["max_score"],
            }
        )


def downgrade() -> None:
    op.drop_table('agent_results')
    op.drop_table('evaluations')
    op.drop_table('agent_configurations')
    op.drop_table('reports')
    op.drop_table('users')
    op.execute('DROP TYPE IF EXISTS evaluationstatus')
    op.execute('DROP TYPE IF EXISTS reportstatus')
