"""Google Places API (New) service — replaces Outscraper for business data."""

import logging
from typing import Dict, List, Optional

import httpx

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

PLACES_BASE = "https://places.googleapis.com/v1"

# Field masks control billing — only request what we need
BUSINESS_FIELDS = (
    "places.id,places.displayName,places.formattedAddress,places.addressComponents,"
    "places.location,places.rating,places.userRatingCount,places.websiteUri,"
    "places.nationalPhoneNumber,places.primaryType,places.primaryTypeDisplayName,"
    "places.businessStatus,places.currentOpeningHours,places.photos,"
    "places.editorialSummary,places.googleMapsUri"
)

DETAIL_FIELDS = (
    "id,displayName,formattedAddress,addressComponents,location,rating,"
    "userRatingCount,websiteUri,nationalPhoneNumber,primaryType,"
    "primaryTypeDisplayName,businessStatus,currentOpeningHours,photos,"
    "editorialSummary,googleMapsUri,reviews"
)

NEARBY_FIELDS = (
    "places.id,places.displayName,places.formattedAddress,places.location,"
    "places.rating,places.userRatingCount,places.websiteUri,places.photos,"
    "places.primaryType,places.primaryTypeDisplayName,places.googleMapsUri"
)


class PlacesService:
    """Google Places API (New) client for business search and competitor discovery."""

    def __init__(self):
        self.api_key = settings.GOOGLE_PLACES_API_KEY
        self.headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
        }

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    async def search_business(
        self, business_name: str, city: str
    ) -> Optional[Dict]:
        """Find a business by name + city using Text Search."""
        query = f"{business_name}, {city}, Brasil"
        headers = {**self.headers, "X-Goog-FieldMask": BUSINESS_FIELDS}
        body = {
            "textQuery": query,
            "languageCode": "pt-BR",
            "regionCode": "BR",
            "maxResultCount": 1,
        }

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{PLACES_BASE}/places:searchText",
                    headers=headers,
                    json=body,
                )
                resp.raise_for_status()
                data = resp.json()

            places = data.get("places", [])
            if not places:
                return None
            return self._normalize_place(places[0], city=city)

        except Exception as e:
            logger.error(f"Places search error: {e}")
            raise

    async def get_business_details(self, place_id: str) -> Optional[Dict]:
        """Fetch full details for a single place (including reviews)."""
        headers = {**self.headers, "X-Goog-FieldMask": DETAIL_FIELDS}

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"{PLACES_BASE}/{place_id}",
                    headers=headers,
                )
                resp.raise_for_status()
                return resp.json()

        except Exception as e:
            logger.error(f"Places detail error for {place_id}: {e}")
            return None

    async def get_business_reviews(
        self, place_id: str, max_results: int = 100
    ) -> List[Dict]:
        """Fetch reviews for a business via Place Details.

        The Places API (New) returns up to 5 reviews in the details call.
        For more reviews we do a single detail call and return what we get.
        """
        details = await self.get_business_details(place_id)
        if not details:
            return []

        raw_reviews = details.get("reviews", [])
        return [self._normalize_review(r) for r in raw_reviews[:max_results]]

    async def find_competitors(
        self,
        category: str,
        lat: float,
        lng: float,
        city: str,
        radius_m: int = 5000,
        limit: int = 5,
        exclude_place_id: Optional[str] = None,
    ) -> List[Dict]:
        """Find top competitors in the same category/area using Nearby Search."""
        headers = {**self.headers, "X-Goog-FieldMask": NEARBY_FIELDS}
        body = {
            "includedTypes": [self._map_category_to_type(category)],
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lng},
                    "radius": float(radius_m),
                }
            },
            "rankPreference": "POPULARITY",
            "maxResultCount": limit + 3,  # extra buffer to filter self
            "languageCode": "pt-BR",
            "regionCode": "BR",
        }

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{PLACES_BASE}/places:searchNearby",
                    headers=headers,
                    json=body,
                )
                resp.raise_for_status()
                data = resp.json()

            places = data.get("places", [])
            competitors = []
            for p in places:
                pid = p.get("id", "")
                if exclude_place_id and pid == exclude_place_id:
                    continue
                competitors.append(self._normalize_place(p, city=city))
                if len(competitors) >= limit:
                    break
            return competitors

        except Exception as e:
            logger.error(f"Nearby search error: {e}")
            return []

    async def find_competitors_text(
        self,
        category: str,
        city: str,
        limit: int = 5,
        exclude_place_id: Optional[str] = None,
    ) -> List[Dict]:
        """Fallback: find competitors via Text Search when lat/lng unavailable."""
        query = f"melhor {category} em {city}, Brasil"
        headers = {**self.headers, "X-Goog-FieldMask": BUSINESS_FIELDS}
        body = {
            "textQuery": query,
            "languageCode": "pt-BR",
            "regionCode": "BR",
            "maxResultCount": limit + 3,
        }

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{PLACES_BASE}/places:searchText",
                    headers=headers,
                    json=body,
                )
                resp.raise_for_status()
                data = resp.json()

            places = data.get("places", [])
            competitors = []
            for p in places:
                pid = p.get("id", "")
                if exclude_place_id and pid == exclude_place_id:
                    continue
                competitors.append(self._normalize_place(p, city=city))
                if len(competitors) >= limit:
                    break
            return competitors

        except Exception as e:
            logger.error(f"Text competitor search error: {e}")
            return []

    # ------------------------------------------------------------------
    # Normalization helpers
    # ------------------------------------------------------------------

    def _normalize_place(self, place: Dict, city: str = "") -> Dict:
        """Convert Places API (New) response to our internal schema."""
        display_name = place.get("displayName", {})
        editorial = place.get("editorialSummary", {})
        location = place.get("location", {})
        photos = place.get("photos", [])
        address_parts = place.get("addressComponents", [])

        # Extract city/state from address components
        extracted_city = city
        extracted_state = ""
        for comp in address_parts:
            types = comp.get("types", [])
            if "administrative_area_level_2" in types:
                extracted_city = comp.get("longText", city)
            if "administrative_area_level_1" in types:
                extracted_state = comp.get("shortText", "")

        hours_data = place.get("currentOpeningHours", {})
        weekday_descriptions = hours_data.get("weekdayDescriptions", [])

        return {
            "place_id": place.get("id", ""),
            "name": display_name.get("text", ""),
            "address": place.get("formattedAddress", ""),
            "city": extracted_city,
            "state": extracted_state,
            "category": (
                place.get("primaryTypeDisplayName", {}).get("text", "")
                or place.get("primaryType", "")
            ),
            "phone": place.get("nationalPhoneNumber"),
            "website": place.get("websiteUri"),
            "rating": place.get("rating"),
            "total_reviews": place.get("userRatingCount", 0),
            "claimed": place.get("businessStatus") == "OPERATIONAL",
            "latitude": location.get("latitude"),
            "longitude": location.get("longitude"),
            "description": editorial.get("text"),
            "hours": weekday_descriptions if weekday_descriptions else None,
            "photos": [self._photo_uri(p) for p in photos[:20]],
            "photos_count": len(photos),
            "google_maps_url": place.get("googleMapsUri"),
            "raw_data": place,
        }

    def _normalize_review(self, review: Dict) -> Dict:
        """Convert Places API review to our internal schema."""
        author = review.get("authorAttribution", {})
        return {
            "author_name": author.get("displayName", "Anônimo"),
            "author_url": author.get("uri"),
            "rating": review.get("rating", 0),
            "text": review.get("text", {}).get("text", ""),
            "published_at": review.get("publishTime"),
            "owner_reply": (
                review.get("authorAttribution", {}).get("text")
                if review.get("flagContentUri")
                else None
            ),
            "owner_reply_at": None,
            "likes": None,
            "photos": [],
        }

    @staticmethod
    def _photo_uri(photo: Dict) -> str:
        """Build photo reference string from Places API photo object."""
        return photo.get("name", "")

    @staticmethod
    def _map_category_to_type(category: str) -> str:
        """Map Portuguese category names to Places API types."""
        cat = (category or "").lower()
        mapping = {
            "dentista": "dentist",
            "clínica odontológica": "dentist",
            "odontologia": "dentist",
            "médico": "doctor",
            "clínica médica": "doctor",
            "hospital": "hospital",
            "farmácia": "pharmacy",
            "restaurante": "restaurant",
            "advogado": "lawyer",
            "escritório de advocacia": "lawyer",
            "academia": "gym",
            "salão de beleza": "beauty_salon",
            "barbearia": "hair_care",
            "veterinário": "veterinary_care",
            "clínica veterinária": "veterinary_care",
            "imobiliária": "real_estate_agency",
            "hotel": "lodging",
            "escola": "school",
            "pet shop": "pet_store",
            "ótica": "optician",
        }
        for key, value in mapping.items():
            if key in cat:
                return value
        # Default: try the category as-is or generic establishment
        return "establishment"


# Singleton
places_service = PlacesService()
