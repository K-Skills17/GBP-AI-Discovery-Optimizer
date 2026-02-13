"""Tests for app.services.competitor_service — internal helper methods that
perform pure data transformation and comparison logic.

Tested methods:
    CompetitorService._build_comparison_matrix
    CompetitorService._identify_gaps
    CompetitorService._calculate_competitive_score
    CompetitorService._empty_result
"""

import pytest
from unittest.mock import patch, MagicMock

# Patch the service-level singletons that are imported at module load time so
# we never touch real Google/Gemini APIs.
with patch("app.services.competitor_service.places_service", MagicMock()), \
     patch("app.services.competitor_service.gemini_service", MagicMock()):
    from app.services.competitor_service import CompetitorService


@pytest.fixture
def svc():
    return CompetitorService()


# ========================================================================
# _build_comparison_matrix
# ========================================================================


class TestBuildComparisonMatrix:
    """Side-by-side comparison of business vs. competitor averages."""

    def test_basic_matrix(self, svc, sample_business_data, sample_competitors):
        matrix = svc._build_comparison_matrix(sample_business_data, sample_competitors)

        assert "your_business" in matrix
        assert "competitor_average" in matrix
        assert "top_competitors" in matrix

        biz = matrix["your_business"]
        assert biz["name"] == "Clinica Sorriso"
        assert biz["rating"] == 4.5
        assert biz["total_reviews"] == 120
        assert biz["has_website"] is True

    def test_competitor_averages(self, svc, sample_business_data, sample_competitors):
        matrix = svc._build_comparison_matrix(sample_business_data, sample_competitors)
        avg = matrix["competitor_average"]

        # Competitors: ratings [4.8, 4.2, 4.0], reviews [250, 80, 40], photos [5, 1, 2]
        expected_avg_rating = round((4.8 + 4.2 + 4.0) / 3, 1)  # 4.3
        expected_avg_reviews = int((250 + 80 + 40) / 3)  # 123
        expected_avg_photos = int((5 + 1 + 2) / 3)  # 2

        assert avg["rating"] == expected_avg_rating
        assert avg["total_reviews"] == expected_avg_reviews
        assert avg["photos_count"] == expected_avg_photos

    def test_top_competitors_limited_to_3(self, svc, sample_business_data):
        """Only first 3 competitors appear in top_competitors."""
        many_competitors = [
            {
                "name": f"Comp{i}",
                "rating": 4.0,
                "total_reviews": 100,
                "photos_count": 3,
                "website": "https://x.com",
            }
            for i in range(10)
        ]
        matrix = svc._build_comparison_matrix(sample_business_data, many_competitors)
        assert len(matrix["top_competitors"]) == 3

    def test_business_photos_count_from_photos_list(self, svc, sample_competitors):
        """When business has no photos_count, len(photos) is used."""
        business = {
            "name": "Test Biz",
            "rating": 4.0,
            "total_reviews": 50,
            "photos": ["a", "b", "c", "d"],
            "website": None,
        }
        matrix = svc._build_comparison_matrix(business, sample_competitors)
        assert matrix["your_business"]["photos_count"] == 4
        assert matrix["your_business"]["has_website"] is False

    def test_empty_competitor_list(self, svc, sample_business_data):
        """Empty competitor list should not raise; averages should be 0."""
        matrix = svc._build_comparison_matrix(sample_business_data, [])
        assert matrix["competitor_average"]["rating"] == 0
        assert matrix["competitor_average"]["total_reviews"] == 0
        assert matrix["top_competitors"] == []

    def test_competitors_with_none_values(self, svc, sample_business_data):
        """Competitors with None values should be treated as 0."""
        competitors = [
            {"name": "C1", "rating": None, "total_reviews": None, "photos_count": None, "website": None},
        ]
        matrix = svc._build_comparison_matrix(sample_business_data, competitors)
        assert matrix["competitor_average"]["rating"] == 0
        assert matrix["competitor_average"]["total_reviews"] == 0
        assert matrix["competitor_average"]["photos_count"] == 0


# ========================================================================
# _identify_gaps
# ========================================================================


