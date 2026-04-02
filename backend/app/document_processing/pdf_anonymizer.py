"""PDF Anonymization utility for student reports."""
import io
import random
import re
from dataclasses import dataclass, asdict
from datetime import datetime

import fitz  # PyMuPDF
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors


@dataclass
class AuthorMapping:
    """Mapping between author name, initials, and candidate number."""
    name: str
    initials: str
    candidate_number: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ExtractedReportInfo:
    """Information extracted from a PDF report."""
    authors: list[dict]  # [{"name": "...", "initials": "..."}]
    medforfatterbidrag: dict[str, list[str]]  # {"Sammendrag": ["I.I.F"], ...}
    ki_brukt: bool
    total_pages: int
    suggested_pages_to_remove: list[int]  # 1-indexed for user display
    extracted_title: str | None  # Title extracted from cover page
    extracted_dato: str | None  # Date extracted from cover page
    extracted_oppgave: str | None  # Assignment name extracted from cover page

    def to_dict(self) -> dict:
        return asdict(self)


def _generate_initials(name: str) -> str:
    """Generate initials from a full name."""
    parts = name.split()
    if not parts:
        return ""
    # Take first letter of each part, with dots
    initials = ".".join(p[0].upper() for p in parts if p)
    return initials


def _extract_authors_from_cover(text: str) -> list[dict]:
    """
    Extract author names from cover page text.
    Looks for patterns like "Ida Irene Faye og Thomas Bræin" at the bottom of the page.
    """
    authors = []

    # Split into lines and look at the last non-empty lines
    lines = [l.strip() for l in text.split('\n') if l.strip()]

    # Look for lines with "og" that might be author names
    for line in lines[-10:]:  # Check last 10 lines
        # Pattern: "Name1 og Name2" or just names
        if ' og ' in line.lower():
            # Split by "og"
            parts = re.split(r'\s+og\s+', line, flags=re.IGNORECASE)
            for part in parts:
                name = part.strip()
                # Filter out things that don't look like names
                if name and len(name) > 2 and not any(c.isdigit() for c in name):
                    # Check it looks like a name (has capital letters, no special chars)
                    if re.match(r'^[A-ZÆØÅ][a-zæøå]+(\s+[A-ZÆØÅ][a-zæøå]+)*$', name):
                        authors.append({
                            "name": name,
                            "initials": _generate_initials(name)
                        })

    return authors


def _extract_medforfatterbidrag(text: str) -> dict[str, list[str]]:
    """
    Extract medforfatterbidrag section from text.
    Handles two formats:
    Format 1 (colon-separated, one per line):
        Sammendrag: I.I.F
        1 Introduksjon: T.B, I.I.F
    Format 2 (comma-separated, semicolon between entries):
        Sammendrag, F.I; Introduksjon, I.A; Materiale og metode, F.I
    """
    medforfatterbidrag = {}

    # Find the Medforfatterbidrag section
    match = re.search(r'[Mm]edforfatterbidrag\s*\n(.*?)(?:\n\s*\n|Alle forfattere|Originalitet|$)',
                      text, re.DOTALL)
    if not match:
        return medforfatterbidrag

    section_text = match.group(1).strip()

    # Pattern for initials like T.B, I.I.F, A.B.C, F.I
    initials_pattern = r'[A-ZÆØÅ](?:\.[A-ZÆØÅ])+\.?'

    # Check if it's Format 2 (semicolon-separated entries with comma before initials)
    if ';' in section_text and re.search(r',\s*[A-ZÆØÅ]\.', section_text):
        # Format 2: "Sammendrag, F.I; Introduksjon, I.A; ..."
        # Join lines and split by semicolon
        full_text = ' '.join(section_text.split('\n'))
        entries = full_text.split(';')

        for entry in entries:
            entry = entry.strip()
            if not entry:
                continue

            # Find the last comma before initials
            # Pattern: "Section name, X.Y" or "Section name, X.Y.Z"
            match_entry = re.match(r'(.+?),\s*(' + initials_pattern + r')', entry)
            if match_entry:
                section_name = match_entry.group(1).strip()
                initial = match_entry.group(2).strip()
                if section_name and initial:
                    if section_name not in medforfatterbidrag:
                        medforfatterbidrag[section_name] = []
                    medforfatterbidrag[section_name].append(initial)
    else:
        # Format 1: colon-separated, one per line
        for line in section_text.split('\n'):
            line = line.strip()
            if not line or ':' not in line:
                continue

            # Split by colon to get section name and contributors
            parts = line.split(':', 1)
            if len(parts) != 2:
                continue

            section_name = parts[0].strip()
            contributors_text = parts[1].strip()

            # Find all initials in the contributors text
            initials = re.findall(initials_pattern, contributors_text)

            if section_name and initials:
                medforfatterbidrag[section_name] = initials

    return medforfatterbidrag


