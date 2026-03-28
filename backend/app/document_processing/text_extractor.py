import io
import fitz  # PyMuPDF
from docx import Document


def extract_text_from_file(content: bytes, file_extension: str) -> str:
    """Extract text content from a document file."""
    file_extension = file_extension.lower().lstrip(".")

    if file_extension == "pdf":
        return extract_text_from_pdf(content)
    elif file_extension in ("docx", "doc"):
        return extract_text_from_docx(content)
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")


def extract_text_from_pdf(content: bytes) -> str:
    """Extract text from a PDF file."""
    text_parts = []

    with fitz.open(stream=content, filetype="pdf") as doc:
        for page_num, page in enumerate(doc, start=1):
            page_text = page.get_text()
            if page_text.strip():
                text_parts.append(f"--- Side {page_num} ---\n{page_text}")

    return "\n\n".join(text_parts)


def extract_text_from_docx(content: bytes) -> str:
    """Extract text from a Word document."""
    doc = Document(io.BytesIO(content))
    text_parts = []

    for para in doc.paragraphs:
        if para.text.strip():
            text_parts.append(para.text)

    # Also extract text from tables
    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
            if row_text:
                text_parts.append(row_text)

    return "\n\n".join(text_parts)