class TestIdentifyGaps:
    """Produce actionable gap statements comparing business to competitors."""

    def test_review_gap_high_severity(self, svc):
        """Business with far fewer reviews than competitors -> high severity."""
        business = {"name": "Biz", "total_reviews": 10, "rating": 4.5, "photos": []}
        competitors = [
            {"total_reviews": 100, "rating": 4.0, "photos_count": 5, "website": "https://x.com"},
            {"total_reviews": 80, "rating": 4.2, "photos_count": 3, "website": None},
        ]
        ai_mentions = {}

        gaps = svc._identify_gaps(business, competitors, ai_mentions)
        review_gaps = [g for g in gaps if g["type"] == "reviews"]
        assert len(review_gaps) == 1
        assert review_gaps[0]["severity"] == "high"  # 10 < 90 * 0.5

    def test_review_gap_medium_severity(self, svc):
        """Business slightly below competitor average -> medium severity."""
        business = {"name": "Biz", "total_reviews": 80, "rating": 4.5, "photos": []}
        competitors = [
            {"total_reviews": 100, "rating": 4.0, "photos_count": 5, "website": None},
            {"total_reviews": 120, "rating": 4.0, "photos_count": 5, "website": None},
        ]
        ai_mentions = {}

        gaps = svc._identify_gaps(business, competitors, ai_mentions)
        review_gaps = [g for g in gaps if g["type"] == "reviews"]
        assert len(review_gaps) == 1
        assert review_gaps[0]["severity"] == "medium"

    def test_no_review_gap_when_above_average(self, svc):
        business = {"name": "Biz", "total_reviews": 200, "rating": 4.5, "photos": []}
        competitors = [
            {"total_reviews": 50, "rating": 4.0, "photos_count": 5, "website": None},
        ]
        gaps = svc._identify_gaps(business, competitors, {})
        review_gaps = [g for g in gaps if g["type"] == "reviews"]
        assert len(review_gaps) == 0

    def test_rating_gap(self, svc):
        business = {"name": "Biz", "total_reviews": 50, "rating": 3.5, "photos": []}
        competitors = [
            {"total_reviews": 50, "rating": 4.5, "photos_count": 5, "website": None},
            {"total_reviews": 50, "rating": 4.3, "photos_count": 5, "website": None},
        ]
        gaps = svc._identify_gaps(business, competitors, {})
        rating_gaps = [g for g in gaps if g["type"] == "rating"]
        assert len(rating_gaps) == 1
        # avg_rating = (4.5+4.3)/2 = 4.4, biz_rating 3.5 < 4.4-0.5 -> high
        assert rating_gaps[0]["severity"] == "high"

    def test_no_rating_gap_when_equal(self, svc):
        business = {"name": "Biz", "total_reviews": 50, "rating": 4.5, "photos": []}
        competitors = [
            {"total_reviews": 50, "rating": 4.5, "photos_count": 5, "website": None},
        ]
        gaps = svc._identify_gaps(business, competitors, {})
        rating_gaps = [g for g in gaps if g["type"] == "rating"]
        assert len(rating_gaps) == 0

    def test_photo_gap(self, svc):
        business = {"name": "Biz", "total_reviews": 50, "rating": 4.5, "photos": ["p1"]}
        competitors = [
            {"total_reviews": 50, "rating": 4.0, "photos_count": 10, "website": None},
            {"total_reviews": 50, "rating": 4.0, "photos_count": 8, "website": None},
        ]
        gaps = svc._identify_gaps(business, competitors, {})
        photo_gaps = [g for g in gaps if g["type"] == "photos"]
        assert len(photo_gaps) == 1
        assert photo_gaps[0]["severity"] == "medium"

    def test_ai_visibility_gap(self, svc):
        """AI mentions competitors but not the business -> ai_visibility gap."""
        business = {"name": "MyBiz", "total_reviews": 50, "rating": 4.5, "photos": []}
        competitors = [
            {"total_reviews": 50, "rating": 4.0, "photos_count": 5, "website": None},
        ]
        ai_mentions = {"MyBiz": False, "CompA": True}

        gaps = svc._identify_gaps(business, competitors, ai_mentions)
        ai_gaps = [g for g in gaps if g["type"] == "ai_visibility"]
        assert len(ai_gaps) == 1
        assert ai_gaps[0]["severity"] == "high"

    def test_no_ai_visibility_gap_when_mentioned(self, svc):
        business = {"name": "MyBiz", "total_reviews": 50, "rating": 4.5, "photos": []}
        competitors = [
            {"total_reviews": 50, "rating": 4.0, "photos_count": 5, "website": None},
        ]
        ai_mentions = {"MyBiz": True, "CompA": True}

        gaps = svc._identify_gaps(business, competitors, ai_mentions)
        ai_gaps = [g for g in gaps if g["type"] == "ai_visibility"]
        assert len(ai_gaps) == 0

    def test_website_gap(self, svc):
        """Business has no website but competitors do -> website gap."""
        business = {"name": "Biz", "total_reviews": 50, "rating": 4.5, "photos": []}
        competitors = [
            {"total_reviews": 50, "rating": 4.0, "photos_count": 5, "website": "https://a.com"},
            {"total_reviews": 50, "rating": 4.0, "photos_count": 5, "website": "https://b.com"},
        ]
        gaps = svc._identify_gaps(business, competitors, {})
        web_gaps = [g for g in gaps if g["type"] == "website"]
        assert len(web_gaps) == 1
        assert web_gaps[0]["severity"] == "high"
        assert "2 de 2" in web_gaps[0]["message"]

    def test_no_website_gap_when_business_has_site(self, svc):
        business = {
            "name": "Biz", "total_reviews": 200, "rating": 4.5, "photos": ["p" * 20],
            "website": "https://mybiz.com",
        }
        competitors = [
            {"total_reviews": 50, "rating": 4.0, "photos_count": 5, "website": "https://a.com"},
        ]
        gaps = svc._identify_gaps(business, competitors, {})
        web_gaps = [g for g in gaps if g["type"] == "website"]
        assert len(web_gaps) == 0

    def test_no_website_gap_when_no_competitors_have_site(self, svc):
        business = {"name": "Biz", "total_reviews": 200, "rating": 4.5, "photos": []}
        competitors = [
            {"total_reviews": 50, "rating": 4.0, "photos_count": 0, "website": None},
        ]
        gaps = svc._identify_gaps(business, competitors, {})
        web_gaps = [g for g in gaps if g["type"] == "website"]
        assert len(web_gaps) == 0

    def test_multiple_gaps_together(self, svc):
        """A weak business should trigger multiple gaps at once."""
        business = {
            "name": "WeakBiz",
            "total_reviews": 5,
            "rating": 3.0,
            "photos": [],
        }
        competitors = [
            {"total_reviews": 200, "rating": 4.8, "photos_count": 20, "website": "https://a.com"},
            {"total_reviews": 150, "rating": 4.5, "photos_count": 15, "website": "https://b.com"},
        ]
        ai_mentions = {"WeakBiz": False, "CompA": True}

        gaps = svc._identify_gaps(business, competitors, ai_mentions)
        gap_types = {g["type"] for g in gaps}
        assert "reviews" in gap_types
        assert "rating" in gap_types
        assert "photos" in gap_types
        assert "ai_visibility" in gap_types
        assert "website" in gap_types

    def test_empty_competitors(self, svc):
        """No competitors -> no gaps (averages would be 0)."""
        business = {"name": "Biz", "total_reviews": 10, "rating": 4.0, "photos": []}
        gaps = svc._identify_gaps(business, [], {})
        assert gaps == []


