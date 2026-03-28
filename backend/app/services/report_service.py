import uuid
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.report import Report, ReportStatus
from app.core.storage import StorageClient
from app.document_processing.text_extractor import extract_text_from_file


class ReportService:
    def __init__(self, db: Session):
        self.db = db
        self.storage = StorageClient()

    async def create_report(self, file: UploadFile, title: str) -> Report:
        """Create a new report from an uploaded file."""
        # Generate unique file path
        file_ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else "pdf"
        file_path = f"reports/{uuid.uuid4()}.{file_ext}"

        # Read file content
        content = await file.read()

        # Upload to S3/MinIO
        self.storage.upload_file(file_path, content)

        # Create database record
        report = Report(
            title=title,
            filename=file.filename or "unknown",
            file_path=file_path,
            status=ReportStatus.PROCESSING,
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)

        # Extract text content
        try:
            text_content = extract_text_from_file(content, file_ext)
            report.content_text = text_content
            report.status = ReportStatus.READY
        except Exception as e:
            report.status = ReportStatus.ERROR
            print(f"Error extracting text: {e}")

        self.db.commit()
        self.db.refresh(report)

        return report

    def delete_report(self, report: Report) -> None:
        """Delete a report and its file from storage."""
        # Delete from storage
        try:
            self.storage.delete_file(report.file_path)
        except Exception:
            pass  # File might not exist

        # Delete from database
        self.db.delete(report)
        self.db.commit()
