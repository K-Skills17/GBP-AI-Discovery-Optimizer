"""Build audit report as PDF or plain text."""
import io
from typing import Any, Dict

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


def _get_business_name(audit: Dict[str, Any]) -> str:
    business = audit.get("businesses") or {}
    if isinstance(business, dict):
        return business.get("name") or "Negócio"
    return "Negócio"


def build_report_text(audit: Dict[str, Any]) -> str:
    """Build plain text report from audit data."""
    name = _get_business_name(audit)
    lines = [
        "=" * 60,
        "RELATÓRIO DE AUDITORIA - AI Discovery Optimizer",
        "=" * 60,
        "",
        f"Negócio: {name}",
        f"Score de Descoberta: {audit.get('discovery_score') or 0}/100",
        "",
        "--- Como a IA vê seu negócio ---",
        "",
    ]
    ai = audit.get("ai_summary") or {}
    if isinstance(ai, dict):
        lines.append(f"Resumo: {ai.get('ai_summary', 'N/A')}")
        lines.append(f"Público-alvo: {ai.get('target_audience', 'N/A')}")
        attrs = ai.get("key_attributes") or []
        if attrs:
            lines.append("Atributos: " + ", ".join(attrs))
        missing = ai.get("missing_signals") or []
        if missing:
            lines.append("Informações faltantes:")
            for m in missing:
                lines.append(f"  - {m}")
    lines.extend(["", "--- Ações recomendadas ---", ""])
    recs = audit.get("recommendations") or []
    for i, r in enumerate(recs, 1):
        if isinstance(r, dict):
            lines.append(f"{i}. {r.get('action', '')} (Prioridade: {r.get('priority', '')}, Impacto: {r.get('impact', '')})")
    lines.extend(["", "=" * 60])
    return "\n".join(lines)


def build_report_pdf(audit: Dict[str, Any]) -> bytes:
    """Build PDF report from audit data. Returns PDF bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=16,
        spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=12,
        spaceAfter=6,
    )
    body_style = styles["Normal"]

    name = _get_business_name(audit)
    flow = [
        Paragraph("Relatório de Auditoria - AI Discovery Optimizer", title_style),
        Spacer(1, 12),
        Paragraph(f"<b>Negócio:</b> {name}", body_style),
        Paragraph(f"<b>Score de Descoberta:</b> {audit.get('discovery_score') or 0}/100", body_style),
        Spacer(1, 16),
        Paragraph("Como a IA vê seu negócio", heading_style),
    ]
    ai = audit.get("ai_summary") or {}
    if isinstance(ai, dict):
        flow.append(Paragraph(f"Resumo: {ai.get('ai_summary', 'N/A')}", body_style))
        flow.append(Paragraph(f"Público-alvo: {ai.get('target_audience', 'N/A')}", body_style))
        attrs = ai.get("key_attributes") or []
        if attrs:
            flow.append(Paragraph("Atributos: " + ", ".join(attrs), body_style))
        missing = ai.get("missing_signals") or []
        if missing:
            flow.append(Paragraph("Informações faltantes:", body_style))
            for m in missing:
                flow.append(Paragraph(f"• {m}", body_style))
        flow.append(Spacer(1, 12))

    flow.append(Paragraph("Ações recomendadas", heading_style))
    recs = audit.get("recommendations") or []
    for r in recs:
        if isinstance(r, dict):
            flow.append(
                Paragraph(
                    f"• <b>{r.get('action', '')}</b> — Prioridade: {r.get('priority', '')}, Impacto: {r.get('impact', '')}",
                    body_style,
                )
            )
    doc.build(flow)
    return buffer.getvalue()
