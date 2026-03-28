from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.report import Report, ReportStatus
from app.schemas.report import ReportResponse, ReportListResponse
from app.services.report_service import ReportService

router = APIRouter()


@router.post("/upload", response_model=ReportResponse)
async def upload_report(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Upload a new report (PDF or Word document)."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Validate file type
    allowed_extensions = {".pdf", ".docx", ".doc"}
    file_ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed: {', '.join(allowed_extensions)}",
        )

    # Use filename as title if not provided
    if not title:
        title = file.filename.rsplit(".", 1)[0]

    service = ReportService(db)
    report = await service.create_report(file, title)
    return report


@router.get("", response_model=list[ReportListResponse])
def list_reports(db: Session = Depends(get_db)):
    """List all reports."""
    reports = db.query(Report).order_by(Report.created_at.desc()).all()
    return reports


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(report_id: int, db: Session = Depends(get_db)):
    """Get a specific report by ID."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.delete("/{report_id}")
def delete_report(report_id: int, db: Session = Depends(get_db)):
    """Delete a report."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    service = ReportService(db)
    service.delete_report(report)
    return {"message": "Report deleted"}
