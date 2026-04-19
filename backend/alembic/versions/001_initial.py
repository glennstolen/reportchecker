"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-04-19
"""
import json
import os
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
                {"id": "tittelside", "label": "Tittelside", "weight": 10,
                 "description": "Egen side (unummerert) med tittel, kandidatnummer, oppgave, dato, emne, institusjon"},
                {"id": "innholdsfortegnelse", "label": "Innholdsfortegnelse", "weight": 15,
                 "description": "Egen side (unummerert)"},
                {"id": "kapittelnummerering", "label": "Kapittelnummerering", "weight": 15,
                 "description": "Sammendrag unummerert, Intro-Diskusjon nummerert (1-5), Referanser/Vedlegg unummerert"},
                {"id": "formatering", "label": "Konsistent formatering", "weight": 20,
                 "description": "Lesbar font, passende størrelse, god lesbarhet"},
                {"id": "lengde", "label": "Passende lengde", "weight": 20,
                 "description": "Ikke for kort eller for lang for oppgavens omfang"},
                {"id": "rod_trad", "label": "Rød tråd", "weight": 20,
                 "description": "Logisk sammenheng gjennom hele rapporten"},
            ],
            "scoringRubric": "Vurder formelle krav strengt. 0–30: Mangler tittelside, innholdsfortegnelse eller korrekt struktur. 30–50: Noen formelle krav oppfylt, men vesentlige mangler (f.eks. feil sideoppsett). 50–70: De fleste krav oppfylt, men med tydelige feil i nummerering eller plassering. 70–85: Godt arbeid, kun mindre formelle feil. 85–100: Alle formelle krav korrekt oppfylt."
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
            "scoringRubric": "Vurder kildebruk strengt. 0–30: Teksten er kopiert eller svært lite egenprodusert, og/eller ulovlige kilder (Wikipedia, Canvas-teori) dominerer. 30–50: Noen korrekte kilder brukt, men stor andel feil eller manglende referanser. 50–70: Tilfredsstillende kildebruk med noen feil i stil eller in-text-referanser. 70–85: God kildebruk, konsekvent referansestil med mindre feil. 85–100: Eksemplarisk kildebruk, korrekt og konsekvent referansestil gjennomgående. Trekk for Wikipedia, Canvas-teori eller manglende in-text-referanser der påstander fremsettes."
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
            "scoringRubric": "Vurder formatering av figurer, tabeller og ligninger strengt. 0–30: Figurtekst over figurer, tabelltekst under tabeller, eller ligninger unummerert gjennomgående. 30–50: Flere formateringsfeil, men noe er riktig. 50–70: Tilfredsstillende formatering med noen feil i plassering eller nummerering. 70–85: Godt arbeid, kun enkeltstående feil. 85–100: Korrekt formatering gjennomgående. Sjekk spesielt at figurtekst er UNDER og tabelltekst er OVER."
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
            "scoringRubric": "Vurder språklig kvalitet strengt. 0–30: Store grammatikkfeil, feil tid brukt gjennomgående, eller uakademisk språk dominerer. 30–50: Vesentlige feil i tidsbruk per kapittel og/eller hyppig bruk av 'jeg', vage ord og adjektiver. 50–70: Tilfredsstillende, men tydelige svakheter i akademisk tone eller tidsbruk i ett eller flere kapitler. 70–85: Godt språk med noen enkeltstående feil. 85–100: Akademisk og korrekt norsk gjennomgående. Trekk for 'jeg', 'veldig', 'ganske', konkrete tidsangivelser og feil verbal tid."
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
            "scoringRubric": "Vurder sammendraget strengt. 0–30: Mangler de fleste obligatoriske elementer (hensikt, metoder, resultater, konklusjon). 30–50: Noen elementer tilstede, men vesentlige mangler eller sammendraget er for langt/kort. 50–70: De fleste elementer inkludert, men med tydelige svakheter i innhold eller struktur. 70–85: Godt sammendrag med noen mangler. 85–100: Komplett og selvstendig lesbart sammendrag innenfor halv side. Trekk for referanser, figurer eller tabeller i sammendraget."
        }
    },
    {
        "name": "Innholdssjekker",
        "description": "Sjekker faglig innhold i alle kapitler (Introduksjon 15p, Metode 20p, Resultater 30p, Diskusjon+Konklusjon 20p, Faglig korrekthet 15p)",
        "max_score": 85.0,
        "criteria": {
            "checkItems": [
                {"id": "intro_hensikt", "label": "Introduksjon: Hensikt", "weight": 4,
                 "description": "Kort hensikt i fortid"},
                {"id": "intro_teori", "label": "Introduksjon: Bakgrunnsteori", "weight": 7,
                 "description": "Tilstrekkelig bakgrunnsteori og prinsipper for teknikker"},
                {"id": "intro_underkapitler", "label": "Introduksjon: Struktur", "weight": 2,
                 "description": "Tematiske underkapitler, ligninger oppgis fortløpende"},
                {"id": "intro_ikke_eksperiment", "label": "Introduksjon: Ikke eksperimentelt", "weight": 2,
                 "description": "IKKE eksperimentelle opplysninger"},
                {"id": "metode_materialer", "label": "Metode: Materialer", "weight": 7,
                 "description": "Materialer med produsentnavn, artikkelnummer, konsentrasjon"},
                {"id": "metode_utstyr", "label": "Metode: Utstyr", "weight": 4,
                 "description": "Utstyr med produsent og modell, instrumentinnstillinger"},
                {"id": "metode_beskrivelse", "label": "Metode: Beskrivelse", "weight": 7,
                 "description": "Passiv fortid, detaljert nok til å gjenta, henvisning til forsøksbeskrivelse"},
                {"id": "metode_ikke_data", "label": "Metode: Ikke bearbeidede data", "weight": 2,
                 "description": "IKKE bearbeidede måledata"},
                {"id": "resultat_innledning", "label": "Resultater: Innledning", "weight": 8,
                 "description": "Innledende tekst før figurer/tabeller"},
                {"id": "resultat_kronologisk", "label": "Resultater: Kronologisk", "weight": 15,
                 "description": "Kronologisk presentasjon, beskrevet i tekst"},
                {"id": "resultat_ikke", "label": "Resultater: Unngå", "weight": 7,
                 "description": "IKKE forkastede forsøk, metodegjentagelse eller diskusjon"},
                {"id": "diskusjon_oppsummering", "label": "Diskusjon: Oppsummering", "weight": 4,
                 "description": "Kort oppsummering først"},
                {"id": "diskusjon_sammenligning", "label": "Diskusjon: Sammenligning", "weight": 6,
                 "description": "Sammenligning med teori/litteraturverdier"},
                {"id": "diskusjon_feilkilder", "label": "Diskusjon: Feilkilder", "weight": 6,
                 "description": "Feilkilder identifisert og effekt diskutert"},
                {"id": "konklusjon", "label": "Diskusjon: Konklusjon", "weight": 4,
                 "description": "Ble hensikten oppnådd? Usikkerhetsvurdering"},
                {"id": "faglig_korrekthet", "label": "Faglig korrekthet", "weight": 15,
                 "description": "Vurder om rapporten inneholder faglige feil, misforståelser eller unøyaktige påstander innen bioteknologi og biokjemi. Påpek konkrete feil med forklaring."},
            ],
            "scoringRubric": "Vurder faglig innhold strengt per kapittel (Introduksjon maks 15, Metode maks 20, Resultater maks 30, Diskusjon+Konklusjon maks 20, Faglig korrekthet maks 15). 0–30: Store faglige mangler i flere kapitler, feil plassering av innhold, mangler sentrale elementer. 30–50: Noen kapitler tilfredsstillende, men vesentlige faglige mangler eller feil struktur. 50–70: De fleste krav oppfylt per kapittel, men tydelige svakheter (f.eks. lite diskusjon av feilkilder, svak metodebeskrivelse). 70–85: Godt faglig innhold, kun mindre mangler. 85–100: Fremragende faglig innhold i alle kapitler. Sjekk at hvert kapittel inneholder riktige elementer og IKKE inneholder innhold som hører hjemme i andre kapitler."
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
            "scoringRubric": "Gi en helhetsvurdering av rapportens kvalitet. 0–30: Rapporten fremstår uferdig eller usammenhengende, vanskelig å følge for en leser. 30–50: Noe sammenheng, men tydelige brudd i rød tråd eller store svakheter i lesbarhet. 50–70: Tilfredsstillende helhet, men med merkbare svakheter i flyt eller profesjonelt inntrykk. 70–85: Godt helhetsinntrykk, leser ledes greit gjennom rapporten. 85–100: Profesjonell, vitenskapelig rapport med sterk rød tråd gjennomgående."
        }
    },
]


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('role', sa.String(50), nullable=True, server_default='lecturer'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
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
        sa.Column('instructor_total_score', sa.Float(), nullable=True),
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
        sa.Column('instructor_score', sa.Float(), nullable=True),
        sa.Column('instructor_comment', sa.Text(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('prompt_used', sa.Text(), nullable=True),
        sa.Column('raw_response', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'ERROR',
                                    name='evaluationstatus', create_type=False),
                  nullable=True, server_default='PENDING'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['evaluation_id'], ['evaluations.id']),
        sa.ForeignKeyConstraint(['agent_config_id'], ['agent_configurations.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_agent_results_id', 'agent_results', ['id'])

    # Candidate registry table
    op.create_table(
        'candidate_registry',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name_normalized', sa.String(500), nullable=False),
        sa.Column('candidate_number', sa.String(6), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('name_normalized'),
        sa.UniqueConstraint('candidate_number'),
    )
    op.create_index('ix_candidate_registry_name_normalized', 'candidate_registry', ['name_normalized'])

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

    # Seed admin user from ADMIN_EMAIL env var
    admin_email = os.environ.get("ADMIN_EMAIL", "")
    if admin_email:
        existing = conn.execute(
            sa.text("SELECT id FROM users WHERE email = :email"),
            {"email": admin_email},
        ).fetchone()
        if not existing:
            conn.execute(
                sa.text("INSERT INTO users (email, is_active) VALUES (:email, true)"),
                {"email": admin_email},
            )
            print(f"Admin-bruker opprettet: {admin_email}")


def downgrade() -> None:
    op.drop_index('ix_candidate_registry_name_normalized', 'candidate_registry')
    op.drop_table('candidate_registry')
    op.drop_table('agent_results')
    op.drop_table('evaluations')
    op.drop_table('agent_configurations')
    op.drop_table('reports')
    op.drop_table('users')
    op.execute('DROP TYPE IF EXISTS evaluationstatus')
    op.execute('DROP TYPE IF EXISTS reportstatus')
