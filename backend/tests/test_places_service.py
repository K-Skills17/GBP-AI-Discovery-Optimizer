"""Tests for app.services.places_service — internal helper methods that perform
pure data transformation without making network requests.

Tested methods:
    PlacesService._normalize_place
    PlacesService._normalize_review
    PlacesService._map_category_to_type
    PlacesService._photo_uri
"""

import pytest
from unittest.mock import patch, MagicMock

# Patch settings before importing the module under test so that PlacesService.__init__
# does not fail when GOOGLE_PLACES_API_KEY is a dummy value.
with patch("app.services.places_service.get_settings") as _mock_settings:
    _mock_settings.return_value = MagicMock(GOOGLE_PLACES_API_KEY="fake-key")
    from app.services.places_service import PlacesService


@pytest.fixture
def places_svc():
    """Return a PlacesService instance with a fake API key."""
    with patch("app.services.places_service.settings", MagicMock(GOOGLE_PLACES_API_KEY="fake-key")):
        svc = PlacesService()
    return svc


# ========================================================================
# _normalize_place
# ========================================================================


class TestNormalizePlace:
    """Convert a raw Places API (New) response to the internal schema."""

    def test_full_place_normalisation(self, places_svc, raw_places_api_place):
        result = places_svc._normalize_place(raw_places_api_place, city="Campinas")

        assert result["place_id"] == "places/ChIJraw123"
        assert result["name"] == "Clinica Exemplo"
        assert result["address"] == "Rua Exemplo, 42, Campinas, SP, Brasil"
        assert result["city"] == "Campinas"
        assert result["state"] == "SP"
        assert result["category"] == "Dentista"
        assert result["phone"] == "(19) 3333-4444"
        assert result["website"] == "https://exemplo.com.br"
        assert result["rating"] == 4.3
        assert result["total_reviews"] == 95
        assert result["claimed"] is True  # businessStatus == "OPERATIONAL"
        assert result["latitude"] == -22.9064
        assert result["longitude"] == -47.0616
        assert result["description"] == "Clinica de referencia em odontologia."
        assert isinstance(result["hours"], list)
        assert len(result["hours"]) == 2
        assert isinstance(result["photos"], list)
        assert result["photos_count"] == 2
        assert result["google_maps_url"] == "https://maps.google.com/?cid=999"
        assert "raw_data" in result

    def test_minimal_place(self, places_svc):
        """A place with almost no data should still normalise without errors."""
        minimal = {"id": "places/min1"}
        result = places_svc._normalize_place(minimal)

        assert result["place_id"] == "places/min1"
        assert result["name"] == ""
        assert result["rating"] is None
        assert result["total_reviews"] == 0
        assert result["website"] is None
        assert result["claimed"] is False  # businessStatus != "OPERATIONAL"
        assert result["photos"] == []
        assert result["photos_count"] == 0

    def test_city_extracted_from_address_components(self, places_svc):
        """City and state are pulled from addressComponents when present."""
        place = {
            "id": "p1",
            "addressComponents": [
                {"longText": "Recife", "shortText": "Recife", "types": ["administrative_area_level_2"]},
                {"longText": "Pernambuco", "shortText": "PE", "types": ["administrative_area_level_1"]},
            ],
        }
        result = places_svc._normalize_place(place, city="FallbackCity")
        assert result["city"] == "Recife"
        assert result["state"] == "PE"

    def test_city_falls_back_to_parameter(self, places_svc):
        """When no addressComponents, the city parameter is used as fallback."""
        place = {"id": "p2"}
        result = places_svc._normalize_place(place, city="Curitiba")
        assert result["city"] == "Curitiba"
        assert result["state"] == ""

    def test_claimed_false_when_not_operational(self, places_svc):
        place = {"id": "p3", "businessStatus": "CLOSED_TEMPORARILY"}
        result = places_svc._normalize_place(place)
        assert result["claimed"] is False

    def test_photos_limited_to_20(self, places_svc):
        """Only first 20 photos are included."""
        photos = [{"name": f"photo_{i}"} for i in range(30)]
        place = {"id": "p4", "photos": photos}
        result = places_svc._normalize_place(place)
        assert len(result["photos"]) == 20
        assert result["photos_count"] == 30

    def test_hours_none_when_missing(self, places_svc):
        """hours is None when currentOpeningHours is absent."""
        place = {"id": "p5"}
        result = places_svc._normalize_place(place)
        assert result["hours"] is None

    def test_display_name_text_used(self, places_svc):
        place = {"id": "p6", "displayName": {"text": "Minha Clinica", "languageCode": "pt-BR"}}
        result = places_svc._normalize_place(place)
        assert result["name"] == "Minha Clinica"

    def test_editorial_summary_used_for_description(self, places_svc):
        place = {"id": "p7", "editorialSummary": {"text": "A great place."}}
        result = places_svc._normalize_place(place)
        assert result["description"] == "A great place."

    def test_primary_type_display_name_preferred(self, places_svc):
        """primaryTypeDisplayName.text is preferred over primaryType."""
        place = {
            "id": "p8",
            "primaryTypeDisplayName": {"text": "Restaurante"},
            "primaryType": "restaurant",
        }
        result = places_svc._normalize_place(place)
        assert result["category"] == "Restaurante"

    def test_primary_type_fallback(self, places_svc):
        """primaryType is used when primaryTypeDisplayName is absent."""
        place = {"id": "p9", "primaryType": "gym"}
        result = places_svc._normalize_place(place)
        assert result["category"] == "gym"


