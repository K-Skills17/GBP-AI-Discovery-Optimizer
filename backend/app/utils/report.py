"""Build audit report as PDF or plain text — now includes competitive analysis."""

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


# ------------------------------------------------------------------
# Plain text report
# ------------------------------------------------------------------


def build_report_text(audit: Dict[str, Any]) -> str:
    """Build plain text report from audit data."""
    name = _get_business_name(audit)
    lines = [
        "=" * 60,
        "DIAGNÓSTICO COMPETITIVO - AI Discovery Optimizer",
        "=" * 60,
        "",
        f"Negócio: {name}",
        f"Score de Descoberta: {audit.get('discovery_score') or 0}/100",
        f"Score Competitivo: {audit.get('competitive_score') or 'N/A'}",
        "",
    ]

    # Section 1: Competitive landscape
    comp = audit.get("competitor_analysis") or {}
    competitors = comp.get("competitors", [])
    if competitors:
        lines.extend([
            "--- 1. QUEM DOMINA SUA REGIÃO ---",
            "",
        ])
        for c in competitors[:3]:
            ai = " [IA recomenda]" if c.get("ai_mentioned") else ""
            lines.append(
                f"  #{c.get('rank', '?')} {c.get('name', 'N/A')}{ai}"
            )
            lines.append(
                f"     Nota: {c.get('rating', 'N/A')} | "
                f"Avaliações: {c.get('total_reviews', 0)} | "
                f"Fotos: {c.get('photos_count', 0)}"
            )
        lines.append("")

    # Section 2: Your position
    matrix = comp.get("comparison_matrix", {})
    biz = matrix.get("your_business", {})
    if biz:
        lines.extend([
            "--- 2. ONDE SUA CLÍNICA ESTÁ ---",
            "",
            f"  Nota: {biz.get('rating', 'N/A')}",
            f"  Avaliações: {biz.get('total_reviews', 0)}",
            f"  Fotos: {biz.get('photos_count', 0)}",
            f"  Site: {'Sim' if biz.get('has_website') else 'Não'}",
            "",
        ])

    # Section 3: Gaps
    gaps = comp.get("gaps", [])
    if gaps:
        lines.extend([
            "--- 3. O QUE SEPARA VOCÊ DO TOP 3 ---",
            "",
        ])
        for g in gaps[:4]:
            severity = "[ALTO]" if g.get("severity") == "high" else "[MÉDIO]"
            lines.append(f"  {severity} {g.get('message', '')}")
        lines.append("")

    # AI summary
    ai = audit.get("ai_summary") or {}
    if isinstance(ai, dict):
        lines.extend([
            "--- COMO A IA VÊ SEU NEGÓCIO ---",
            "",
            f"Resumo: {ai.get('ai_summary', 'N/A')}",
            f"Público-alvo: {ai.get('target_audience', 'N/A')}",
        ])
        attrs = ai.get("key_attributes") or []
        if attrs:
            lines.append("Atributos: " + ", ".join(attrs))
        missing = ai.get("missing_signals") or []
        if missing:
            lines.append("Informações faltantes:")
            for m in missing:
                lines.append(f"  - {m}")

    # Recommendations
    lines.extend(["", "--- AÇÕES RECOMENDADAS ---", ""])
    recs = audit.get("recommendations") or []
    for i, r in enumerate(recs, 1):
        if isinstance(r, dict):
            lines.append(
                f"{i}. {r.get('action', '')} "
                f"(Prioridade: {r.get('priority', '')}, Impacto: {r.get('impact', '')})"
            )

    lines.extend(["", "=" * 60])
    return "\n".join(lines)


# ------------------------------------------------------------------
# PDF report
# ------------------------------------------------------------------


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
        Paragraph("Diagnóstico Competitivo - AI Discovery Optimizer", title_style),
        Spacer(1, 12),
        Paragraph(f"<b>Negócio:</b> {name}", body_style),
        Paragraph(
            f"<b>Score de Descoberta:</b> {audit.get('discovery_score') or 0}/100",
            body_style,
        ),
    ]

    # Competitive section
    comp = audit.get("competitor_analysis") or {}
    competitors = comp.get("competitors", [])
    if competitors:
        flow.append(Spacer(1, 16))
        flow.append(Paragraph("1. Quem domina sua região", heading_style))
        for c in competitors[:3]:
            ai_badge = " [IA recomenda]" if c.get("ai_mentioned") else ""
            flow.append(
                Paragraph(
                    f"<b>#{c.get('rank', '?')} {c.get('name', 'N/A')}{ai_badge}</b> "
                    f"— Nota: {c.get('rating', 'N/A')} | "
                    f"Avaliações: {c.get('total_reviews', 0)} | "
                    f"Fotos: {c.get('photos_count', 0)}",
                    body_style,
                )
            )

    # Your position
    matrix = comp.get("comparison_matrix", {})
    biz = matrix.get("your_business", {})
    if biz:
        flow.append(Spacer(1, 12))
        flow.append(Paragraph("2. Onde sua clínica está", heading_style))
        flow.append(
            Paragraph(
                f"Nota: {biz.get('rating', 'N/A')} | "
                f"Avaliações: {biz.get('total_reviews', 0)} | "
                f"Fotos: {biz.get('photos_count', 0)} | "
                f"Site: {'Sim' if biz.get('has_website') else 'Não'}",
                body_style,
            )
        )

    # Gaps
    gaps = comp.get("gaps", [])
    if gaps:
        flow.append(Spacer(1, 12))
        flow.append(Paragraph("3. O que separa você do Top 3", heading_style))
        for g in gaps[:4]:
            sev = "ALTO" if g.get("severity") == "high" else "MÉDIO"
            flow.append(
                Paragraph(f"[{sev}] {g.get('message', '')}", body_style)
            )

    # AI perception
    flow.append(Spacer(1, 16))
    ai = audit.get("ai_summary") or {}
    if isinstance(ai, dict):
        flow.append(Paragraph("Como a IA vê seu negócio", heading_style))
        flow.append(Paragraph(f"Resumo: {ai.get('ai_summary', 'N/A')}", body_style))
        flow.append(Paragraph(f"Público-alvo: {ai.get('target_audience', 'N/A')}", body_style))
        attrs = ai.get("key_attributes") or []
        if attrs:
            flow.append(Paragraph("Atributos: " + ", ".join(attrs), body_style))
        missing = ai.get("missing_signals") or []
        if missing:
            flow.append(Paragraph("Informações faltantes:", body_style))
            for m in missing:
                flow.append(Paragraph(f"&bull; {m}", body_style))
        flow.append(Spacer(1, 12))

    # Recommendations
    flow.append(Paragraph("Ações recomendadas", heading_style))
    recs = audit.get("recommendations") or []
    for r in recs:
        if isinstance(r, dict):
            flow.append(
                Paragraph(
                    f"&bull; <b>{r.get('action', '')}</b> — "
                    f"Prioridade: {r.get('priority', '')}, "
                    f"Impacto: {r.get('impact', '')}",
                    body_style,
                )
            )

    doc.build(flow)
    return buffer.getvalue()