def _extract_ki_status(text: str) -> bool:
    """Check if KI/AI was used based on text."""
    text_lower = text.lower()

    # Look for phrases indicating KI was NOT used
    not_used_patterns = [
        r'ikke\s+brukt\s+ki',
        r'er\s+det\s+ikke\s+brukt\s+ki',
        r'ble\s+det\s+ikke\s+brukt\s+ki',
        r'ikke\s+benyttet\s+ki',
        r'ikke\s+brukt\s+noe\s+ki',
        r'ingen\s+ki',
    ]

    for pattern in not_used_patterns:
        if re.search(pattern, text_lower):
            return False

    # Look for phrases indicating KI WAS used
    used_patterns = [
        r'er\s+det\s+brukt\s+ki',
        r'ble\s+det\s+brukt\s+.*?ki',  # "ble det brukt to KI-verktøy"
        r'har\s+brukt\s+ki',
        r'benyttet\s+ki',
        r'brukt\s+ki-verktøy',
        r'brukt\s+følgende\s+ki',
        r'chat\s*gpt',  # Common AI tools
        r'chatgpt',
        r'copilot',
        r'claude',
    ]

    for pattern in used_patterns:
        if re.search(pattern, text_lower):
            return True

    # Default to False if no clear indication
    return False


def _extract_date_from_cover(text: str) -> str | None:
    """Extract date from cover page text."""
    # Look for date patterns: DD.MM.YYYY, DD/MM/YYYY, DD-MM-YYYY
    date_pattern = r'(\d{1,2}[./-]\d{1,2}[./-]\d{4})'
    match = re.search(date_pattern, text)
    if match:
        return match.group(1)
    return None


def _extract_oppgave_from_cover(text: str) -> str | None:
    """Extract oppgave/assignment name from cover page text."""
    # Look for "Oppgave:" or similar patterns followed by text
    oppgave_patterns = [
        r'[Oo]ppgave[:\s]+([^\n\r]+)',
        r'[Ll]abrapport\s+i\s+([^\n\r]+)',  # "Labrapport i KJM1001"
        r'[Ll]ab(?:oratorium)?[:\s]+([^\n\r]+)',
    ]

    for pattern in oppgave_patterns:
        match = re.search(pattern, text)
        if match:
            oppgave = match.group(1).strip()
            # Clean up - remove trailing punctuation
            oppgave = re.sub(r'[.,:;]+$', '', oppgave).strip()
            if oppgave and len(oppgave) > 3:
                return oppgave

    # Look for course code pattern: "KJM3100 Bioteknologi", "KJM1001 Generell kjemi"
    # Format: 2-4 uppercase letters + 4 digits + optional space + course name
    course_pattern = r'([A-ZÆØÅ]{2,4}\d{4}\s+[A-ZÆØÅ][a-zæøåA-ZÆØÅ\s]+)'
    course_match = re.search(course_pattern, text)
    if course_match:
        oppgave = course_match.group(1).strip()
        # Clean up - stop at newline or author names
        oppgave = oppgave.split('\n')[0].strip()
        if oppgave and len(oppgave) > 5:
            return oppgave

    return None


