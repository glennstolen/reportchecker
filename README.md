# ReportChecker

AI-assistert vurdering av labrapporter for universitetsforelesere.

## Funksjoner

- Last opp PDF/Word-rapporter
- Konfigurerbare AI-agenter som sjekker ulike aspekter:
  - Formaliteter (struktur, tittelside, sidetall)
  - Kildereferanser (format, in-text citations)
  - Figurer og tabeller (tekster, kvalitet)
  - Språk og grammatikk
  - Sammendrag/abstract
- Parallell evaluering med flere agenter
- Detaljert tilbakemelding per kriterie

## Teknisk stack

- **Frontend:** Next.js 14, TypeScript, Tailwind CSS
- **Backend:** Python FastAPI
- **Database:** PostgreSQL
- **Fillagring:** MinIO (S3-kompatibel)
- **AI:** Claude API (Anthropic)

## Oppsett

### Forutsetninger

- Docker og Docker Compose
- Node.js 18+
- En Anthropic API-nøkkel

### 1. Konfigurer miljøvariabler

```bash
cp .env.example .env
```

Rediger `.env` og legg inn din Anthropic API-nøkkel:

```
ANTHROPIC_API_KEY=din_api_nøkkel_her
```

### 2. Start infrastruktur (database, Redis, MinIO)

```bash
docker compose up -d db redis minio
```

### 3. Kjør database-migrasjoner

```bash
cd backend
python -m venv venv
source venv/bin/activate  # På Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
```

### 4. Start backend

```bash
# Fortsatt i backend-mappen med venv aktivert
uvicorn app.main:app --reload
```

Backend kjører nå på http://localhost:8000

### 5. Start frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend kjører nå på http://localhost:3000

## Alternativ: Kjør alt med Docker

```bash
docker compose up -d
```

Dette starter alle tjenester. Frontend på port 3000, backend på port 8000.

## Bruk

1. Åpne http://localhost:3000
2. Klikk "Last opp rapport" og velg en PDF eller Word-fil
3. Vent til rapporten er prosessert (status: "Klar")
4. Velg hvilke agenter som skal evaluere rapporten
5. Klikk "Start evaluering"
6. Se detaljerte resultater med score og tilbakemelding

## Agent-konfigurasjon

Du kan lage egne agenter under "Agenter"-fanen:

1. Klikk "Ny agent"
2. Gi agenten et navn og beskrivelse
3. Legg til evalueringskriterier med vekt
4. Skriv eventuelt en vurderingsmal

Eller dupliser en av de ferdiglagde templates og tilpass den.

## API-dokumentasjon

Swagger UI: http://localhost:8000/docs

### Hovedendepunkter

- `POST /api/reports/upload` - Last opp rapport
- `GET /api/reports` - Liste rapporter
- `POST /api/agents` - Opprett agent
- `GET /api/agents` - Liste agenter
- `POST /api/evaluations` - Start evaluering
- `GET /api/evaluations/{id}` - Hent resultater

## Utvikling

### Backend-tester

```bash
cd backend
pytest
```

### Kodestruktur

```
reportchecker/
├── frontend/          # Next.js app
│   └── src/
│       ├── app/       # Sider
│       ├── components/# React-komponenter
│       └── types/     # TypeScript-typer
├── backend/           # FastAPI app
│   ├── app/
│   │   ├── api/       # API-ruter
│   │   ├── models/    # Database-modeller
│   │   ├── services/  # Forretningslogikk
│   │   └── ai/        # AI-evaluering
│   └── alembic/       # Migrasjoner
└── docker-compose.yml
```

## Lisens

Privat bruk.
