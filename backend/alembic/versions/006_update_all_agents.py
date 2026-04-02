"""Replace all agents with 8 updated template agents

Revision ID: 006
Revises: 005
Create Date: 2026-03-29

"""
from typing import Sequence, Union
import json

from alembic import op
import sqlalchemy as sa


revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# 8 new agents based on university guidelines
# Scoring based on "Vurderingskriterier labrapport.docx":
# - Skriving og struktur: 10% (split among Formalitet, Kilder, Figur, Språk)
# - Sammendrag: 2%
# - Introduksjon: 15%
# - Metodedelen: 20%
# - Resultater: 30%
# - Diskusjon og konklusjon: 20%
# Total: ~100 points

NEW_AGENTS = [
    {
        "name": "Formalitetssjekker",
        "description": "Sjekker struktur, tittelside, nummerering og formatering (del av 'Skriving og struktur')",
        "max_score": 3.0,
        "criteria": {
            "checkItems": [
                {"id": "tittelside", "label": "Tittelside", "weight": 2.0,
                 "description": "Egen side (unummerert) med tittel, kandidatnummer, oppgave, dato, emne, institusjon"},
                {"id": "innholdsfortegnelse", "label": "Innholdsfortegnelse", "weight": 1.5,
                 "description": "Egen side (unummerert)"},
                {"id": "sammendrag_plassering", "label": "Sammendrag-plassering", "weight": 1.0,
                 "description": "Sammendrag på egen side, sidenummerering starter her"},
                {"id": "kapittelnummerering", "label": "Kapittelnummerering", "weight": 1.5,
                 "description": "Sammendrag unummerert, Intro-Diskusjon nummerert (1-5), Referanser/Vedlegg unummerert"},
                {"id": "formatering", "label": "Konsistent formatering", "weight": 1.0,
                 "description": "Lesbar font, passende størrelse, god lesbarhet"},
                {"id": "lengde", "label": "Passende lengde", "weight": 1.0,
                 "description": "Ikke for kort eller for lang for oppgavens omfang"},
                {"id": "rod_trad", "label": "Rød tråd", "weight": 2.0,
                 "description": "Logisk sammenheng gjennom hele rapporten"},
            ],
            "scoringRubric": "Gi poeng basert på hvor godt hvert kriterie er oppfylt. Rapporten skal inneholde kandidatnummer (IKKE navn)."
        }
    },
    {
        "name": "Kildesjekker",
        "description": "Sjekker kilder, referanser og egenprodusert tekst (del av 'Skriving og struktur')",
        "max_score": 3.0,
        "criteria": {
            "checkItems": [
                {"id": "egenprodusert", "label": "Egenprodusert tekst", "weight": 2.5,
                 "description": "Teksten er skrevet med egne ord, ikke kopiert"},
                {"id": "tillatte_kilder", "label": "Tillatte kilder", "weight": 1.5,
                 "description": "Bruker lærebok, vitenskapelige artikler, offentlige nettsider"},
                {"id": "ikke_tillatte", "label": "Unngår ikke-tillatte kilder", "weight": 1.5,
                 "description": "Unngår Wikipedia, forelesningsnotater, Canvas-teori (unntak: forsøksbeskrivelse)"},
                {"id": "referansestil", "label": "Konsekvent referansestil", "weight": 1.5,
                 "description": "IEEE eller APA brukt konsekvent"},
                {"id": "intext", "label": "In-text referanser", "weight": 1.5,
                 "description": "Korrekte referanser i teksten der påstander/fakta presenteres"},
                {"id": "referanseliste", "label": "Komplett referanseliste", "weight": 1.0,
                 "description": "Alle siterte kilder er i referanselisten"},
                {"id": "kildekvalitet", "label": "Kildekvalitet", "weight": 0.5,
                 "description": "Fagfellevurderte kilder prioritert"},
            ],
            "scoringRubric": "Vurder om rapporten bruker egne formuleringer og siterer kilder korrekt. Trekk for Wikipedia, Canvas-teori eller manglende referanser."
        }
    },
    {
        "name": "Figur-, tabell- og ligningssjekker",
        "description": "Sjekker figurer, tabeller og ligninger (del av 'Skriving og struktur')",
        "max_score": 3.0,
        "criteria": {
            "checkItems": [
                {"id": "tabelltekst", "label": "Tabelltekst", "weight": 1.5,
                 "description": "Tabelltekst OVER tabellen, i mindre skrift"},
                {"id": "figurtekst", "label": "Figurtekst", "weight": 1.5,
                 "description": "Figurtekst UNDER figuren, i mindre skrift"},
                {"id": "grafer", "label": "Grafer", "weight": 1.5,
                 "description": "Uten støttelinjer og overskrifter, aksetitler med benevning"},
                {"id": "tabellformatering", "label": "Tabellformatering", "weight": 1.0,
                 "description": "Unngå tomme celler, innenfor marginer, ikke delt over sider"},
                {"id": "ligning_nummerering", "label": "Ligningsnummerering", "weight": 1.5,
                 "description": "Ligninger er nummerert og henvist til i tekst"},
                {"id": "symboler", "label": "Symbolforklaring", "weight": 1.0,
                 "description": "Symboler i ligninger er forklart"},
                {"id": "stokiometri", "label": "Støkiometrisk formatering", "weight": 0.5,
                 "description": "Støkiometriske indekser i senket skrift"},
                {"id": "radata", "label": "Rådata plassering", "weight": 1.5,
                 "description": "Rådata i vedlegg, ikke i hoveddelen"},
            ],
            "scoringRubric": "Vurder formatering av figurer, tabeller og ligninger. Sjekk at figur-/tabelltekster er korrekt plassert og at ligninger er nummerert."
        }
    },
    {
        "name": "Språksjekker",
        "description": "Sjekker språk, grammatikk og korrekt tid (del av 'Skriving og struktur')",
        "max_score": 2.0,
        "criteria": {
            "checkItems": [
                {"id": "rettskriving", "label": "Rettskriving og grammatikk", "weight": 2.0,
                 "description": "Korrekt norsk rettskriving og grammatikk"},
                {"id": "tid_sammendrag", "label": "Tid i sammendrag", "weight": 1.0,
                 "description": "Passiv fortid"},
                {"id": "tid_intro", "label": "Tid i introduksjon", "weight": 1.0,
                 "description": "Passiv fortid + nåtid for teori"},
                {"id": "tid_metode", "label": "Tid i metode", "weight": 1.0,
                 "description": "Passiv fortid"},
                {"id": "tid_resultat_diskusjon", "label": "Tid i resultat/diskusjon", "weight": 1.0,
                 "description": "Blanding tillatt, 'vi' tillatt men aldri 'jeg'"},
                {"id": "forkortelser", "label": "Forkortelser", "weight": 1.0,
                 "description": "Forklares ved første bruk"},
                {"id": "akademisk_tone", "label": "Akademisk tone", "weight": 1.5,
                 "description": "Unngå adjektiv/adverb (meget, veldig), småord (nok, vel, da), konkrete tidsangivelser"},
                {"id": "fagterminologi", "label": "Fagterminologi", "weight": 1.5,
                 "description": "Korrekt bruk av fagtermer"},
            ],
            "scoringRubric": "Vurder språklig kvalitet, korrekt bruk av tid i ulike kapitler, og akademisk tone. Trekk for 'jeg', vage formuleringer eller feil tid."
        }
    },
    {
        "name": "Sammendragssjekker",
        "description": "Sjekker sammendrag/abstract (2% av total)",
        "max_score": 2.0,
        "criteria": {
            "checkItems": [
                {"id": "lengde", "label": "Lengde", "weight": 1.5,
                 "description": "Maks halv side"},
                {"id": "hensikt", "label": "Hensikt", "weight": 1.5,
                 "description": "Formålet med forsøket er beskrevet"},
                {"id": "metoder", "label": "Metoder", "weight": 1.5,
                 "description": "Kort beskrivelse av metoder brukt"},
                {"id": "hovedresultater", "label": "Hovedresultater", "weight": 2.0,
                 "description": "De viktigste resultatene er presentert"},
                {"id": "kvalitet_feil", "label": "Kvalitet og feilkilder", "weight": 1.5,
                 "description": "Kvalitetsvurdering og feilkilder nevnt"},
                {"id": "konklusjon", "label": "Konklusjon", "weight": 1.0,
                 "description": "Kort konklusjon inkludert"},
                {"id": "selvstendig", "label": "Selvstendig lesbart", "weight": 0.5,
                 "description": "Kan leses uavhengig av resten"},
                {"id": "ingen_ref_fig", "label": "Ingen referanser/figurer", "weight": 0.5,
                 "description": "Inneholder IKKE referanser, figurer eller tabeller"},
            ],
            "scoringRubric": "Vurder om sammendraget gir et komplett bilde av forsøket på maks halv side. Trekk for referanser, figurer eller manglende elementer."
        }
    },
    {
        "name": "Innholdssjekker",
        "description": "Sjekker innhold i Introduksjon (15%), Metode (20%), Resultater (30%) og Diskusjon (20%)",
        "max_score": 85.0,
        "criteria": {
            "checkItems": [
                # Introduksjon
                {"id": "intro_hensikt", "label": "Introduksjon: Hensikt", "weight": 1.0,
                 "description": "Kort hensikt i fortid"},
                {"id": "intro_teori", "label": "Introduksjon: Bakgrunnsteori", "weight": 1.5,
                 "description": "Tilstrekkelig bakgrunnsteori og prinsipper for teknikker"},
                {"id": "intro_underkapitler", "label": "Introduksjon: Struktur", "weight": 0.5,
                 "description": "Tematiske underkapitler, ligninger oppgis fortløpende"},
                {"id": "intro_ikke_eksperiment", "label": "Introduksjon: Ikke eksperimentelt", "weight": 0.5,
                 "description": "IKKE eksperimentelle opplysninger"},
                # Metode
                {"id": "metode_materialer", "label": "Metode: Materialer", "weight": 1.5,
                 "description": "Materialer med produsentnavn, artikkelnummer, konsentrasjon"},
                {"id": "metode_utstyr", "label": "Metode: Utstyr", "weight": 1.0,
                 "description": "Utstyr med produsent og modell, instrumentinnstillinger"},
                {"id": "metode_beskrivelse", "label": "Metode: Beskrivelse", "weight": 1.5,
                 "description": "Passiv fortid, detaljert nok til å gjenta, henvisning til forsøksbeskrivelse"},
                {"id": "metode_ikke_data", "label": "Metode: Ikke bearbeidede data", "weight": 0.5,
                 "description": "IKKE bearbeidede måledata"},
                # Resultater
                {"id": "resultat_innledning", "label": "Resultater: Innledning", "weight": 0.5,
                 "description": "Innledende tekst før figurer/tabeller"},
                {"id": "resultat_kronologisk", "label": "Resultater: Kronologisk", "weight": 1.0,
                 "description": "Kronologisk presentasjon, beskrevet i tekst"},
                {"id": "resultat_ikke", "label": "Resultater: Unngå", "weight": 0.5,
                 "description": "IKKE forkastede forsøk, metodegjentagelse eller diskusjon"},
                # Diskusjon
                {"id": "diskusjon_oppsummering", "label": "Diskusjon: Oppsummering", "weight": 1.0,
                 "description": "Kort oppsummering først"},
                {"id": "diskusjon_sammenligning", "label": "Diskusjon: Sammenligning", "weight": 1.5,
                 "description": "Sammenligning med teori/litteraturverdier"},
                {"id": "diskusjon_feilkilder", "label": "Diskusjon: Feilkilder", "weight": 1.5,
                 "description": "Feilkilder identifisert og effekt diskutert"},
                {"id": "konklusjon", "label": "Konklusjon", "weight": 1.0,
                 "description": "Ble hensikten oppnådd? Usikkerhetsvurdering"},
            ],
            "scoringRubric": "Vurder innholdet i hvert hovedkapittel. Sjekk at hvert kapittel inneholder riktige elementer og unngår feil plassering av innhold."
        }
    },
    {
        "name": "Vedleggssjekker",
        "description": "Sjekker obligatoriske vedlegg og vedleggsstruktur",
        "max_score": 1.0,
        "criteria": {
            "checkItems": [
                {"id": "medforfatterbidrag", "label": "Medforfatterbidrag", "weight": 1.5,
                 "description": "Vedlagt hvis mer enn én forfatter"},
                {"id": "originalitet", "label": "Originalitetserklæring", "weight": 2.0,
                 "description": "Erklæring om at arbeidet er eget"},
                {"id": "ki_avklaring", "label": "KI-avklaring", "weight": 2.0,
                 "description": "Avklaring om bruk av KI-verktøy"},
                {"id": "innholdsfortegnelse", "label": "I innholdsfortegnelse", "weight": 0.5,
                 "description": "Vedlegg oppgitt i innholdsfortegnelsen"},
                {"id": "henvist", "label": "Henvist i tekst", "weight": 0.5,
                 "description": "Henvist til fra hovedteksten"},
                {"id": "struktur", "label": "Vedleggsstruktur", "weight": 1.0,
                 "description": "Nummerering, overskrift, forklarende tekst"},
                {"id": "nummerering", "label": "Figur/tabellnummerering", "weight": 0.5,
                 "description": "Egen nummerering (f.eks. Figur A1)"},
            ],
            "scoringRubric": "Sjekk at obligatoriske vedlegg er inkludert og at vedlegg har korrekt struktur. Originalitetserklæring og KI-avklaring er spesielt viktig."
        }
    },
    {
        "name": "Helhetsvurdering",
        "description": "Overordnet kvalitet og sammenheng",
        "max_score": 1.0,
        "criteria": {
            "checkItems": [
                {"id": "rod_trad", "label": "Rød tråd", "weight": 2.0,
                 "description": "Logisk sammenheng gjennom hele rapporten"},
                {"id": "lesbarhet", "label": "Lesbarhet", "weight": 1.5,
                 "description": "Leseren ledes gjennom trinnene på en klar måte"},
                {"id": "kapittelsammenheng", "label": "Kapittelsammenheng", "weight": 1.5,
                 "description": "Kapitler henger sammen og bygger på hverandre"},
                {"id": "profesjonelt", "label": "Profesjonelt inntrykk", "weight": 1.0,
                 "description": "Profesjonelt og vitenskapelig helhetsinntrykk"},
                {"id": "malgruppe", "label": "Målgruppe", "weight": 1.0,
                 "description": "Egnet for en leser med generelle kjemikunnskaper"},
            ],
            "scoringRubric": "Gi en helhetsvurdering av rapportens kvalitet. Vurder om rapporten fungerer som en sammenhengende vitenskapelig tekst."
        }
    },
]


