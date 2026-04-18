# ReportChecker

AI-assistert vurdering og anonymisering av labrapporter i bioteknologi og biokjemi.

## Funksjoner

- Last opp PDF-rapporter for evaluering
- **Anonymisering:** søk-og-erstatt navn/initialer gjennom hele rapporten, persistent kandidatnummer per student på tvers av rapporter
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
- PDF-eksport av evalueringsresultater
- Magic link-innlogging (ingen passord)

## Teknisk stack

- **Frontend:** Next.js 14, TypeScript, Tailwind CSS
- **Backend:** Python FastAPI
- **Database:** PostgreSQL
- **Fillagring:** MinIO (S3-kompatibel)
- **Oppgavekø:** Redis + Celery
- **AI:** Claude API (Anthropic)

---

## Utviklingsoppsett

### Forutsetninger

- Docker og Docker Compose
- Node.js 20+
- En Anthropic API-nøkkel

### 1. Konfigurer miljøvariabler

```bash
cp .env.example .env.docker
```

Rediger `.env.docker` og legg inn nødvendige verdier:

```
ANTHROPIC_API_KEY=sk-ant-...
ADMIN_EMAIL=din@epost.no
```

### 2. Start alle tjenester

```bash
docker compose --env-file .env.docker up -d
```

Backend kjører på port 8000. Migrasjoner kjøres manuelt første gang:

```bash
docker exec reportchecker-backend alembic upgrade head
```

### 3. Start frontend

```bash
cd frontend
npm install
npm run dev
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs

### Innlogging

Appen bruker magic link-innlogging. Admin-brukeren opprettes automatisk fra `ADMIN_EMAIL` ved oppstart. Magic link printes til backend-loggene når SMTP ikke er konfigurert:

```bash
docker logs reportchecker-backend | grep "MAGIC LINK"
```

**Merk:** Utviklingsmiljøet bruker `network_mode: host` og PostgreSQL på port 5433 (for å unngå kollisjon med eventuelle lokale postgres-instanser).

---

## Anonymiseringsflyt

1. Last opp PDF → appen ekstraherer navn og initialer som forslag
2. Hvert navn får et fast 6-sifret kandidatnummer (samme navn → samme nummer alltid)
3. Bruker verifiserer/korrigerer tabellen og legger til eventuelle navn-varianter (kommaseparert)
4. Appen gjør søk-og-erstatt gjennom hele PDF-en og genererer ny anonymisert forside
5. Last ned anonymisert PDF og mapping-fil (navn ↔ kandidatnummer)

**Begrensninger:** Tekst som er brutt over linjer eller ligger i scannede bilder erstattes ikke.

---

## Bruk

1. Åpne http://localhost:3000 og logg inn
2. Klikk **"Last opp rapport"** og velg en PDF
3. Gå gjennom anonymiseringssteget og last ned anonymisert PDF
4. Klikk **"Start evaluering"** på rapporten
5. Se detaljerte resultater med score og tilbakemelding per kriterie

---

## Kodestruktur

```
reportchecker/
├── frontend/                        # Next.js app
│   └── src/
│       ├── app/                     # Sider (Next.js App Router)
│       │   ├── reports/upload/      # Opplasting
│       │   ├── reports/[id]/        # Rapport + evaluering
│       │   ├── reports/[id]/anonymize/  # Anonymisering
│       │   ├── agents/              # Agent-konfigurasjon
│       │   ├── login/               # Innlogging
│       │   └── auth/verify/         # Magic link-verifisering
│       └── lib/api.ts               # API-klient med cookie-håndtering
├── backend/                         # FastAPI app
│   ├── app/
│   │   ├── api/routes/              # API-endepunkter
│   │   ├── models/                  # Database-modeller
│   │   ├── services/                # Forretningslogikk
│   │   ├── document_processing/     # PDF-ekstraksjon og anonymisering
│   │   └── core/                    # Auth, database, storage
│   └── alembic/versions/            # Databasemigrasjoner
├── docker-compose.yml               # Utviklingsmiljø
└── .env.docker.example              # Mal for miljøvariabler
```

## Lisens

Privat bruk.
