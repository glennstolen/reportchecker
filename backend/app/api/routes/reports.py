import re
from io import BytesIO
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from app.core.database import get_db
from app.core.storage import StorageClient
from app.models.report import Report, ReportStatus
from app.models.evaluation import EvaluationStatus
from app.schemas.report import (
    ReportResponse,
    ReportListResponse,
    AnonymizeRequest,
    AnonymizeResponse,
    AuthorMappingResponse,
)
from app.services.report_service import ReportService
from app.document_processing.pdf_anonymizer import anonymize_pdf, extract_report_info
from app.document_processing.text_extractor import extract_text_from_pdf, extract_metadata_from_text

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
    """List all reports with latest evaluation scores."""
    reports = db.query(Report).order_by(Report.created_at.desc()).all()

    result = []
    for report in reports:
        # Get latest completed evaluation
        latest_eval = None
        if report.evaluations:
            completed_evals = [e for e in report.evaluations if e.status.value == "completed"]
            if completed_evals:
                latest_eval = max(completed_evals, key=lambda e: e.created_at)

        result.append(ReportListResponse(
            id=report.id,
            title=report.title,
            filename=report.filename,
            status=report.status.value,
            created_at=report.created_at,
            kandidater=report.kandidater,
            oppgave=report.oppgave,
            innleveringsdato=report.innleveringsdato,
            latest_score=latest_eval.total_score if latest_eval else None,
            latest_max_score=latest_eval.max_possible_score if latest_eval else None,
            is_anonymized=report.anonymized_file_path is not None,
        ))

    return result


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(report_id: int, db: Session = Depends(get_db)):
    """Get a specific report by ID."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/{report_id}/export-pdf")
def export_report_pdf(report_id: int, db: Session = Depends(get_db)):
    """Export report evaluation results as PDF."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Get completed evaluations
    completed_evals = [e for e in report.evaluations if e.status == EvaluationStatus.COMPLETED]
    if not completed_evals:
        raise HTTPException(status_code=400, detail="No completed evaluations to export")

    # Get latest evaluation
    latest_eval = max(completed_evals, key=lambda e: e.created_at)

    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, spaceAfter=20)
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, spaceAfter=10, spaceBefore=15)
    normal_style = styles['Normal']
    feedback_style = ParagraphStyle('Feedback', parent=styles['Normal'], fontSize=10, textColor=colors.grey)

    elements = []

    # Title
    elements.append(Paragraph(f"Evalueringsrapport: {report.title}", title_style))
    elements.append(Paragraph(f"Fil: {report.filename}", normal_style))
    elements.append(Paragraph(f"Evaluert: {latest_eval.completed_at.strftime('%d.%m.%Y %H:%M') if latest_eval.completed_at else 'N/A'}", normal_style))
    elements.append(Spacer(1, 0.5*cm))

    # Total score
    if latest_eval.total_score is not None:
        score_pct = (latest_eval.total_score / latest_eval.max_possible_score * 100) if latest_eval.max_possible_score else 0
        elements.append(Paragraph(f"<b>Total score: {latest_eval.total_score:.1f} / {latest_eval.max_possible_score:.1f} ({score_pct:.0f}%)</b>", heading_style))
    elements.append(Spacer(1, 0.5*cm))

    # Agent results
    for result in latest_eval.agent_results:
        if result.status != EvaluationStatus.COMPLETED:
            continue

        agent_name = result.agent_configuration.name
        agent_desc = result.agent_configuration.description or ""

        elements.append(Paragraph(f"{agent_name}", heading_style))
        elements.append(Paragraph(agent_desc, feedback_style))

        if result.score is not None:
            elements.append(Paragraph(f"Score: {result.score:.1f} / {result.max_score:.1f}", normal_style))

        if result.feedback:
            elements.append(Paragraph(f"Tilbakemelding: {result.feedback}", normal_style))

        # Details table
        if result.details:
            table_data = [["Kriterie", "Status", "Kommentar"]]
            for detail in result.details:
                status = "✓" if detail.get("passed") else "✗"
                table_data.append([
                    detail.get("criterion", ""),
                    status,
                    detail.get("comment", "")[:50] + "..." if len(detail.get("comment", "")) > 50 else detail.get("comment", "")
                ])

            table = Table(table_data, colWidths=[5*cm, 1.5*cm, 10*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(Spacer(1, 0.3*cm))
            elements.append(table)

        elements.append(Spacer(1, 0.5*cm))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)

    # Sanitize filename - remove special characters that break Content-Disposition
    safe_title = re.sub(r'[^\w\s-]', '', report.title).replace(' ', '_')
    filename = f"evaluering_{safe_title}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/{report_id}/extract-info")
