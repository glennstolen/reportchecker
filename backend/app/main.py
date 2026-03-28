from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import reports, agents, evaluations
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="ReportChecker API",
    description="AI-assistert vurdering av labrapporter",
    version="0.1.0",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(evaluations.router, prefix="/api/evaluations", tags=["evaluations"])


@app.get("/")
def root():
    return {"message": "ReportChecker API", "version": "0.1.0"}


@app.get("/health")
def health():
    return {"status": "ok"}
