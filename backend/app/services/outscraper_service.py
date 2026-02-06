import logging
from typing import Dict, List, Optional
from outscraper import ApiClient
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class OutscraperService:
    def __init__(self):
        self.client = ApiClient(api_key=settings.OUTSCRAPER_API_KEY)
    
    def search_business(self, business_name: str, location: str) -> Optional[Dict]:
        """
        Search for a business on Google Maps
        
        Args:
            business_name: Name of the business
            location: City/region to search in
            
        Returns:
            First matching business data or None
        """
        try:
            query = f"{business_name}, {location}, Brasil"
            results = self.client.google_maps_search(
                query=query,
                limit=1,
                language='pt',
                region='br'
            )
            
            if results and len(results) > 0 and len(results[0]) > 0:
                return self._normalize_business_data(results[0][0])
            
            return None
            
        except Exception as e:
            logger.error(f"Outscraper search error: {str(e)}")
            raise
    
    def get_business_by_place_id(self, place_id: str) -> Optional[Dict]:
        """Get business data by Google Place ID"""
        try:
            results = self.client.google_maps_search(
                query=f"place_id:{place_id}",
                limit=1,
                language='pt',
                region='br'
            )
            
            if results and len(results) > 0 and len(results[0]) > 0:
                return self._normalize_business_data(results[0][0])
            
            return None
            
        except Exception as e:
            logger.error(f"Outscraper place_id lookup error: {str(e)}")
            raise
    
    def get_reviews(self, place_id: str, limit: int = 100) -> List[Dict]:
        """
        Get reviews for a business
        
        Args:
            place_id: Google Place ID
            limit: Maximum number of reviews to fetch
            
        Returns:
            List of review dictionaries
        """
        try:
            results = self.client.google_maps_reviews(
                query=place_id,
                reviews_limit=limit,
                limit=1,
                sort='newest',
                language='pt',
                region='br',
                cutoff_rating=1  # Include all ratings
            )
            
            if not results or len(results) == 0:
                return []
            
            reviews = results[0].get('reviews_data', [])
            return [self._normalize_review_data(r) for r in reviews]
            
        except Exception as e:
            logger.error(f"Outscraper reviews error: {str(e)}")
            return []
    
    def _normalize_business_data(self, raw_data: Dict) -> Dict:
        """Normalize Outscraper business data for Supabase businesses table (full scrape data)."""
        photos = raw_data.get('photos_data', [])[:20] if raw_data.get('photos_data') else []
        return {
            'place_id': raw_data.get('place_id'),
            'name': raw_data.get('name'),
            'address': raw_data.get('full_address') or raw_data.get('address'),
            'city': raw_data.get('city'),
            'state': raw_data.get('state') or 'SP',
            'category': raw_data.get('type') or raw_data.get('category'),
            'phone': raw_data.get('phone'),
            'website': raw_data.get('site'),
            'rating': float(raw_data.get('rating', 0)) if raw_data.get('rating') else None,
            'total_reviews': int(raw_data.get('reviews', 0)),
            'claimed': raw_data.get('owner_title') is not None,
            'latitude': float(raw_data.get('latitude')) if raw_data.get('latitude') else None,
            'longitude': float(raw_data.get('longitude')) if raw_data.get('longitude') else None,
            'description': raw_data.get('description'),
            'hours': raw_data.get('working_hours'),
            'photos': photos,
            'questions_and_answers': raw_data.get('questions_and_answers', []),
            'raw_data': raw_data,
        }
    
    def _normalize_review_data(self, raw_review: Dict) -> Dict:
        """Normalize Outscraper review data"""
        return {
            'author_name': raw_review.get('author_title'),
            'author_url': raw_review.get('author_link'),
            'rating': int(raw_review.get('review_rating', 0)),
            'text': raw_review.get('review_text'),
            'published_at': raw_review.get('review_datetime_utc'),
            'owner_reply': raw_review.get('owner_answer'),
            'owner_reply_at': raw_review.get('owner_answer_timestamp_datetime_utc'),
            'likes': raw_review.get('review_likes'),
            'photos': raw_review.get('review_photos', [])
        }

# Singleton instance
outscraper_service = OutscraperService()