def extract_info(report_id: int, db: Session = Depends(get_db)):
    """Extract author and contribution information from a report for anonymization."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Download the PDF
    storage = StorageClient()
    try:
        content = storage.download_file(report.file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not download file: {e}")

    # Extract information
    try:
        info = extract_report_info(content)
        return {
            "authors": info.authors,
            "medforfatterbidrag": info.medforfatterbidrag,
            "ki_brukt": info.ki_brukt,
            "total_pages": info.total_pages,
            "suggested_pages_to_remove": info.suggested_pages_to_remove,
            "title": info.extracted_title or report.title,  # Prefer extracted title
            "oppgave": info.extracted_oppgave or report.oppgave,  # Prefer extracted oppgave
            "dato": info.extracted_dato or (report.innleveringsdato.strftime("%d.%m.%Y") if report.innleveringsdato else None),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not extract info: {e}")


@router.post("/{report_id}/anonymize", response_model=AnonymizeResponse)
def anonymize_report(
    report_id: int,
    request: AnonymizeRequest,
    db: Session = Depends(get_db),
):
    """Anonymize a report by removing identifying information."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Download original PDF
    storage = StorageClient()
    try:
        original_content = storage.download_file(report.file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not download original file: {e}")

    # Prepare authors list
    authors = [{"name": a.name, "initials": a.initials} for a in request.authors]

    # Use title, dato, and oppgave from request if provided, otherwise fall back to report data
    title = request.title or report.title
    dato = request.dato or (report.innleveringsdato.strftime("%d.%m.%Y") if report.innleveringsdato else "")
    oppgave = request.oppgave or report.oppgave or ""

    # Anonymize the PDF
    try:
        anonymized_content, mapping_content, mappings = anonymize_pdf(
            content=original_content,
            title=title,
            oppgave=oppgave,
            dato=dato,
            authors=authors,
            medforfatterbidrag=request.medforfatterbidrag,
            ki_brukt=request.ki_brukt,
            pages_to_remove=request.pages_to_remove,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Anonymization failed: {e}")

    # Generate file paths
    base_name = report.file_path.split("/")[-1].rsplit(".", 1)[0]
    anonymized_path = f"anonymized/{base_name}.pdf"
    mapping_path = f"mappings/{base_name}_mapping.txt"

    # Upload anonymized PDF and mapping file
    try:
        storage.upload_file(anonymized_path, anonymized_content)
        storage.upload_file(mapping_path, mapping_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not upload files: {e}")

    # Extract text from anonymized PDF for use in evaluations
    try:
        anonymized_text = extract_text_from_pdf(anonymized_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not extract text from anonymized PDF: {e}")

    # Extract metadata (kandidater) from anonymized text
    metadata = extract_metadata_from_text(anonymized_text)

    # Parse dato string to date object
    innleveringsdato = None
    if dato:
        try:
            from datetime import datetime
            innleveringsdato = datetime.strptime(dato, "%d.%m.%Y").date()
        except ValueError:
            pass  # Keep as None if parsing fails

    # Update report with anonymization info and anonymized text
    report.anonymized_file_path = anonymized_path
    report.mapping_file_path = mapping_path
    report.candidate_mappings = [m.to_dict() for m in mappings]
    report.content_text = anonymized_text  # Replace with anonymized content
    report.kandidater = metadata.kandidater  # Update kandidater from anonymized cover
    report.innleveringsdato = innleveringsdato  # Update date from cover page
    report.title = title  # Update title from cover page
    report.oppgave = oppgave if oppgave else None  # Update oppgave from cover page
    db.commit()

    return AnonymizeResponse(
        anonymized_file_path=anonymized_path,
        mapping_file_path=mapping_path,
        mappings=[
            AuthorMappingResponse(
                name=m.name,
                initials=m.initials,
                candidate_number=m.candidate_number,
            )
            for m in mappings
        ],
        message="Rapport anonymisert",
    )


@router.get("/{report_id}/mapping-file")
def download_mapping_file(report_id: int, db: Session = Depends(get_db)):
    """Download the candidate mapping file for a report."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if not report.mapping_file_path:
        raise HTTPException(status_code=404, detail="No mapping file available. Anonymize the report first.")

    storage = StorageClient()
    try:
        content = storage.download_file(report.mapping_file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not download mapping file: {e}")

    # Sanitize filename - remove special characters that break Content-Disposition
    safe_title = re.sub(r'[^\w\s-]', '', report.title).replace(' ', '_')
    filename = f"kandidatmapping_{safe_title}.txt"
    return StreamingResponse(
        BytesIO(content),
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/{report_id}/anonymized-pdf")
def download_anonymized_pdf(report_id: int, db: Session = Depends(get_db)):
    """Download the anonymized PDF for a report."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if not report.anonymized_file_path:
        raise HTTPException(status_code=404, detail="No anonymized PDF available. Anonymize the report first.")

    storage = StorageClient()
    try:
        content = storage.download_file(report.anonymized_file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not download anonymized PDF: {e}")

    # Sanitize filename - remove special characters that break Content-Disposition
    safe_title = re.sub(r'[^\w\s-]', '', report.title).replace(' ', '_')
    filename = f"{safe_title}_anonym.pdf"
    return StreamingResponse(
        BytesIO(content),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.delete("/{report_id}")
def delete_report(report_id: int, db: Session = Depends(get_db)):
    """Delete a report."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    service = ReportService(db)
    service.delete_report(report)
    return {"message": "Report deleted"}