def _extract_title_from_cover(text: str, authors: list[dict]) -> str | None:
    """
    Extract title from cover page text.
    The title is typically the main text between the date and author names.
    """
    lines = [l.strip() for l in text.split('\n') if l.strip()]

    # Find author names to exclude them
    author_names = [a.get('name', '').lower() for a in authors if a.get('name')]

    # Skip lines that are: dates, author names, or very short
    title_lines = []
    for line in lines:
        line_lower = line.lower()

        # Skip date lines
        if re.match(r'^\d{1,2}[./-]\d{1,2}[./-]\d{4}$', line):
            continue

        # Skip author name lines
        is_author = False
        for name in author_names:
            if name and name in line_lower:
                is_author = True
                break
        if is_author:
            continue

        # Skip "og" connectors between names
        if line_lower == 'og':
            continue

        # Skip very short lines (likely noise)
        if len(line) < 5:
            continue

        # This could be part of the title
        title_lines.append(line)

    # The title is usually the first substantial text block
    if title_lines:
        # Join first few lines that look like title (before we hit other content)
        title_parts = []
        for line in title_lines[:3]:  # Max 3 lines for title
            # Stop if we hit what looks like section content
            if re.match(r'^(innhold|sammendrag|introduksjon|\d+\.)', line.lower()):
                break
            # Stop if we hit a course code (e.g., "KJM3100 Bioteknologi")
            if re.match(r'^[A-ZÆØÅ]{2,4}\d{4}\s', line):
                break
            title_parts.append(line)

        if title_parts:
            return ' '.join(title_parts)

    return None


def _find_appendix_page(doc: fitz.Document) -> int | None:
    """Find the page number containing Vedlegg/appendix section."""
    for page_num in range(len(doc) - 1, -1, -1):  # Search from end
        page = doc[page_num]
        text = page.get_text()

        # Look for Vedlegg header
        if re.search(r'\bVedlegg\b', text):
            # Check if this page has Medforfatterbidrag or Originalitet
            if re.search(r'[Mm]edforfatterbidrag|[Oo]riginalitet|KI-avklaring', text):
                return page_num

    return None


def extract_report_info(content: bytes) -> ExtractedReportInfo:
    """
    Extract author and contribution information from a PDF report.

    Args:
        content: PDF file content as bytes

    Returns:
        ExtractedReportInfo with authors, medforfatterbidrag, ki_brukt, etc.
    """
    doc = fitz.open(stream=content, filetype="pdf")
    total_pages = len(doc)

    # Extract text from first page (cover)
    cover_text = doc[0].get_text() if total_pages > 0 else ""

    # Extract authors from cover page
    authors = _extract_authors_from_cover(cover_text)

    # Extract date, title, and oppgave from cover page
    extracted_dato = _extract_date_from_cover(cover_text)
    extracted_title = _extract_title_from_cover(cover_text, authors)
    extracted_oppgave = _extract_oppgave_from_cover(cover_text)

    # Find appendix page and extract medforfatterbidrag
    appendix_page = _find_appendix_page(doc)
    medforfatterbidrag = {}
    ki_brukt = False

    if appendix_page is not None:
        appendix_text = doc[appendix_page].get_text()
        medforfatterbidrag = _extract_medforfatterbidrag(appendix_text)
        ki_brukt = _extract_ki_status(appendix_text)

    # Suggested pages to remove (1-indexed for user display)
    suggested_pages = [1]  # Always suggest removing cover page
    if appendix_page is not None:
        suggested_pages.append(appendix_page + 1)  # Convert to 1-indexed

    doc.close()

    return ExtractedReportInfo(
        authors=authors,
        medforfatterbidrag=medforfatterbidrag,
        ki_brukt=ki_brukt,
        total_pages=total_pages,
        suggested_pages_to_remove=sorted(suggested_pages),
        extracted_title=extracted_title,
        extracted_dato=extracted_dato,
        extracted_oppgave=extracted_oppgave,
    )


def generate_candidate_number(existing: set[str] | None = None) -> str:
    """Generate a unique 6-digit candidate number."""
    existing = existing or set()
    while True:
        number = str(random.randint(100000, 999999))
        if number not in existing:
            return number


