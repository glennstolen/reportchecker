# ReportChecker

AI-assistert vurdering av labrapporter i bioteknologi og biokjemi.

## Funksjoner

- Last opp PDF- eller Word-rapporter
- 7 forhåndskonfigurerte sjekkere som evaluerer ulike aspekter:
  - **Formalitetssjekker** – tittelside, innholdsfortegnelse, kapittelstruktur (3%)
  - **Kildesjekker** – kildebruk, referansestil, in-text-referanser (3%)
  - **Figur-, tabell- og ligningssjekker** – tekster, grafer, ligningsnummerering (2%)
  - **Språksjekker** – grammatikk, tidsbruk, akademisk tone (2%)
  - **Sammendragssjekker** – innhold, lengde, struktur (2%)
  - **Innholdssjekker** – faglig innhold i alle kapitler (85%)
  - **Helhetsvurdering** – rød tråd, lesbarhet, profesjonelt inntrykk (3%)
- Parallell evaluering med live framdriftsvising
- Score per kriterie med detaljert tilbakemelding
- Anonymisering av rapporter (fjern navn, behold kandidatnummer)
- PDF-eksport av evalueringsresultater

## Teknisk stack

- **Frontend:** Next.js 14, TypeScript, Tailwind CSS
- **Backend:** Python FastAPI
- **Database:** PostgreSQL
- **Fillagring:** MinIO (S3-kompatibel)
- **Oppgavekø:** Redis + Celery
- **AI:** Claude API (Anthropic)

---

## Installasjon for sluttbrukere (Windows)

### Forutsetninger

- [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) installert og startet
- En [Anthropic API-nøkkel](https://console.anthropic.com/)

### Steg

1. Last ned `ReportChecker-Setup.exe` fra [siste release](../../releases/latest)
2. Kjør installasjonsfilen og følg veiviseren
3. Oppgi Anthropic API-nøkkel når du blir bedt om det
4. Klikk **"Start ReportChecker"** på skrivebordet

**NB:** Første oppstart tar noen minutter mens Docker laster ned nødvendige komponenter (~1 GB).

Appen åpnes automatisk i nettleseren på `http://localhost:3000`.

---

## Utviklingsoppsett

### Forutsetninger

- Docker og Docker Compose
- Python 3.12+ med venv
- Node.js 20+
- En Anthropic API-nøkkel

### 1. Konfigurer miljøvariabler

```bash
cp .env.example .env
```

Rediger `.env` og legg inn din Anthropic API-nøkkel:

```
ANTHROPIC_API_KEY=sk-ant-...
```

### 2. Start tjenester og kjør migrasjoner

```bash
docker compose up -d db redis minio

cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
```

### 3. Start backend og frontend

```bash
# Terminal 1 – backend (fra backend/ med venv aktivert)
uvicorn app.main:app --reload

# Terminal 2 – frontend (fra frontend/)
npm install
npm run dev
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs

### Alternativ: Kjør alt med Docker (Linux)

```bash
docker compose up -d
```

---

## Bruk

1. Åpne http://localhost:3000
2. Klikk **"Last opp rapport"** og velg en PDF eller Word-fil
3. Vent til rapporten er prosessert (status: "Klar")
4. Klikk **"Start evaluering"**
5. Se detaljerte resultater med score og tilbakemelding per kriterie

---

## Lage en ny release (Windows-installer)

Når du er klar til å distribuere en ny versjon:

```bash
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actions bygger da automatisk:
1. Backend-image (`Dockerfile.prod`) og frontend-image pushet til `ghcr.io`
2. `ReportChecker-Setup.exe` via Inno Setup på Windows-runner
3. Installer-filen lastes opp som asset på GitHub Release-siden

Brukere laster ned `.exe`-filen fra [Releases](../../releases).

---

## Kodestruktur

```
reportchecker/
├── frontend/                  # Next.js app
│   ├── Dockerfile             # Produksjons-image
│   └── src/
│       ├── app/               # Sider (Next.js App Router)
│       ├── components/        # React-komponenter
│       └── types/             # TypeScript-typer
├── backend/                   # FastAPI app
│   ├── Dockerfile             # Utviklings-image (med corp-certs)
│   ├── Dockerfile.prod        # Produksjons-image (uten corp-certs)
│   ├── app/
│   │   ├── api/               # API-ruter
│   │   ├── models/            # Database-modeller
│   │   ├── services/          # Forretningslogikk
│   │   └── ai/                # Claude-evaluering
│   └── alembic/               # Databasemigrasjoner
├── installer/                 # Windows-installer
│   ├── reportchecker.iss      # Inno Setup-script
│   ├── start.bat              # Starter alle tjenester
│   └── stop.bat               # Stopper alle tjenester
├── docker-compose.yml         # Utviklingsmiljø (Linux, network_mode: host)
├── docker-compose.prod.yml    # Produksjonsmiljø (Windows-kompatibel)
└── .github/workflows/
    └── build-release.yml      # Bygger images + installer ved tagging
```

## Lisens

Privat bruk.
