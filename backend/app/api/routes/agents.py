from datetime import datetime, timezone
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.agent_configuration import AgentConfiguration
from app.schemas.agent import AgentConfigResponse, AgentConfigUpdate

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/export-criteria-pdf")
def export_criteria_pdf(db: Session = Depends(get_db)):
    """Export all agent criteria as a PDF document."""
    agents = db.query(AgentConfiguration).order_by(AgentConfiguration.id).all()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm, leftMargin=2*cm, rightMargin=2*cm)
    PAGE_WIDTH = A4[0] - 4*cm

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, spaceAfter=6)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#6b7280'), spaceAfter=16)
    agent_heading_style = ParagraphStyle('AgentHeading', parent=styles['Heading2'], fontSize=13, spaceBefore=16, spaceAfter=4)
    agent_desc_style = ParagraphStyle('AgentDesc', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#555555'), spaceAfter=6)
    rubric_style = ParagraphStyle('Rubric', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#1e40af'), spaceAfter=4)
    cell_style = ParagraphStyle('Cell', parent=styles['Normal'], fontSize=9)
    cell_bold_style = ParagraphStyle('CellBold', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold')

    total_score = sum(a.max_score for a in agents)

    elements = []
    elements.append(Paragraph("Vurderingskriterier", title_style))
    elements.append(Paragraph(
        f"{len(agents)} sjekkere · Total maks score: {total_score:.0f} poeng · Generert {datetime.now().strftime('%d.%m.%Y')}",
        subtitle_style,
    ))

    for agent in agents:
        check_items = (agent.criteria or {}).get("checkItems", [])
        scoring_rubric = (agent.criteria or {}).get("scoringRubric", "")

        elements.append(Paragraph(f"{agent.name} ({agent.max_score:.0f}p)", agent_heading_style))
        if agent.description:
            elements.append(Paragraph(agent.description, agent_desc_style))

        if check_items:
            col_label = 5*cm
            col_weight = 1.5*cm
            col_desc = PAGE_WIDTH - col_label - col_weight

            table_data = [[
                Paragraph("Kriterie", cell_bold_style),
                Paragraph("Vekt", cell_bold_style),
                Paragraph("Beskrivelse", cell_bold_style),
            ]]
            for item in check_items:
                table_data.append([
                    Paragraph(item.get("label", ""), cell_style),
                    Paragraph(str(item.get("weight", "")), cell_style),
                    Paragraph(item.get("description", ""), cell_style),
                ])

            table = Table(table_data, colWidths=[col_label, col_weight, col_desc])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ]))
            elements.append(table)

        if scoring_rubric:
            elements.append(Spacer(1, 0.2*cm))
            elements.append(Paragraph(f"<b>Vurderingsmal:</b> {scoring_rubric}", rubric_style))

    doc.build(elements)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="vurderingskriterier.pdf"'},
    )


@router.get("", response_model=list[AgentConfigResponse])
def list_agents(db: Session = Depends(get_db)):
    """List all agent configurations (all are templates)."""
    agents = db.query(AgentConfiguration).order_by(AgentConfiguration.id).all()
    return agents


@router.get("/{agent_id}", response_model=AgentConfigResponse)
def get_agent(agent_id: int, db: Session = Depends(get_db)):
    """Get a specific agent configuration."""
    agent = db.query(AgentConfiguration).filter(AgentConfiguration.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent configuration not found")
    return agent


@router.put("/{agent_id}", response_model=AgentConfigResponse)
def update_agent(agent_id: int, payload: AgentConfigUpdate, db: Session = Depends(get_db)):
    """Update an agent configuration."""
    agent = db.query(AgentConfiguration).filter(AgentConfiguration.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent configuration not found")
    agent.name = payload.name
    agent.description = payload.description
    agent.max_score = payload.max_score
    agent.criteria = payload.criteria
    agent.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(agent)
    return agent