def create_author_mappings(authors: list[dict]) -> list[AuthorMapping]:
    """
    Create candidate number mappings for authors.

    Args:
        authors: List of {"name": "...", "initials": "..."}

    Returns:
        List of AuthorMapping with generated candidate numbers
    """
    existing_numbers: set[str] = set()
    mappings = []

    for author in authors:
        candidate_number = generate_candidate_number(existing_numbers)
        existing_numbers.add(candidate_number)
        mappings.append(AuthorMapping(
            name=author.get("name", ""),
            initials=author.get("initials", ""),
            candidate_number=candidate_number,
        ))

    return mappings


def generate_mapping_file_content(
    mappings: list[AuthorMapping],
    title: str,
) -> str:
    """Generate content for the mapping file."""
    lines = [
        f"# Kandidatmapping - {title}",
        f"# Generert: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        f"{'Navn':<30} {'Initialer':<12} {'Kandidatnummer':<15}",
        "-" * 60,
    ]

    for mapping in mappings:
        lines.append(f"{mapping.name:<30} {mapping.initials:<12} {mapping.candidate_number:<15}")

    return "\n".join(lines)


def remove_pages_from_pdf(content: bytes, pages_to_remove: list[int]) -> bytes:
    """
    Remove specified pages from a PDF.

    Args:
        content: PDF file content as bytes
        pages_to_remove: List of page indices to remove (0-indexed)

    Returns:
        Modified PDF as bytes
    """
    doc = fitz.open(stream=content, filetype="pdf")

    # Sort in reverse order to avoid index shifting
    for page_idx in sorted(pages_to_remove, reverse=True):
        if 0 <= page_idx < len(doc):
            doc.delete_page(page_idx)

    output = io.BytesIO()
    doc.save(output)
    doc.close()

    return output.getvalue()


