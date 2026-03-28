-- Create enums
DO $$ BEGIN
    CREATE TYPE reportstatus AS ENUM ('UPLOADED', 'PROCESSING', 'READY', 'ERROR');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE evaluationstatus AS ENUM ('PENDING', 'RUNNING', 'COMPLETED', 'ERROR');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'lecturer',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Reports table
CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    title VARCHAR(500) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    content_text TEXT,
    status reportstatus DEFAULT 'UPLOADED',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent configurations table
CREATE TABLE IF NOT EXISTS agent_configurations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    criteria JSONB DEFAULT '{}',
    max_score FLOAT DEFAULT 10.0,
    prompt_template TEXT,
    is_template BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Evaluations table
CREATE TABLE IF NOT EXISTS evaluations (
    id SERIAL PRIMARY KEY,
    report_id INTEGER NOT NULL REFERENCES reports(id),
    user_id INTEGER REFERENCES users(id),
    status evaluationstatus DEFAULT 'PENDING',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    total_score FLOAT,
    max_possible_score FLOAT,
    summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent results table
CREATE TABLE IF NOT EXISTS agent_results (
    id SERIAL PRIMARY KEY,
    evaluation_id INTEGER NOT NULL REFERENCES evaluations(id),
    agent_config_id INTEGER NOT NULL REFERENCES agent_configurations(id),
    score FLOAT,
    max_score FLOAT,
    feedback TEXT,
    details JSONB,
    status evaluationstatus DEFAULT 'PENDING',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Update alembic version
DELETE FROM alembic_version;
INSERT INTO alembic_version (version_num) VALUES ('001');

-- Seed agent templates
INSERT INTO agent_configurations (name, description, criteria, max_score, is_template) VALUES
('Formalitetssjekker', 'Sjekker at rapporten har korrekt struktur og formaliteter',
 '{"checkItems": [{"id": "title_page", "label": "Tittelside med alle nødvendige elementer", "weight": 1.0, "description": "Tittel, forfatternavn, dato, institutt/emne"}, {"id": "structure", "label": "Korrekt seksjonsstruktur", "weight": 2.0, "description": "Sammendrag, Introduksjon, Metode, Resultater, Diskusjon, Konklusjon"}, {"id": "page_numbers", "label": "Sidetall på alle sider", "weight": 0.5}, {"id": "font_formatting", "label": "Konsistent formatering", "weight": 0.5, "description": "Lesbar font, passende størrelse, god lesbarhet"}, {"id": "length", "label": "Passende lengde", "weight": 1.0, "description": "Ikke for kort eller for lang for oppgavens omfang"}], "scoringRubric": "0-2 poeng per kriterie basert på hvor godt det er oppfylt. Trekk for manglende elementer."}',
 10.0, true),

('Kildesjekker', 'Evaluerer bruk av kilder og referanser',
 '{"checkItems": [{"id": "citation_format", "label": "Korrekt referanseformat", "weight": 2.0, "description": "Konsistent bruk av APA, Vancouver eller annet format"}, {"id": "in_text", "label": "Korrekte in-text referanser", "weight": 2.0, "description": "Alle påstander støttes av referanser der det trengs"}, {"id": "reference_list", "label": "Komplett referanseliste", "weight": 1.5, "description": "Alle siterte kilder er listet"}, {"id": "source_quality", "label": "Kvalitet på kilder", "weight": 2.0, "description": "Vitenskapelige, fagfellevurderte kilder prioritert"}, {"id": "source_quantity", "label": "Tilstrekkelig antall kilder", "weight": 1.0}], "scoringRubric": "Vurder kvalitet og konsistens i referansebruk. Fullt poeng krever feilfri referansebruk."}',
 10.0, true),

('Figursjekker', 'Evaluerer kvalitet på figurer, tabeller og visualiseringer',
 '{"checkItems": [{"id": "figure_captions", "label": "Beskrivende figurtekster", "weight": 2.0, "description": "Alle figurer har informative undertekster"}, {"id": "table_captions", "label": "Beskrivende tabelltekster", "weight": 2.0, "description": "Alle tabeller har informative overskrifter"}, {"id": "references_in_text", "label": "Referanser til figurer i tekst", "weight": 1.5, "description": "Alle figurer og tabeller omtales i teksten"}, {"id": "quality", "label": "Visuell kvalitet", "weight": 1.5, "description": "Lesbare akser, tydelige labels, god oppløsning"}, {"id": "relevance", "label": "Relevante visualiseringer", "weight": 1.5, "description": "Figurene støtter og illustrerer poengene i teksten"}], "scoringRubric": "Vurder om figurer og tabeller er profesjonelle og støtter rapporten."}',
 10.0, true),

('Språksjekker', 'Evaluerer språk, grammatikk og fagterminologi',
 '{"checkItems": [{"id": "spelling", "label": "Rettskriving", "weight": 2.0, "description": "Ingen eller svært få skrivefeil"}, {"id": "grammar", "label": "Grammatikk", "weight": 2.0, "description": "Korrekt setningsbygging og grammatikk"}, {"id": "terminology", "label": "Fagterminologi", "weight": 2.0, "description": "Korrekt bruk av faglige begreper"}, {"id": "clarity", "label": "Klarhet og presisjon", "weight": 2.0, "description": "Tydelig og presis formulering"}, {"id": "academic_tone", "label": "Akademisk tone", "weight": 1.5, "description": "Passende formelt og objektivt språk"}], "scoringRubric": "Trekk for gjentatte feil. Fullt poeng krever profesjonelt akademisk språk."}',
 10.0, true),

('Sammendragssjekker', 'Evaluerer kvaliteten på sammendraget/abstract',
 '{"checkItems": [{"id": "length", "label": "Passende lengde (150-300 ord)", "weight": 1.0}, {"id": "background", "label": "Kort bakgrunn/kontekst", "weight": 1.5, "description": "Hvorfor er dette viktig?"}, {"id": "objective", "label": "Tydelig formål/problemstilling", "weight": 2.0}, {"id": "methods", "label": "Kort metodebeskrivelse", "weight": 1.5}, {"id": "results", "label": "Hovedresultater nevnt", "weight": 2.0}, {"id": "conclusion", "label": "Hovedkonklusjon", "weight": 1.5}], "scoringRubric": "Et godt sammendrag gir leseren full oversikt over rapporten uten å lese resten."}',
 10.0, true);
