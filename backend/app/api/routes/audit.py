import logging
from io import BytesIO

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import PlainTextResponse, StreamingResponse

from app.schemas.audit import AuditCreateRequest, AuditResponse
from app.services.audit_service import audit_service
from app.utils.report import build_report_pdf, build_report_text

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/audits", response_model=AuditResponse, status_code=status.HTTP_201_CREATED)
async def create_audit(request: AuditCreateRequest):
    """
    Create a new audit for a business
    
    This will:
    1. Search for the business on Google Maps
    2. Create an audit record
    3. Trigger background processing
    4. Return the audit ID for status tracking
    """
    try:
        audit = await audit_service.create_audit(
            business_name=request.business_name,
            location=request.location,
            user_id=None  # For MVP, no auth required
        )
        
        return audit
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating audit: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao criar auditoria. Tente novamente."
        )

@router.get("/audits/{audit_id}", response_model=AuditResponse)
async def get_audit(audit_id: str):
    """
    Get audit status and results
    
    Status values:
    - pending: Audit created, waiting to process
    - processing: Currently analyzing the business
    - completed: Analysis complete, results available
    - failed: An error occurred during processing
    """
    try:
        audit = await audit_service.get_audit_status(audit_id)
        return audit
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting audit: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao buscar auditoria."
        )


@router.get("/audits/{audit_id}/report")
async def get_audit_report(
    audit_id: str,
    report_format: str = Query("pdf", alias="format", pattern="^(pdf|text)$"),
):
    """
    Download audit report as PDF or plain text.
    Only available for completed audits.
    """
    try:
        audit = await audit_service.get_audit_status(audit_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching audit for report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao gerar relatório.",
        )
    if audit.get("status") != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Relatório disponível apenas para auditorias concluídas.",
        )
    name = (audit.get("businesses") or {}).get("name", "audit") if isinstance(audit.get("businesses"), dict) else "audit"
    safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in name)[:50]
    if report_format == "text":
        text = build_report_text(audit)
        return PlainTextResponse(
            text,
            media_type="text/plain; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="auditoria-{safe_name}.txt"',
            },
        )
    pdf_bytes = build_report_pdf(audit)
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="auditoria-{safe_name}.pdf"',
        },
    )
