import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from app.services.outscraper_service import outscraper_service
from app.services.gemini_service import gemini_service
from app.utils.scoring import (
    calculate_discovery_score,
    get_score_interpretation,
    generate_priority_recommendations
)
from app.database import get_supabase_client

logger = logging.getLogger(__name__)

class AuditService:
    def __init__(self):
        self.supabase = get_supabase_client()
    
    async def create_audit(
        self,
        business_name: str,
        location: str,
        user_id: Optional[str] = None
    ) -> Dict:
        """Create new audit request"""
        
        try:
            # Check for recent audit
            existing = await self._check_existing_audit(business_name, location)
            if existing:
                logger.info(f"Returning cached audit: {existing['id']}")
                return existing
            
            # Search for business
            business_data = outscraper_service.search_business(business_name, location)
            
            if not business_data:
                raise ValueError(f"Negócio '{business_name}' não encontrado em {location}")
            
            # Save or update business
            business = await self._save_business(business_data)
            
            # Create audit record
            audit_data = {
                "business_id": business['id'],
                "user_id": user_id,
                "status": "pending",
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table('audits').insert(audit_data).execute()
            audit = result.data[0]
            
            # Trigger background processing (Celery if Redis available, else in-process)
            try:
                from app.tasks.audit_tasks import process_audit_task
                process_audit_task.delay(audit['id'])
            except Exception as e:
                logger.warning(f"Celery/Redis unavailable ({e}), running audit in-process")
                asyncio.create_task(self.process_audit(audit['id']))
            
            return audit
            
        except Exception as e:
            logger.error(f"Audit creation error: {str(e)}")
            raise
    
    async def process_audit(self, audit_id: str) -> Dict:
        """Main audit processing logic"""
        
        start_time = datetime.utcnow()
        
        try:
            # Update status
            self.supabase.table('audits').update({
                "status": "processing"
            }).eq('id', audit_id).execute()
            
            # Get audit and business data
            audit_result = self.supabase.table('audits').select(
                '*, businesses(*)'
            ).eq('id', audit_id).execute()
            
            audit = audit_result.data[0]
            business = audit['businesses']
            
            # Step 1: Fetch reviews
            logger.info(f"Fetching reviews for {business['place_id']}")
            reviews = outscraper_service.get_reviews(business['place_id'], limit=100)
            
            # Save reviews
            await self._save_reviews(business['id'], reviews)
            
            # Step 2: AI Perception Analysis
            logger.info("Running AI perception analysis")
            ai_perception = gemini_service.analyze_business_perception(business, reviews)
            
            # Step 3: Sentiment Gap Analysis
            logger.info("Running sentiment analysis")
            sentiment_analysis = gemini_service.analyze_sentiment_gaps(business, reviews)
            
            # Step 4: Conversational Query Generation
            logger.info("Generating conversational queries")
            conversational_queries = gemini_service.generate_conversational_queries(business)
            
            # Step 5: Visual Coverage Audit
            logger.info("Analyzing visual coverage")
            photo_urls = business.get('photos') or business.get('raw_data', {}).get('photos_data', []) or []
            visual_audit = gemini_service.analyze_photo_coverage(business, photo_urls)
            
            # Step 6: Calculate Discovery Score
            discovery_score = calculate_discovery_score(
                ai_perception,
                sentiment_analysis,
                visual_audit,
                business
            )
            
            score_interpretation = get_score_interpretation(discovery_score)
            
            # Step 7: Generate Recommendations
            recommendations = generate_priority_recommendations(
                discovery_score,
                ai_perception,
                sentiment_analysis,
                visual_audit,
                business
            )
            
            # Step 8: Calculate sentiment score
            topics = sentiment_analysis.get('topics', {})
            sentiment_score = sum(topics.values()) / len(topics) if topics else 0.5
            
            # Processing time
            processing_time = int((datetime.utcnow() - start_time).total_seconds())
            
            # Step 9: Update audit with results
            update_data = {
                "status": "completed",
                "discovery_score": discovery_score,
                "sentiment_score": sentiment_score,
                "visual_coverage_score": visual_audit.get('coverage_score', 0.0),
                "ai_summary": ai_perception,
                "sentiment_analysis": sentiment_analysis,
                "conversational_queries": conversational_queries,
                "visual_audit": visual_audit,
                "recommendations": recommendations,
                "processing_time_seconds": processing_time,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table('audits').update(
                update_data
            ).eq('id', audit_id).execute()
            
            completed_audit = result.data[0]
            
            logger.info(f"Audit {audit_id} completed in {processing_time}s")
            
            return completed_audit
            
        except Exception as e:
            logger.error(f"Audit processing error: {str(e)}")
            
            self.supabase.table('audits').update({
                "status": "failed",
                "error_message": str(e),
                "updated_at": datetime.utcnow().isoformat()
            }).eq('id', audit_id).execute()
            
            raise
    
    async def get_audit_status(self, audit_id: str) -> Dict:
        """Get current status of an audit"""
        
        result = self.supabase.table('audits').select(
            '*, businesses(*)'
        ).eq('id', audit_id).execute()
        
        if not result.data:
            raise ValueError(f"Audit {audit_id} not found")
        
        return result.data[0]
    
    async def _check_existing_audit(
        self,
        business_name: str,
        location: str
    ) -> Optional[Dict]:
        """Check for recent audit (< 24h)"""
        
        business_data = outscraper_service.search_business(business_name, location)
        if not business_data:
            return None
        
        place_id = business_data.get('place_id')
        cutoff = datetime.utcnow() - timedelta(hours=24)
        
        result = self.supabase.table('audits').select(
            '*, businesses!inner(*)'
        ).eq('businesses.place_id', place_id).gte(
            'created_at', cutoff.isoformat()
        ).eq('status', 'completed').order(
            'created_at', desc=True
        ).limit(1).execute()
        
        return result.data[0] if result.data else None
    
    async def _save_business(self, business_data: Dict) -> Dict:
        """Save or update business in database"""
        
        place_id = business_data['place_id']
        
        existing = self.supabase.table('businesses').select(
            '*'
        ).eq('place_id', place_id).execute()
        
        if existing.data:
            result = self.supabase.table('businesses').update({
                **business_data,
                "updated_at": datetime.utcnow().isoformat()
            }).eq('place_id', place_id).execute()
            
            return result.data[0]
        else:
            result = self.supabase.table('businesses').insert(
                business_data
            ).execute()
            
            return result.data[0]
    
    async def _save_reviews(self, business_id: str, reviews: list) -> None:
        """Save reviews to database"""
        
        if not reviews:
            return
        
        review_records = [
            {**review, "business_id": business_id}
            for review in reviews
        ]
        
        try:
            self.supabase.table('reviews').insert(
                review_records
            ).execute()
        except Exception as e:
            logger.warning(f"Some reviews already exist: {str(e)}")

# Singleton instance
audit_service = AuditService()
