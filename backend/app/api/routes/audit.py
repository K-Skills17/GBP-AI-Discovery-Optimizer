import logging
from io import BytesIO

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse

from app.schemas.audit import AuditCreateRequest, AuditResponse
from app.services.audit_service import audit_service
from app.utils.report import build_report_pdf, build_report_text

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/audits",
    response_model=AuditResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create competitive diagnostic audit",
)
async def create_audit(request_body: AuditCreateRequest, request: Request):
    """Create a new competitive diagnostic audit.

    WhatsApp number is required — the report is always delivered via WhatsApp
    (Evolution API) after processing completes.

    Steps:
    1. Search business via Google Places API
    2. Find top competitors in same category/area
    3. Run AI analysis (Gemini)
    4. Build competitive report
    5. Send to WhatsApp
    """
    try:
        # Pull optional user_id from auth middleware
        user_id = getattr(request.state, "user_id", None)

        audit = await audit_service.create_audit(
            business_name=request_body.business_name,
            location=request_body.location,
            whatsapp=request_body.whatsapp,
            user_id=user_id,
            utm_source=request_body.utm_source,
            utm_medium=request_body.utm_medium,
            utm_campaign=request_body.utm_campaign,
            utm_content=request_body.utm_content,
        )
        return audit

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error creating audit: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao criar auditoria. Tente novamente.",
        )


@router.get(
    "/audits/{audit_id}",
    response_model=AuditResponse,
    summary="Get audit status and results",
)
async def get_audit(audit_id: str):
    """Get audit status and results.

    Status values:
    - **pending**: Created, waiting to process
    - **processing**: Analysis in progress
    - **completed**: Results available (includes competitor_analysis)
    - **failed**: Error occurred
    """
    try:
        audit = await audit_service.get_audit_status(audit_id)
        return audit
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error getting audit: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao buscar auditoria.",
        )


@router.get(
    "/audits/{audit_id}/competitors",
    summary="Get competitor breakdown",
)
async def get_competitors(audit_id: str):
    """Return just the competitor analysis portion of a completed audit."""
    try:
        audit = await audit_service.get_audit_status(audit_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if audit.get("status") != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Análise competitiva disponível apenas para auditorias concluídas.",
        )

    return audit.get("competitor_analysis") or {}


@router.post(
    "/audits/{audit_id}/send-whatsapp",
    summary="Trigger WhatsApp delivery",
)
async def send_whatsapp(audit_id: str):
    """Manually send (or re-send) the diagnostic report to the WhatsApp number
    associated with this audit.  Useful for standalone audits that later want
    WhatsApp delivery.
    """
    try:
        result = await audit_service.send_whatsapp_report(audit_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"WhatsApp send error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao enviar relatório via WhatsApp.",
        )


@router.get(
    "/audits/{audit_id}/whatsapp-status",
    summary="Check WhatsApp delivery status",
)
async def get_whatsapp_status(audit_id: str):
    """Check whether the WhatsApp report was successfully delivered."""
    try:
        audit = await audit_service.get_audit_status(audit_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return {
        "whatsapp_sent": audit.get("whatsapp_sent", False),
        "whatsapp_sent_at": audit.get("whatsapp_sent_at"),
        "whatsapp_error": audit.get("whatsapp_error"),
        "whatsapp_number": audit.get("whatsapp_number"),
    }


@router.get(
    "/audits/{audit_id}/report",
    summary="Download report (PDF or text)",
)
async def get_audit_report(
    audit_id: str,
    report_format: str = Query("pdf", alias="format", pattern="^(pdf|text)$"),
):
    """Download the competitive diagnostic report as PDF or plain text."""
    try:
        audit = await audit_service.get_audit_status(audit_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching audit for report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao gerar relatório.",
        )

    if audit.get("status") != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Relatório disponível apenas para auditorias concluídas.",
        )

    name = (
        (audit.get("businesses") or {}).get("name", "audit")
        if isinstance(audit.get("businesses"), dict)
        else "audit"
    )
    safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in name)[:50]

    if report_format == "text":
        text = build_report_text(audit)
        return PlainTextResponse(
            text,
            media_type="text/plain; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="diagnostico-{safe_name}.txt"',
            },
        )

    pdf_bytes = build_report_pdf(audit)
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="diagnostico-{safe_name}.pdf"',
        },
    )