def create_cover_page(
    title: str,
    kandidater: list[str],
    oppgave: str,
    dato: str,
    medforfatterbidrag: dict[str, list[str]] | None,
    ki_brukt: bool,
    mappings: list[AuthorMapping],
) -> bytes:
    """
    Create an anonymized cover page as PDF.

    Args:
        title: Report title
        kandidater: List of candidate numbers
        oppgave: Assignment name
        dato: Submission date
        medforfatterbidrag: Dict of section -> list of initials, to be converted to candidate numbers
        ki_brukt: Whether AI was used
        mappings: Author mappings for converting initials to candidate numbers

    Returns:
        Cover page PDF as bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1,  # Center
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        spaceBefore=20,
        spaceAfter=10,
        textColor=colors.darkblue,
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6,
    )

    small_style = ParagraphStyle(
        'CustomSmall',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=4,
        textColor=colors.gray,
    )

    # Build initials -> candidate number lookup
    initials_to_candidate = {m.initials: m.candidate_number for m in mappings}

    # Build document content
    story = []

    # Title
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 1*cm))

    # Horizontal line
    story.append(Table([['']], colWidths=[15*cm], rowHeights=[1]))
    story[-1].setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.darkblue),
    ]))
    story.append(Spacer(1, 0.5*cm))

    # Metadata
    story.append(Paragraph(f"<b>Tittel:</b> {title}", normal_style))
    if dato:
        story.append(Paragraph(f"<b>Dato:</b> {dato}", normal_style))
    story.append(Paragraph(f"<b>Kandidat(er):</b> {', '.join(kandidater)}", normal_style))
    if oppgave:
        story.append(Paragraph(f"<b>Oppgave:</b> {oppgave}", normal_style))

    # Medforfatterbidrag section
    if medforfatterbidrag:
        story.append(Spacer(1, 0.5*cm))
        story.append(Table([['']], colWidths=[15*cm], rowHeights=[1]))
        story[-1].setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.gray),
        ]))
        story.append(Spacer(1, 0.3*cm))

        story.append(Paragraph("MEDFORFATTERBIDRAG", heading_style))

        for section, initials_list in medforfatterbidrag.items():
            # Convert initials to candidate numbers
            candidate_nums = []
            for initials in initials_list:
                if initials in initials_to_candidate:
                    candidate_nums.append(initials_to_candidate[initials])
                else:
                    candidate_nums.append(initials)  # Keep as-is if not found

            story.append(Paragraph(f"{section}: {', '.join(candidate_nums)}", small_style))

    # Originalitetserklæring
    story.append(Spacer(1, 0.5*cm))
    story.append(Table([['']], colWidths=[15*cm], rowHeights=[1]))
    story[-1].setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.gray),
    ]))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("ORIGINALITETSERKLÆRING", heading_style))
    story.append(Paragraph(
        "Vi erklærer at denne rapporten er vårt originale arbeid, "
        "med unntak av der det er henvist til andres arbeid via kilder. "
        "Alle sitater og andre kilder for informasjon er behandlet i "
        "henhold til institusjonens retningslinjer.",
        normal_style
    ))
    story.append(Paragraph(f"<b>Kandidat:</b> {', '.join(kandidater)}", small_style))

    # KI-avklaring
    story.append(Spacer(1, 0.5*cm))
    story.append(Table([['']], colWidths=[15*cm], rowHeights=[1]))
    story[-1].setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.gray),
    ]))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("KI-AVKLARING", heading_style))
    if ki_brukt:
        story.append(Paragraph(
            "I denne rapporten er det brukt KI-verktøy. "
            "Detaljer om bruken er dokumentert i henhold til retningslinjene.",
            normal_style
        ))
    else:
        story.append(Paragraph(
            "I denne rapporten er det ikke brukt KI.",
            normal_style
        ))
    story.append(Paragraph(f"<b>Kandidat:</b> {', '.join(kandidater)}", small_style))

    doc.build(story)
    return buffer.getvalue()


def merge_pdfs(cover_pdf: bytes, main_pdf: bytes) -> bytes:
    """
    Merge cover page PDF with main PDF.

    Args:
        cover_pdf: Cover page PDF as bytes
        main_pdf: Main document PDF as bytes

    Returns:
        Merged PDF as bytes
    """
    cover_doc = fitz.open(stream=cover_pdf, filetype="pdf")
    main_doc = fitz.open(stream=main_pdf, filetype="pdf")

    # Insert main document pages after cover
    cover_doc.insert_pdf(main_doc)

    output = io.BytesIO()
    cover_doc.save(output)

    cover_doc.close()
    main_doc.close()

    return output.getvalue()


def anonymize_pdf(
    content: bytes,
    title: str,
    oppgave: str,
    dato: str,
    authors: list[dict],
    medforfatterbidrag: dict[str, list[str]] | None,
    ki_brukt: bool,
    pages_to_remove: list[int],
) -> tuple[bytes, bytes, list[AuthorMapping]]:
    """
    Anonymize a PDF report.

    Args:
        content: Original PDF content
        title: Report title
        oppgave: Assignment name
        dato: Submission date
        authors: List of {"name": "...", "initials": "..."} for each author
        medforfatterbidrag: Dict of section -> list of initials
        ki_brukt: Whether AI was used
        pages_to_remove: Page indices to remove (0-indexed)

    Returns:
        Tuple of (anonymized_pdf, mapping_file_content, mappings)
    """
    # Generate candidate mappings
    mappings = create_author_mappings(authors)
    kandidater = [m.candidate_number for m in mappings]

    # Remove specified pages from original
    main_pdf = remove_pages_from_pdf(content, pages_to_remove)

    # Create anonymized cover page
    cover_pdf = create_cover_page(
        title=title,
        kandidater=kandidater,
        oppgave=oppgave,
        dato=dato,
        medforfatterbidrag=medforfatterbidrag,
        ki_brukt=ki_brukt,
        mappings=mappings,
    )

    # Merge cover with main document
    anonymized_pdf = merge_pdfs(cover_pdf, main_pdf)

    # Generate mapping file
    mapping_content = generate_mapping_file_content(mappings, title)

    return anonymized_pdf, mapping_content.encode('utf-8'), mappings