def upgrade() -> None:
    conn = op.get_bind()

    # Delete agent_results first (child of evaluations AND agent_configurations)
    conn.execute(sa.text("DELETE FROM agent_results"))
    # Then delete evaluations
    conn.execute(sa.text("DELETE FROM evaluations"))
    # Delete all existing agent configurations (including non-templates)
    conn.execute(sa.text("DELETE FROM agent_configurations"))

    # Insert all 8 new agents as templates
    for agent in NEW_AGENTS:
        conn.execute(
            sa.text("""
                INSERT INTO agent_configurations (name, description, criteria, max_score, is_template, created_at)
                VALUES (:name, :description, :criteria, :max_score, true, NOW())
            """),
            {
                "name": agent["name"],
                "description": agent["description"],
                "criteria": json.dumps(agent["criteria"]),
                "max_score": agent["max_score"],
            }
        )


def downgrade() -> None:
    # This would require storing the old agents, which is complex
    # For simplicity, just delete all and note that manual re-seeding is needed
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM agent_configurations"))

    # Re-seed with original 5 templates (simplified version)
    original_agents = [
        ("Formalitetssjekker", "Sjekker formelle krav til rapporten", 10.0),
        ("Kildesjekker", "Sjekker kilder og referanser", 10.0),
        ("Figursjekker", "Sjekker figurer og tabeller", 10.0),
        ("Språksjekker", "Sjekker språk og grammatikk", 10.0),
        ("Sammendragssjekker", "Sjekker sammendrag/abstract", 10.0),
    ]
    for name, desc, score in original_agents:
        conn.execute(
            sa.text("""
                INSERT INTO agent_configurations (name, description, criteria, max_score, is_template, created_at)
                VALUES (:name, :description, '{}', :max_score, true, NOW())
            """),
            {"name": name, "description": desc, "max_score": score}
        )
