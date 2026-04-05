"""Scale criteria weights to sum to 100 per agent

All agents now use criteria weights that sum to 100. Claude scores each
criterion 0-weight and the total sums to 0-100 per agent.
Backend converts: contribution = (score / 100) * agent.max_score.

Revision ID: 010
Revises: 009
Create Date: 2026-04-05
"""
import json
from alembic import op
import sqlalchemy as sa


revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


UPDATED_AGENTS = [
    {
        "name": "Formalitetssjekker",
        "criteria": {
            "checkItems": [
                {"id": "tittelside", "label": "Tittelside", "weight": 20,
                 "description": "Egen side (unummerert) med tittel, kandidatnummer, oppgave, dato, emne, institusjon"},
                {"id": "innholdsfortegnelse", "label": "Innholdsfortegnelse", "weight": 15,
                 "description": "Egen side (unummerert)"},
                {"id": "sammendrag_plassering", "label": "Sammendrag-plassering", "weight": 10,
                 "description": "Sammendrag på egen side, sidenummerering starter her"},
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
        "criteria": {
            "checkItems": [
                {"id": "egenprodusert", "label": "Egenprodusert tekst", "weight": 25,
                 "description": "Teksten er skrevet med egne ord, ikke kopiert"},
                {"id": "tillatte_kilder", "label": "Tillatte kilder", "weight": 15,
                 "description": "Bruker lærebok, vitenskapelige artikler, offentlige nettsider"},
                {"id": "ikke_tillatte", "label": "Unngår ikke-tillatte kilder", "weight": 15,
                 "description": "Unngår Wikipedia, forelesningsnotater, Canvas-teori (unntak: forsøksbeskrivelse)"},
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
        "criteria": {
            "checkItems": [
                # Introduksjon: sum = 18 (proporsjonalt til 15% av 85, skalert til 100)
                {"id": "intro_hensikt", "label": "Introduksjon: Hensikt", "weight": 5,
                 "description": "Kort hensikt i fortid"},
                {"id": "intro_teori", "label": "Introduksjon: Bakgrunnsteori", "weight": 8,
                 "description": "Tilstrekkelig bakgrunnsteori og prinsipper for teknikker"},
                {"id": "intro_underkapitler", "label": "Introduksjon: Struktur", "weight": 3,
                 "description": "Tematiske underkapitler, ligninger oppgis fortløpende"},
                {"id": "intro_ikke_eksperiment", "label": "Introduksjon: Ikke eksperimentelt", "weight": 2,
                 "description": "IKKE eksperimentelle opplysninger"},
                # Metode: sum = 24 (proporsjonalt til 20% av 85, skalert til 100)
                {"id": "metode_materialer", "label": "Metode: Materialer", "weight": 8,
                 "description": "Materialer med produsentnavn, artikkelnummer, konsentrasjon"},
                {"id": "metode_utstyr", "label": "Metode: Utstyr", "weight": 5,
                 "description": "Utstyr med produsent og modell, instrumentinnstillinger"},
                {"id": "metode_beskrivelse", "label": "Metode: Beskrivelse", "weight": 8,
                 "description": "Passiv fortid, detaljert nok til å gjenta, henvisning til forsøksbeskrivelse"},
                {"id": "metode_ikke_data", "label": "Metode: Ikke bearbeidede data", "weight": 3,
                 "description": "IKKE bearbeidede måledata"},
                # Resultater: sum = 35 (proporsjonalt til 30% av 85, skalert til 100)
                {"id": "resultat_innledning", "label": "Resultater: Innledning", "weight": 9,
                 "description": "Innledende tekst før figurer/tabeller"},
                {"id": "resultat_kronologisk", "label": "Resultater: Kronologisk", "weight": 17,
                 "description": "Kronologisk presentasjon, beskrevet i tekst"},
                {"id": "resultat_ikke", "label": "Resultater: Unngå", "weight": 9,
                 "description": "IKKE forkastede forsøk, metodegjentagelse eller diskusjon"},
                # Diskusjon og konklusjon: sum = 23 (proporsjonalt til 20% av 85, skalert til 100)
                {"id": "diskusjon_oppsummering", "label": "Diskusjon: Oppsummering", "weight": 5,
                 "description": "Kort oppsummering først"},
                {"id": "diskusjon_sammenligning", "label": "Diskusjon: Sammenligning", "weight": 7,
                 "description": "Sammenligning med teori/litteraturverdier"},
                {"id": "diskusjon_feilkilder", "label": "Diskusjon: Feilkilder", "weight": 7,
                 "description": "Feilkilder identifisert og effekt diskutert"},
                {"id": "konklusjon", "label": "Konklusjon", "weight": 4,
                 "description": "Ble hensikten oppnådd? Usikkerhetsvurdering"},
            ],
            # Vektfordelingen: Introduksjon=18, Metode=24, Resultater=35, Diskusjon+Konklusjon=23 (sum=100)
            # Tilsvarer opprinnelig: Intro 15%, Metode 20%, Resultater 30%, Diskusjon 20% av 85%
            "scoringRubric": "Vurder innholdet i hvert hovedkapittel. Total score 0-100 (Introduksjon maks 18, Metode maks 24, Resultater maks 35, Diskusjon+Konklusjon maks 23). Sjekk at hvert kapittel inneholder riktige elementer og unngår feil plassering av innhold."
        }
    },
    {
        "name": "Helhetsvurdering",
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
    conn = op.get_bind()
    for agent in UPDATED_AGENTS:
        conn.execute(
            sa.text("UPDATE agent_configurations SET criteria = :criteria WHERE name = :name"),
            {"criteria": json.dumps(agent["criteria"]), "name": agent["name"]}
        )


def downgrade() -> None:
    # Criteria from migration 006 (original weights)
    pass