# ========================================================================
# _calculate_competitive_score
# ========================================================================


class TestCalculateCompetitiveScore:
    """0-100 score for how the business compares to its competitors."""

    def test_no_competitors_returns_50(self, svc):
        score = svc._calculate_competitive_score({"name": "Biz"}, [], {})
        assert score == 50.0

    def test_business_equals_best_competitor(self, svc):
        """When business matches the top competitor in every metric -> near max."""
        business = {
            "name": "Biz",
            "rating": 5.0,
            "total_reviews": 200,
            "photos": ["p"] * 20,
            "website": "https://biz.com",
        }
        competitors = [
            {"rating": 5.0, "total_reviews": 200, "photos_count": 20},
        ]
        ai_mentions = {"Biz": True}

        score = svc._calculate_competitive_score(business, competitors, ai_mentions)
        # rating: (5/5)*30=30, reviews: (200/200)*30=30, photos: (20/20)*15=15,
        # ai: 15, website: 10 -> total 100
        assert score == 100.0

    def test_business_half_of_competitors(self, svc):
        """Business at half of competitor max in reviews and photos."""
        business = {
            "name": "Biz",
            "rating": 4.0,
            "total_reviews": 50,
            "photos": ["p"] * 5,
            "website": None,
        }
        competitors = [
            {"rating": 4.0, "total_reviews": 100, "photos_count": 10},
        ]
        ai_mentions = {}

        score = svc._calculate_competitive_score(business, competitors, ai_mentions)
        # rating: (4/4)*30=30, reviews: (50/100)*30=15, photos: (5/10)*15=7.5,
        # ai: 0, website: 0 -> 52.5
        assert score == 52.5

    def test_ai_mention_bonus(self, svc):
        """Being mentioned by AI adds 15 points."""
        business = {
            "name": "Biz",
            "rating": 0,
            "total_reviews": 0,
            "photos": [],
        }
        competitors = [
            {"rating": 5.0, "total_reviews": 100, "photos_count": 10},
        ]
        score_without = svc._calculate_competitive_score(business, competitors, {})
        score_with = svc._calculate_competitive_score(
            business, competitors, {"Biz": True}
        )
        assert score_with - score_without == 15

    def test_website_bonus(self, svc):
        """Having a website adds 10 points."""
        business = {
            "name": "Biz",
            "rating": 0,
            "total_reviews": 0,
            "photos": [],
        }
        competitors = [
            {"rating": 5.0, "total_reviews": 100, "photos_count": 10},
        ]
        score_without = svc._calculate_competitive_score(
            business, competitors, {}
        )
        business["website"] = "https://example.com"
        score_with = svc._calculate_competitive_score(
            business, competitors, {}
        )
        assert score_with - score_without == 10

    def test_score_clamped_to_100(self, svc):
        """Score never exceeds 100 even with inflated values."""
        business = {
            "name": "Biz",
            "rating": 5.0,
            "total_reviews": 9999,
            "photos": ["p"] * 100,
            "website": "https://biz.com",
        }
        competitors = [
            {"rating": 4.0, "total_reviews": 50, "photos_count": 5},
        ]
        score = svc._calculate_competitive_score(
            business, competitors, {"Biz": True}
        )
        assert score <= 100.0

    def test_score_never_negative(self, svc):
        """Score never goes below 0."""
        business = {
            "name": "Biz",
            "rating": 0,
            "total_reviews": 0,
            "photos": [],
        }
        competitors = [
            {"rating": 5.0, "total_reviews": 1000, "photos_count": 50},
        ]
        score = svc._calculate_competitive_score(business, competitors, {})
        assert score >= 0

    def test_competitors_with_none_values(self, svc):
        """Competitors with None metrics should be treated as 0."""
        business = {
            "name": "Biz",
            "rating": 4.0,
            "total_reviews": 50,
            "photos": ["p"] * 5,
        }
        competitors = [
            {"rating": None, "total_reviews": None, "photos_count": None},
        ]
        # All competitor maxes are 0 -> fallback logic avoids division by zero
        score = svc._calculate_competitive_score(business, competitors, {})
        assert score >= 0

    def test_score_is_float_rounded(self, svc):
        """Return value is a float rounded to 1 decimal place."""
        business = {
            "name": "Biz",
            "rating": 3.7,
            "total_reviews": 33,
            "photos": ["p"] * 3,
        }
        competitors = [
            {"rating": 4.5, "total_reviews": 100, "photos_count": 10},
        ]
        score = svc._calculate_competitive_score(business, competitors, {})
        assert isinstance(score, float)
        assert score == round(score, 1)


# ========================================================================
# _empty_result
# ========================================================================


class TestEmptyResult:
    def test_structure(self, svc):
        result = svc._empty_result()
        assert result["competitors"] == []
        assert result["comparison_matrix"] == {}
        assert result["gaps"] == []
        assert result["ai_mentions"] == {}
        assert result["competitive_score"] == 50.0
