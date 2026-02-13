"""Evolution API integration for WhatsApp message delivery."""

import logging
from typing import Dict, Optional

import httpx

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class WhatsAppService:
    """Send diagnostic reports and notifications via Evolution API."""

    def __init__(self):
        self.base_url = settings.EVOLUTION_API_URL.rstrip("/")
        self.api_key = settings.EVOLUTION_API_KEY
        self.instance = settings.EVOLUTION_INSTANCE_NAME
        self.owner_phone = settings.OWNER_WHATSAPP
        self.headers = {
            "Content-Type": "application/json",
            "apikey": self.api_key,
        }

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    async def send_diagnostic_report(
        self,
        phone: str,
        audit_data: Dict,
    ) -> Dict:
        """Format and send the competitive diagnostic report to WhatsApp."""
        number = self._format_phone_br(phone)
        message = self._format_report_message(audit_data)

        result = await self._send_text(number, message)

        # Notify owner that a new lead received their report
        if self.owner_phone:
            biz_name = (
                audit_data.get("business", {}).get("name")
                or audit_data.get("business_name", "Negócio")
            )
            await self._notify_owner(number, biz_name)

        return result

    async def send_text_message(
        self,
        phone: str,
        message: str,
    ) -> Dict:
        """Send a plain text message to a WhatsApp number."""
        number = self._format_phone_br(phone)
        return await self._send_text(number, message)

    # ------------------------------------------------------------------
    # Report formatting
    # ------------------------------------------------------------------

    def _format_report_message(self, audit_data: Dict) -> str:
        """Build the 3-section WhatsApp report.

        Section 1: Quem domina sua região
        Section 2: Onde sua clínica está
        Section 3: O que separa você do Top 3
        """
        business = audit_data.get("business", {})
        competitor_analysis = audit_data.get("competitor_analysis", {})
        competitors = competitor_analysis.get("competitors", [])
        matrix = competitor_analysis.get("comparison_matrix", {})
        gaps = competitor_analysis.get("gaps", [])
        discovery_score = audit_data.get("discovery_score", 0)
        biz = matrix.get("your_business", {})

        lines = [
            "🔍 *DIAGNÓSTICO COMPETITIVO*",
            f"📍 {business.get('name', 'Sua clínica')} — {business.get('city', '')}",
            "",
            "━━━━━━━━━━━━━━━━━━━━",
            "*1. QUEM DOMINA SUA REGIÃO*",
            "━━━━━━━━━━━━━━━━━━━━",
        ]

        for comp in competitors[:3]:
            ai_badge = " 🤖" if comp.get("ai_mentioned") else ""
            lines.append(
                f"{'🥇🥈🥉'[comp.get('rank', 1) - 1]} *{comp['name']}*{ai_badge}"
            )
            lines.append(
                f"   ⭐ {comp.get('rating', 'N/A')} "
                f"| 💬 {comp.get('total_reviews', 0)} avaliações "
                f"| 📸 {comp.get('photos_count', 0)} fotos"
            )

        lines.extend([
            "",
            "━━━━━━━━━━━━━━━━━━━━",
            "*2. ONDE SUA CLÍNICA ESTÁ*",
            "━━━━━━━━━━━━━━━━━━━━",
            f"📊 *Score de Descoberta: {discovery_score}/100*",
            "",
            f"⭐ Nota: {biz.get('rating', 'N/A')}",
            f"💬 Avaliações: {biz.get('total_reviews', 0)}",
            f"📸 Fotos: {biz.get('photos_count', 0)}",
            f"🌐 Site: {'Sim' if biz.get('has_website') else 'Não'}",
        ])

        if gaps:
            lines.extend([
                "",
                "━━━━━━━━━━━━━━━━━━━━",
                "*3. O QUE SEPARA VOCÊ DO TOP 3*",
                "━━━━━━━━━━━━━━━━━━━━",
            ])
            for i, gap in enumerate(gaps[:4], 1):
                severity_icon = "🔴" if gap.get("severity") == "high" else "🟡"
                lines.append(f"{severity_icon} {gap['message']}")

        lines.extend([
            "",
            "━━━━━━━━━━━━━━━━━━━━",
            "",
            "💡 *Quer saber como fechamos essas lacunas?*",
            "Responda aqui e nosso especialista vai te explicar.",
        ])

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Evolution API calls
    # ------------------------------------------------------------------

    async def _send_text(self, number: str, text: str) -> Dict:
        """Send a text message via Evolution API."""
        url = f"{self.base_url}/message/sendText/{self.instance}"
        payload = {
            "number": number,
            "text": text,
        }

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(url, headers=self.headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                logger.info(f"WhatsApp sent to {number[:8]}...")
                return {
                    "success": True,
                    "message_id": data.get("key", {}).get("id"),
                    "status": "sent",
                }
        except Exception as e:
            logger.error(f"WhatsApp send error: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": "failed",
            }

    async def _notify_owner(self, lead_phone: str, business_name: str) -> None:
        """Notify the business owner that a new lead received a report."""
        owner = self._format_phone_br(self.owner_phone)
        msg = (
            f"🔔 *Novo lead!*\n\n"
            f"📍 {business_name}\n"
            f"📱 {lead_phone}\n\n"
            f"O diagnóstico já foi enviado. Entre em contato agora!"
        )
        await self._send_text(owner, msg)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def validate_phone_br(phone: str) -> bool:
        """Validate that a phone string looks like a Brazilian mobile number."""
        digits = "".join(c for c in phone if c.isdigit())
        # Strip country code
        if digits.startswith("55"):
            digits = digits[2:]
        # Brazilian mobile: 2-digit DDD + 9-digit number starting with 9
        if len(digits) == 11 and digits[2] == "9":
            return True
        # Some older 10-digit formats still work
        if len(digits) == 10:
            return True
        return False

    @staticmethod
    def _format_phone_br(phone: str) -> str:
        """Normalize Brazilian phone to E.164-ish format for Evolution API.

        Accepts: +55 11 99999-1234, 5511999991234, 11999991234, etc.
        Returns: 5511999991234
        """
        digits = "".join(c for c in phone if c.isdigit())
        if digits.startswith("55") and len(digits) >= 12:
            return digits
        if len(digits) == 11:  # DDD + 9-digit mobile
            return f"55{digits}"
        if len(digits) == 10:  # DDD + 8-digit landline
            return f"55{digits}"
        # Fallback: assume it's already formatted or international
        return digits


# Singleton
whatsapp_service = WhatsAppService()
