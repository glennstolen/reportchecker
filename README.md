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
- **Instruktøroverstyring:** foreleser kan korrigere score og legge til kommentar per sjekker – både AI-score og instruktørscore vises
- PDF-eksport av evalueringsresultater (inkl. instruktøroverstyringer)
- Eksport av vurderingskriterier som PDF
- Magic link-innlogging (ingen passord)
- Last ned global kandidatnummer-mapping som CSV

## Teknisk stack

- **Frontend:** Next.js 14, TypeScript, Tailwind CSS
- **Backend:** Python FastAPI
- **Database:** PostgreSQL
- **Fillagring:** MinIO (S3-kompatibel)
- **Oppgavekø:** Redis + Celery
- **AI:** Claude API (Anthropic)

---

## Produksjonsoppsett (Hetzner / VPS)

### Forutsetninger

- En Hetzner-konto (hetzner.com)
- En SSH-nøkkel registrert i Hetzner
- En Anthropic API-nøkkel

### 0. Opprett server i Hetzner

1. Gå til **Hetzner Cloud Console → Projects → Add Server**
2. Velg: Location = Helsinki, Image = **Ubuntu 24.04**, Type = **CX22** (~4 EUR/mnd)
3. Under **SSH keys**: legg til din offentlige nøkkel (generer med `ssh-keygen -t ed25519` om du ikke har en)
4. Opprett serveren og noter IP-adressen

**Installer Docker på serveren:**

```bash
ssh root@<SERVER-IP>
curl -fsSL https://get.docker.com | sh
```

**Brannmur i Hetzner Console:**

Gå til **Firewalls → Create Firewall** og tillat kun innkommende trafikk på:
- Port 22 (SSH)
- Port 80 (HTTP)
- Port 443 (HTTPS)

Koble brannmuren til serveren under **Resources**-fanen.

### 1. Hent kodebasen

```bash
git clone https://github.com/glennstolen/reportchecker /opt/reportchecker
cd /opt/reportchecker
```

### 2. Konfigurer miljøvariabler

```bash
cp .env.docker.example .env
```

Rediger `.env` og fyll inn alle verdier:

```
ANTHROPIC_API_KEY=sk-ant-...
ADMIN_EMAIL=din@epost.no
DOMAIN=reportchecker.no   
APP_URL=http://reportchecker.no 
POSTGRES_PASSWORD=sterkt_passord
MINIO_ACCESS_KEY=bruker
MINIO_SECRET_KEY=sterkt_passord
JWT_SECRET=lang_tilfeldig_streng # generer med: openssl rand -hex 32

# E-post (Brevo) — se eget avsnitt nedenfor
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USER=din@epost.no
SMTP_PASSWORD=xsmtpsib-...
SMTP_FROM=din@epost.no
```

### 3. Start alle tjenester

```bash
docker compose -f docker-compose.prod.yml up -d
```

Docker-images hentes automatisk fra GHCR. Backend kjører `alembic upgrade head` og oppretter admin-bruker fra `ADMIN_EMAIL` ved første oppstart.

### 4. Brannmur

Åpne kun port 22 (SSH), 80 (HTTP) og 443 (HTTPS). Alle andre porter (3000, 8000, 5432 osv.) skal være stengt – all trafikk rutes gjennom Caddy.

### 5. E-post med magic link (Brevo)

Uten SMTP-konfigurasjon printes innloggingslenken kun i backend-loggen:

```bash
docker logs reportchecker-backend 2>&1 | grep "MAGIC LINK"
```

For å aktivere e-postutsending via Brevo:

