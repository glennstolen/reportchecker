from sqlalchemy.orm import Session

from app.models.candidate_registry import CandidateRegistry
from app.document_processing.pdf_anonymizer import generate_candidate_number


def get_or_create_candidate_number(db: Session, name: str) -> str:
    """Return existing candidate number for name, or create a new one."""
    normalized = name.strip().lower()
    existing = db.query(CandidateRegistry).filter_by(name_normalized=normalized).first()
    if existing:
        return existing.candidate_number

    used = {r for (r,) in db.query(CandidateRegistry.candidate_number).all()}
    number = generate_candidate_number(existing=used)
    db.add(CandidateRegistry(name_normalized=normalized, candidate_number=number))
    db.commit()
    return number
