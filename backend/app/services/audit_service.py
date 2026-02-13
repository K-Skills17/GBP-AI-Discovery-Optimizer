"""Core audit orchestrator — Places API + Gemini + Competitor Analysis + WhatsApp."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

from app.database import get_supabase_client
from app.services.places_service import places_service
from app.services.gemini_service import gemini_service
from app.services.competitor_service import competitor_service
from app.services.whatsapp_service import whatsapp_service
from app.utils.scoring import (
    calculate_discovery_score,
    generate_priority_recommendations,
)

logger = logging.getLogger(__name__)


class AuditService:
    def __init__(self):
        self.supabase = get_supabase_client()

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    async def create_audit(
        self,
        business_name: str,
        location: str,
        whatsapp: str,
        user_id: Optional[str] = None,
        utm_source: Optional[str] = None,
        utm_medium: Optional[str] = None,
        utm_campaign: Optional[str] = None,
        utm_content: Optional[str] = None,
    ) -> Dict:
        """Create a new audit request and kick off processing.

        WhatsApp number is required — every audit delivers results via WhatsApp.
        """
        try:
            # Check for recent cached audit
            existing = await self._check_existing_audit(business_name, location)
            if existing:
                logger.info(f"Returning cached audit: {existing['id']}")
                return existing

            # Search for business via Places API
            business_data = await places_service.search_business(
                business_name, location
            )
            if not business_data:
                raise ValueError(
                    f"Negócio '{business_name}' não encontrado em {location}"
                )

            # Save / update business
            business = await self._save_business(business_data)

            # Create audit record
            audit_data = {
                "business_id": business["id"],
                "user_id": user_id,
                "status": "pending",
                "whatsapp_number": whatsapp,
                "created_at": datetime.utcnow().isoformat(),
            }

            # Include UTM params if present (Facebook ad attribution)
            if utm_source:
                audit_data["utm_source"] = utm_source
            if utm_medium:
                audit_data["utm_medium"] = utm_medium
            if utm_campaign:
                audit_data["utm_campaign"] = utm_campaign
            if utm_content:
                audit_data["utm_content"] = utm_content

            result = self.supabase.table("audits").insert(audit_data).execute()
            audit = result.data[0]

            # Trigger background processing
            try:
                from app.tasks.audit_tasks import process_audit_task

                process_audit_task.delay(audit["id"])
            except Exception as e:
                logger.warning(
                    f"Celery/Redis unavailable ({e}), running audit in-process"
                )
                asyncio.create_task(self.process_audit(audit["id"]))

            return audit

        except Exception as e:
            logger.error(f"Audit creation error: {e}")
            raise

    # ------------------------------------------------------------------
    # Process (main pipeline)
    # ------------------------------------------------------------------

    async def process_audit(self, audit_id: str) -> Dict:
        """Main 10-step audit + competitive diagnostic pipeline."""
        start_time = datetime.utcnow()

        try:
            # Update status → processing
            self.supabase.table("audits").update(
                {"status": "processing"}
            ).eq("id", audit_id).execute()

            # Load audit + business
            audit_result = (
                self.supabase.table("audits")
                .select("*, businesses(*)")
                .eq("id", audit_id)
                .execute()
            )
            audit = audit_result.data[0]
            business = audit["businesses"]

            # Step 1: Fetch reviews (Places API)
            logger.info(f"[{audit_id}] Step 1: Fetching reviews")
            reviews = await places_service.get_business_reviews(
                business["place_id"]
            )
            await self._save_reviews(business["id"], reviews)

            # Step 2: Find top competitors (Places API)
            logger.info(f"[{audit_id}] Step 2: Finding competitors")
            lat = business.get("latitude")
            lng = business.get("longitude")
            category = business.get("category", "")

            if lat and lng:
                competitors = await places_service.find_competitors(
                    category=category,
                    lat=float(lat),
                    lng=float(lng),
                    city=business.get("city", ""),
                    radius_m=5000,
                    limit=5,
                    exclude_place_id=business.get("place_id"),
                )
            else:
                competitors = await places_service.find_competitors_text(
                    category=category,
                    city=business.get("city", ""),
                    limit=5,
                    exclude_place_id=business.get("place_id"),
                )

            # Step 3: AI Perception Analysis (Gemini)
            logger.info(f"[{audit_id}] Step 3: AI perception analysis")
            ai_perception = gemini_service.analyze_business_perception(
                business, reviews
            )

            # Step 4: Sentiment Gap Analysis (Gemini)
            logger.info(f"[{audit_id}] Step 4: Sentiment gap analysis")
            sentiment_analysis = gemini_service.analyze_sentiment_gaps(
                business, reviews
            )

            # Step 5: Conversational Query Generation (Gemini)
            logger.info(f"[{audit_id}] Step 5: Generating queries")
            conversational_queries = gemini_service.generate_conversational_queries(
                business
            )

            # Step 6: Visual Coverage Audit
            logger.info(f"[{audit_id}] Step 6: Visual coverage audit")
            photo_urls = business.get("photos") or []
            visual_audit = gemini_service.analyze_photo_coverage(
                business, photo_urls
            )

            # Step 7: Competitive Analysis (Gemini + Places data)
            logger.info(f"[{audit_id}] Step 7: Competitive analysis")
            comp_analysis = await competitor_service.run_competitive_analysis(
                business, competitors
            )

            # Step 8: Calculate Discovery Score (updated weights)
            logger.info(f"[{audit_id}] Step 8: Calculating score")
            discovery_score = calculate_discovery_score(
                ai_perception,
                sentiment_analysis,
                visual_audit,
                business,
                comp_analysis,
            )

            # Step 9: Generate Recommendations (including competitor insights)
            logger.info(f"[{audit_id}] Step 9: Generating recommendations")
            recommendations = generate_priority_recommendations(
                discovery_score,
                ai_perception,
                sentiment_analysis,
                visual_audit,
                business,
                comp_analysis,
            )

            # Sentiment score
            topics = sentiment_analysis.get("topics", {})
            sentiment_score = (
                sum(topics.values()) / len(topics) if topics else 0.5
            )

            processing_time = int(
                (datetime.utcnow() - start_time).total_seconds()
            )

            # Step 10: Save results
            update_data = {
                "status": "completed",
                "discovery_score": discovery_score,
                "competitive_score": comp_analysis.get("competitive_score"),
                "sentiment_score": sentiment_score,
                "visual_coverage_score": visual_audit.get("coverage_score", 0.0),
                "ai_summary": ai_perception,
                "sentiment_analysis": sentiment_analysis,
                "conversational_queries": conversational_queries,
                "visual_audit": visual_audit,
                "competitor_analysis": comp_analysis,
                "recommendations": recommendations,
                "processing_time_seconds": processing_time,
                "updated_at": datetime.utcnow().isoformat(),
            }

            result = (
                self.supabase.table("audits")
                .update(update_data)
                .eq("id", audit_id)
                .execute()
            )
            completed_audit = result.data[0]

            # Step 11: Send WhatsApp report (always — WhatsApp is required)
            whatsapp_number = audit.get("whatsapp_number")
            if whatsapp_number:
                logger.info(f"[{audit_id}] Step 11: Sending WhatsApp")
                wa_result = await self._send_whatsapp_report(
                    audit_id, whatsapp_number, completed_audit, business
                )
                # Retry once on failure
                if not wa_result.get("success"):
                    logger.warning(
                        f"[{audit_id}] WhatsApp first attempt failed, retrying..."
                    )
                    await asyncio.sleep(3)
                    wa_result = await self._send_whatsapp_report(
                        audit_id, whatsapp_number, completed_audit, business
                    )
                    if not wa_result.get("success"):
                        # Record the error so frontend can show retry button
                        self.supabase.table("audits").update(
                            {"whatsapp_error": wa_result.get("error", "Falha no envio")}
                        ).eq("id", audit_id).execute()

            logger.info(
                f"Audit {audit_id} completed in {processing_time}s"
            )
            return completed_audit

        except Exception as e:
            logger.error(f"Audit processing error: {e}")
            self.supabase.table("audits").update(
                {
                    "status": "failed",
                    "error_message": str(e),
                    "updated_at": datetime.utcnow().isoformat(),
                }
            ).eq("id", audit_id).execute()
            raise

    # ------------------------------------------------------------------
    # WhatsApp delivery
    # ------------------------------------------------------------------

    async def send_whatsapp_report(self, audit_id: str) -> Dict:
        """Manually trigger WhatsApp delivery for an existing audit."""
        audit = await self.get_audit_status(audit_id)
        if audit.get("status") != "completed":
            raise ValueError("Audit not completed yet")

        whatsapp_number = audit.get("whatsapp_number")
        if not whatsapp_number:
            raise ValueError("No WhatsApp number on this audit")

        business = audit.get("businesses") or {}
        return await self._send_whatsapp_report(
            audit_id, whatsapp_number, audit, business
        )

    async def _send_whatsapp_report(
        self,
        audit_id: str,
        phone: str,
        audit: Dict,
        business: Dict,
    ) -> Dict:
        """Internal: format + send + record WhatsApp delivery."""
        report_data = {
            "business": business,
            "business_name": business.get("name"),
            "discovery_score": audit.get("discovery_score"),
            "competitor_analysis": audit.get("competitor_analysis", {}),
        }

        result = await whatsapp_service.send_diagnostic_report(phone, report_data)

        # Record delivery
        wa_update = {
            "whatsapp_sent": result.get("success", False),
            "updated_at": datetime.utcnow().isoformat(),
        }
        if result.get("success"):
            wa_update["whatsapp_sent_at"] = datetime.utcnow().isoformat()

        self.supabase.table("audits").update(wa_update).eq(
            "id", audit_id
        ).execute()

        # Also store in whatsapp_messages table
        try:
            self.supabase.table("whatsapp_messages").insert(
                {
                    "audit_id": audit_id,
                    "phone_number": phone,
                    "message_type": "diagnostic_report",
                    "status": "sent" if result.get("success") else "failed",
                    "evolution_message_id": result.get("message_id"),
                    "error_message": result.get("error"),
                    "sent_at": (
                        datetime.utcnow().isoformat()
                        if result.get("success")
                        else None
                    ),
                }
            ).execute()
        except Exception as e:
            logger.warning(f"Failed to log WhatsApp message: {e}")

        return result

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def get_audit_status(self, audit_id: str) -> Dict:
        """Get current status of an audit."""
        result = (
            self.supabase.table("audits")
            .select("*, businesses(*)")
            .eq("id", audit_id)
            .execute()
        )
        if not result.data:
            raise ValueError(f"Audit {audit_id} not found")
        return result.data[0]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _check_existing_audit(
        self, business_name: str, location: str
    ) -> Optional[Dict]:
        """Return a cached completed audit from the last 24 h."""
        business_data = await places_service.search_business(
            business_name, location
        )
        if not business_data:
            return None

        place_id = business_data.get("place_id")
        cutoff = datetime.utcnow() - timedelta(hours=24)

        result = (
            self.supabase.table("audits")
            .select("*, businesses!inner(*)")
            .eq("businesses.place_id", place_id)
            .gte("created_at", cutoff.isoformat())
            .eq("status", "completed")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    async def _save_business(self, business_data: Dict) -> Dict:
        """Upsert business record."""
        place_id = business_data["place_id"]

        existing = (
            self.supabase.table("businesses")
            .select("*")
            .eq("place_id", place_id)
            .execute()
        )

        # Filter to columns that exist in our schema
        allowed_cols = {
            "place_id", "name", "address", "city", "state", "category",
            "phone", "website", "rating", "total_reviews", "claimed",
            "latitude", "longitude", "description", "hours", "photos",
            "photos_count", "google_maps_url", "raw_data",
        }
        filtered = {
            k: v for k, v in business_data.items() if k in allowed_cols
        }

        if existing.data:
            result = (
                self.supabase.table("businesses")
                .update({**filtered, "updated_at": datetime.utcnow().isoformat()})
                .eq("place_id", place_id)
                .execute()
            )
            return result.data[0]
        else:
            result = (
                self.supabase.table("businesses").insert(filtered).execute()
            )
            return result.data[0]

    async def _save_reviews(self, business_id: str, reviews: list) -> None:
        """Save reviews to database."""
        if not reviews:
            return

        review_records = [
            {**review, "business_id": business_id} for review in reviews
        ]

        try:
            self.supabase.table("reviews").insert(review_records).execute()
        except Exception as e:
            logger.warning(f"Some reviews already exist: {e}")


# Singleton
audit_service = AuditService()