1. Opprett gratis konto på [brevo.com](https://www.brevo.com) (ingen kredittkort)
2. Gå til **SMTP & API → SMTP** og generer en SMTP-nøkkel
3. Gå til **Senders & IP → Senders** og verifiser avsenderadressen din (kan være en Gmail-adresse)
4. Legg til i `.env` på serveren:
   ```
   SMTP_HOST=smtp-relay.brevo.com
   SMTP_PORT=587
   SMTP_USER=din@epost.no       # Brevo-innloggingsepost
   SMTP_PASSWORD=xsmtpsib-...   # SMTP-nøkkel fra Brevo
   SMTP_FROM=din@epost.no       # må være verifisert i Brevo
   ```
5. Restart backend:
   ```bash
   docker compose -f docker-compose.prod.yml up -d backend
   ```

### 6. Innlogging

Gå til appens URL og skriv inn e-postadressen registrert som `ADMIN_EMAIL`. Du mottar en magic link på e-post (eller i loggen om SMTP ikke er satt opp). Lenken er gyldig i 15 minutter.

---

## Utviklingsoppsett

### Forutsetninger

- Docker og Docker Compose
- Node.js 20+
- En Anthropic API-nøkkel

### 1. Konfigurer miljøvariabler

```bash
cp .env.docker.example .env.docker
```

Rediger `.env.docker`:

```
ANTHROPIC_API_KEY=sk-ant-...
ADMIN_EMAIL=din@epost.no
```

### 2. Start alle tjenester

```bash
docker compose --env-file .env.docker up -d
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

Magic link printes i backend-loggen:

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
5. Last ned anonymisert PDF fra rapportlisten

**Begrensninger:** Tekst som er brutt over linjer eller ligger i scannede bilder erstattes ikke.

---

## Instruktøroverstyring

Etter at en AI-evaluering er gjennomført kan foreleser justere vurderingen:

1. Åpne en ferdig evaluert rapport og klikk blyant-ikonet på en sjekker
2. Skriv inn ny score (0–100, samme skala som AI) og/eller en kommentar
3. Lagre – instruktørscoren beregnes automatisk som ny vektet totalscore
4. Begge totalscore (AI og instruktør) vises side om side med egne progressbarer
5. Instruktørdata inkluderes i PDF-eksporten av evalueringsrapporten

---

## Bruk

1. Åpne appens URL og logg inn via magic link
2. Klikk **"Last opp rapport"** og velg en PDF
3. Gå gjennom anonymiseringssteget
4. Klikk **"Start evaluering"** på rapporten
5. Se detaljerte resultater med score og tilbakemelding per kriterie
6. Korriger eventuelt score/kommentar per sjekker med blyant-ikonet
7. Last ned evalueringsrapport (PDF) eller kandidatnummer-mapping (CSV) fra rapportlisten

---

## Kodestruktur

```
reportchecker/
├── frontend/                        # Next.js app
│   └── src/
│       ├── app/                     # Sider (Next.js App Router)
│       │   ├── reports/             # Rapportliste
│       │   ├── reports/upload/      # Opplasting
│       │   ├── reports/[id]/        # Rapport + evaluering + instruktøroverstyring
│       │   ├── reports/[id]/anonymize/  # Anonymisering
│       │   ├── agents/              # Agent-konfigurasjon
│       │   ├── login/               # Innlogging
│       │   └── auth/verify/         # Magic link-verifisering
│       └── lib/api.ts               # API-klient med cookie-håndtering
├── backend/                         # FastAPI app
│   ├── app/
│   │   ├── api/routes/              # API-endepunkter
│   │   ├── models/                  # Database-modeller
│   │   ├── schemas/                 # Pydantic-skjemaer
│   │   ├── services/                # Forretningslogikk
│   │   ├── document_processing/     # PDF-ekstraksjon og anonymisering
│   │   └── core/                    # Auth, database, storage
│   └── alembic/versions/            # Databasemigrasjoner
├── docker-compose.yml               # Utviklingsmiljø
├── docker-compose.prod.yml          # Produksjonsmiljø
├── Caddyfile                        # Reverse proxy-konfigurasjon
└── .env.docker.example              # Mal for miljøvariabler
```

## Lisens

Privat bruk.
