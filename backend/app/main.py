from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import reports, agents, evaluations, auth
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="ReportChecker API",
    description="AI-assistert vurdering av labrapporter",
    version="0.1.0",
)

# CORS — origins configured via ALLOWED_ORIGINS env var
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(evaluations.router, prefix="/api/evaluations", tags=["evaluations"])



@app.on_event("startup")
async def seed_admin_user():
    """Create admin user from ADMIN_EMAIL env var if not already present."""
    import os
    from app.core.database import SessionLocal
    from app.models.user import User

    admin_email = os.environ.get("ADMIN_EMAIL", "")
    if not admin_email:
        return
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == admin_email).first()
        if not existing:
            db.add(User(email=admin_email, is_active=True))
            db.commit()
            print(f"Admin-bruker opprettet ved oppstart: {admin_email}")
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "ReportChecker API", "version": "0.1.0"}


@app.get("/health")
def health():
    return {"status": "ok"}