# ========================================================================
# _normalize_review
# ========================================================================


class TestNormalizeReview:
    """Convert a raw Places API review to our internal schema."""

    def test_full_review_normalisation(self, places_svc, raw_places_api_review):
        result = places_svc._normalize_review(raw_places_api_review)

        assert result["author_name"] == "Joao Silva"
        assert result["author_url"] == "https://maps.google.com/contrib/12345"
        assert result["rating"] == 5
        assert result["text"] == "Otimo atendimento, super recomendo!"
        assert result["published_at"] == "2024-06-15T14:30:00Z"
        assert result["owner_reply"] is None  # flagContentUri is None
        assert result["owner_reply_at"] is None
        assert result["likes"] is None
        assert result["photos"] == []

    def test_anonymous_author_fallback(self, places_svc):
        review = {"rating": 3, "text": {"text": "OK"}}
        result = places_svc._normalize_review(review)
        assert result["author_name"] == "An\u00f4nimo"
        assert result["author_url"] is None

    def test_empty_review_text(self, places_svc):
        review = {"rating": 4}
        result = places_svc._normalize_review(review)
        assert result["text"] == ""
        assert result["rating"] == 4

    def test_review_default_rating(self, places_svc):
        review = {}
        result = places_svc._normalize_review(review)
        assert result["rating"] == 0


# ========================================================================
# _map_category_to_type
# ========================================================================


class TestMapCategoryToType:
    """Map Portuguese business category names to Google Places API types."""

    @pytest.mark.parametrize(
        "category, expected_type",
        [
            ("dentista", "dentist"),
            ("Dentista", "dentist"),
            ("cl\u00ednica odontol\u00f3gica", "dentist"),
            ("odontologia", "dentist"),
            ("m\u00e9dico", "doctor"),
            ("cl\u00ednica m\u00e9dica", "doctor"),
            ("hospital", "hospital"),
            ("farm\u00e1cia", "pharmacy"),
            ("restaurante", "restaurant"),
            ("advogado", "lawyer"),
            ("escrit\u00f3rio de advocacia", "lawyer"),
            ("academia", "gym"),
            ("sal\u00e3o de beleza", "beauty_salon"),
            ("barbearia", "hair_care"),
            ("veterin\u00e1rio", "veterinary_care"),
            ("cl\u00ednica veterin\u00e1ria", "veterinary_care"),
            ("imobili\u00e1ria", "real_estate_agency"),
            ("hotel", "lodging"),
            ("escola", "school"),
            ("pet shop", "pet_store"),
            ("\u00f3tica", "optician"),
        ],
    )
    def test_known_categories(self, category, expected_type):
        assert PlacesService._map_category_to_type(category) == expected_type

    def test_unknown_category_returns_establishment(self):
        assert PlacesService._map_category_to_type("padaria") == "establishment"

    def test_empty_category_returns_establishment(self):
        assert PlacesService._map_category_to_type("") == "establishment"

    def test_none_category_returns_establishment(self):
        assert PlacesService._map_category_to_type(None) == "establishment"

    def test_case_insensitive(self):
        assert PlacesService._map_category_to_type("DENTISTA") == "dentist"
        assert PlacesService._map_category_to_type("Hospital") == "hospital"

    def test_substring_match(self):
        """Mapping uses 'in' operator, so partial match works."""
        assert PlacesService._map_category_to_type("meu dentista favorito") == "dentist"


# ========================================================================
# _photo_uri
# ========================================================================


class TestPhotoUri:
    def test_returns_name_field(self):
        photo = {"name": "places/abc/photos/xyz"}
        assert PlacesService._photo_uri(photo) == "places/abc/photos/xyz"

    def test_missing_name_returns_empty(self):
        assert PlacesService._photo_uri({}) == ""
