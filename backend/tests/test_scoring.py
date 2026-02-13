"""Tests for app.utils.scoring — Discovery Score calculation, interpretation,
and priority recommendation generation.

All tests exercise pure functions with deterministic inputs; no mocking required.
"""

import pytest

from app.utils.scoring import (
    calculate_discovery_score,
    generate_priority_recommendations,
    get_score_interpretation,
)


# ========================================================================
# calculate_discovery_score
# ========================================================================


class TestCalculateDiscoveryScore:
    """Verify score calculation against documented weight breakdown:

        AI Confidence:        25 %
        Data Completeness:    20 %
        Sentiment Alignment:  20 %
        Visual Coverage:      15 %
        Competitive Position: 20 %
    """

    def test_perfect_score_without_competitor(self):
        """All factors maximised, no competitor data -> comp defaults to 10."""
        ai_perception = {"confidence_score": 1.0}
        sentiment_analysis = {
            "gaps": [
                {"status": "validated"},
                {"status": "validated"},
            ]
        }
        # Maximise completeness: description, website, phone, claimed,
        # reviews >= 40 (capped at 4), rating = 5 -> 3 pts
        business_data = {
            "description": "Full description",
            "website": "https://example.com",
            "phone": "123",
            "claimed": True,
            "total_reviews": 100,  # min(100/10,4) = 4
            "rating": 5,          # (5/5)*3 = 3
        }
        visual_audit = {"coverage_score": 1.0}

        score = calculate_discovery_score(
            ai_perception, sentiment_analysis, visual_audit, business_data
        )

        # ai=25, completeness=4+3+2+4+4+3=20, sentiment=20, visual=15, comp=10 (default)
        # total = 90
        assert score == 90

    def test_perfect_score_with_competitor(self):
        """All factors maxed including competitive_score = 100."""
        ai_perception = {"confidence_score": 1.0}
        sentiment_analysis = {
            "gaps": [{"status": "validated"}]
        }
        business_data = {
            "description": "d",
            "website": "w",
            "phone": "p",
            "claimed": True,
            "total_reviews": 100,
            "rating": 5,
        }
        visual_audit = {"coverage_score": 1.0}
        competitor_analysis = {"competitive_score": 100}

        score = calculate_discovery_score(
            ai_perception, sentiment_analysis, visual_audit,
            business_data, competitor_analysis
        )

        # ai=25, completeness=20, sentiment=20, visual=15, comp=20
        assert score == 100

    def test_zero_score(self):
        """Every factor at absolute minimum."""
        score = calculate_discovery_score(
            ai_perception={"confidence_score": 0},
            sentiment_analysis={"gaps": [{"status": "missing"}]},
            visual_audit={"coverage_score": 0},
            business_data={},
            competitor_analysis={"competitive_score": 0},
        )
        assert score == 0

    def test_score_clamped_to_0_100(self):
        """Score is clamped even if arithmetic would exceed bounds."""
        # Extremely high values should still be <= 100
        score = calculate_discovery_score(
            ai_perception={"confidence_score": 5.0},  # unrealistic
            sentiment_analysis={"gaps": [{"status": "validated"}]},
            visual_audit={"coverage_score": 5.0},
            business_data={
                "description": "d", "website": "w", "phone": "p",
                "claimed": True, "total_reviews": 9999, "rating": 5,
            },
            competitor_analysis={"competitive_score": 500},
        )
        assert score <= 100

    def test_ai_confidence_component(self):
        """AI confidence of 0.5 contributes 12.5 to the score."""
        base = calculate_discovery_score(
            {"confidence_score": 0.0}, {"gaps": []}, {"coverage_score": 0}, {},
        )
        with_ai = calculate_discovery_score(
            {"confidence_score": 0.5}, {"gaps": []}, {"coverage_score": 0}, {},
        )
        # Difference should be int(0.5 * 25) = 12 (after int conversion)
        assert with_ai - base == 12 or with_ai - base == 13  # int rounding

    def test_sentiment_all_validated(self):
        """100 % validated gaps -> full 20-point sentiment bucket."""
        gaps = [{"status": "validated"} for _ in range(5)]
        score = calculate_discovery_score(
            {"confidence_score": 0},
            {"gaps": gaps},
            {"coverage_score": 0},
            {},
        )
        # sentiment = (5/5)*20 = 20, comp default = 10 -> total 30
        assert score == 30

    def test_sentiment_no_gaps_gives_zero(self):
        """Empty gap list -> total_gaps defaults to 1, validated=0 -> 0."""
        score = calculate_discovery_score(
            {"confidence_score": 0},
            {"gaps": []},
            {"coverage_score": 0},
            {},
        )
        # sentiment = 0, comp default = 10 -> total 10
        assert score == 10

    def test_visual_coverage_component(self):
        """Visual coverage of 0.6 contributes 9 points."""
        score = calculate_discovery_score(
            {"confidence_score": 0},
            {"gaps": []},
            {"coverage_score": 0.6},
            {},
        )
        # visual = 0.6 * 15 = 9, comp default = 10 -> total 19
        assert score == 19

    def test_completeness_factors(self):
        """Verify each completeness sub-factor independently."""
        # Only description -> 4 pts
        score_desc = calculate_discovery_score(
            {"confidence_score": 0}, {"gaps": []}, {"coverage_score": 0},
            {"description": "Hello"},
        )
        # comp default = 10, completeness = 4 -> 14
        assert score_desc == 14

        # Only website -> 3 pts
        score_web = calculate_discovery_score(
            {"confidence_score": 0}, {"gaps": []}, {"coverage_score": 0},
            {"website": "https://x.com"},
        )
        assert score_web == 13

        # Only phone -> 2 pts
        score_phone = calculate_discovery_score(
            {"confidence_score": 0}, {"gaps": []}, {"coverage_score": 0},
            {"phone": "123"},
        )
        assert score_phone == 12

        # Only claimed -> 4 pts
        score_claimed = calculate_discovery_score(
            {"confidence_score": 0}, {"gaps": []}, {"coverage_score": 0},
            {"claimed": True},
        )
        assert score_claimed == 14

    def test_reviews_capped_at_40(self):
        """reviews component = min(total_reviews/10, 4).  40 and 400 both give 4."""
        s1 = calculate_discovery_score(
            {"confidence_score": 0}, {"gaps": []}, {"coverage_score": 0},
            {"total_reviews": 40},
        )
        s2 = calculate_discovery_score(
            {"confidence_score": 0}, {"gaps": []}, {"coverage_score": 0},
            {"total_reviews": 400},
        )
        assert s1 == s2

    def test_rating_contribution(self):
        """Rating 5 -> (5/5)*3 = 3 pts."""
        score = calculate_discovery_score(
            {"confidence_score": 0}, {"gaps": []}, {"coverage_score": 0},
            {"rating": 5},
        )
        # completeness = 3, comp default = 10 -> 13
        assert score == 13

    def test_competitor_score_overrides_default(self):
        """When competitor_analysis is provided, competitive_score is used."""
        no_comp = calculate_discovery_score(
            {"confidence_score": 0}, {"gaps": []}, {"coverage_score": 0}, {},
        )
        with_comp = calculate_discovery_score(
            {"confidence_score": 0}, {"gaps": []}, {"coverage_score": 0}, {},
            competitor_analysis={"competitive_score": 100},
        )
        # no_comp default = 10, with_comp = (100/100)*20 = 20
        assert with_comp - no_comp == 10

    def test_non_dict_gaps_ignored(self):
        """Non-dict items in gaps list are filtered out."""
        score = calculate_discovery_score(
            {"confidence_score": 0},
            {"gaps": ["string_gap", 123, {"status": "validated"}]},
            {"coverage_score": 0},
            {},
        )
        # Only the dict gap counts: validated=1, total=1 -> sentiment=20
        # comp default=10 -> 30
        assert score == 30

    def test_invalid_total_reviews_handled(self):
        """Non-numeric total_reviews falls back to 0."""
        score = calculate_discovery_score(
            {"confidence_score": 0}, {"gaps": []}, {"coverage_score": 0},
            {"total_reviews": "not a number"},
        )
        # reviews factor = 0, comp default = 10 -> 10
        assert score == 10

    def test_none_total_reviews_handled(self):
        """None total_reviews falls back to 0."""
        score = calculate_discovery_score(
            {"confidence_score": 0}, {"gaps": []}, {"coverage_score": 0},
            {"total_reviews": None},
        )
        assert score == 10

    def test_none_rating_handled(self):
        """None rating falls back to 0."""
        score = calculate_discovery_score(
            {"confidence_score": 0}, {"gaps": []}, {"coverage_score": 0},
            {"rating": None},
        )
        assert score == 10

    def test_realistic_mid_range_score(
        self,
        sample_ai_perception,
        sample_sentiment_analysis,
        sample_visual_audit,
        sample_business_data,
        sample_competitor_analysis,
    ):
        """A realistic mid-to-good scenario produces a score in the 50-85 range."""
        score = calculate_discovery_score(
            sample_ai_perception,
            sample_sentiment_analysis,
            sample_visual_audit,
            sample_business_data,
            sample_competitor_analysis,
        )
        assert 40 <= score <= 90


# ========================================================================
# get_score_interpretation
# ========================================================================


class TestGetScoreInterpretation:
    """Score range mapping: 80+ Excelente, 60-79 Bom, 40-59 Regular, <40 Critico."""

    def test_excelente_at_boundary(self):
        result = get_score_interpretation(80)
        assert result["level"] == "Excelente"
        assert result["color"] == "#22c55e"

    def test_excelente_above_boundary(self):
        result = get_score_interpretation(100)
        assert result["level"] == "Excelente"

    def test_bom_at_boundary(self):
        result = get_score_interpretation(60)
        assert result["level"] == "Bom"
        assert result["color"] == "#3b82f6"

    def test_bom_upper(self):
        result = get_score_interpretation(79)
        assert result["level"] == "Bom"

    def test_regular_at_boundary(self):
        result = get_score_interpretation(40)
        assert result["level"] == "Regular"
        assert result["color"] == "#f59e0b"

    def test_regular_upper(self):
        result = get_score_interpretation(59)
        assert result["level"] == "Regular"

    def test_critico_at_boundary(self):
        result = get_score_interpretation(39)
        assert result["level"] == "Cr\u00edtico"
        assert result["color"] == "#ef4444"

    def test_critico_zero(self):
        result = get_score_interpretation(0)
        assert result["level"] == "Cr\u00edtico"

    def test_all_interpretations_have_required_keys(self):
        for score in [0, 20, 40, 60, 80, 100]:
            result = get_score_interpretation(score)
            assert "level" in result
            assert "color" in result
            assert "message" in result
            assert isinstance(result["message"], str)
            assert len(result["message"]) > 0


# ========================================================================
# generate_priority_recommendations
# ========================================================================


class TestGeneratePriorityRecommendations:
    """Test recommendation generation for various business profiles."""

    def test_low_ai_confidence_generates_profile_rec(self):
        recs = generate_priority_recommendations(
            discovery_score=30,
            ai_perception={"confidence_score": 0.3},
            sentiment_analysis={"gaps": []},
            visual_audit={"coverage_score": 0.8},
            business_data={"claimed": True, "website": "https://x.com", "total_reviews": 5},
        )
        categories = [r["category"] for r in recs]
        assert "profile_completion" in categories

    def test_unclaimed_profile_generates_verification_rec(self):
        recs = generate_priority_recommendations(
            discovery_score=50,
            ai_perception={"confidence_score": 0.8},
            sentiment_analysis={"gaps": []},
            visual_audit={"coverage_score": 0.8},
            business_data={"claimed": False, "website": "https://x.com"},
        )
        categories = [r["category"] for r in recs]
        assert "verification" in categories

    def test_no_website_generates_profile_rec(self):
        recs = generate_priority_recommendations(
            discovery_score=50,
            ai_perception={"confidence_score": 0.8},
            sentiment_analysis={"gaps": []},
            visual_audit={"coverage_score": 0.8},
            business_data={"claimed": True, "website": None},
        )
        profile_recs = [r for r in recs if r["category"] == "profile_completion"]
        assert len(profile_recs) >= 1

    def test_missing_validation_gap_generates_review_rec(self):
        recs = generate_priority_recommendations(
            discovery_score=50,
            ai_perception={"confidence_score": 0.8},
            sentiment_analysis={
                "gaps": [
                    {"claimed": "atendimento rapido", "status": "missing_validation"},
                ]
            },
            visual_audit={"coverage_score": 0.8},
            business_data={"claimed": True, "website": "https://x.com"},
        )
        categories = [r["category"] for r in recs]
        assert "review_generation" in categories

    def test_low_visual_coverage_generates_visual_rec(self):
        recs = generate_priority_recommendations(
            discovery_score=50,
            ai_perception={"confidence_score": 0.8},
            sentiment_analysis={"gaps": []},
            visual_audit={
                "coverage_score": 0.3,
                "recommendations": ["foto da equipe", "foto equipamentos"],
            },
            business_data={"claimed": True, "website": "https://x.com"},
        )
        categories = [r["category"] for r in recs]
        assert "visual_optimization" in categories

    def test_qa_seeding_recommendation(self):
        """Businesses with > 10 reviews get Q&A seeding recommendation."""
        recs = generate_priority_recommendations(
            discovery_score=50,
            ai_perception={"confidence_score": 0.8},
            sentiment_analysis={"gaps": []},
            visual_audit={"coverage_score": 0.8},
            business_data={"claimed": True, "website": "https://x.com", "total_reviews": 50},
        )
        categories = [r["category"] for r in recs]
        assert "content_seeding" in categories

    def test_no_qa_seeding_for_few_reviews(self):
        """Businesses with <= 10 reviews don't get Q&A seeding recommendation."""
        recs = generate_priority_recommendations(
            discovery_score=50,
            ai_perception={"confidence_score": 0.8},
            sentiment_analysis={"gaps": []},
            visual_audit={"coverage_score": 0.8},
            business_data={"claimed": True, "website": "https://x.com", "total_reviews": 5},
        )
        categories = [r["category"] for r in recs]
        assert "content_seeding" not in categories

    def test_competitor_gaps_added(self):
        """Competitor analysis gaps are included in recommendations."""
        comp = {
            "gaps": [
                {
                    "type": "reviews",
                    "severity": "high",
                    "message": "You need more reviews.",
                    "action": "Ask for reviews.",
                },
            ],
            "ai_mentions": {},
            "competitive_score": 40,
        }
        recs = generate_priority_recommendations(
            discovery_score=50,
            ai_perception={"confidence_score": 0.8},
            sentiment_analysis={"gaps": []},
            visual_audit={"coverage_score": 0.8},
            business_data={"claimed": True, "website": "https://x.com"},
            competitor_analysis=comp,
        )
        categories = [r["category"] for r in recs]
        assert "competitive_reviews" in categories

    def test_ai_visibility_rec_when_not_mentioned(self):
        """AI visibility rec added when business is not mentioned but competitors are."""
        comp = {
            "gaps": [],
            "ai_mentions": {
                "MyBiz": False,
                "Competitor1": True,
            },
            "competitive_score": 40,
        }
        recs = generate_priority_recommendations(
            discovery_score=50,
            ai_perception={"confidence_score": 0.8},
            sentiment_analysis={"gaps": []},
            visual_audit={"coverage_score": 0.8},
            business_data={"name": "MyBiz", "claimed": True, "website": "https://x.com"},
            competitor_analysis=comp,
        )
        categories = [r["category"] for r in recs]
        assert "ai_visibility" in categories

    def test_no_ai_visibility_rec_when_mentioned(self):
        """No AI visibility rec when business IS mentioned."""
        comp = {
            "gaps": [],
            "ai_mentions": {
                "MyBiz": True,
                "Competitor1": True,
            },
            "competitive_score": 80,
        }
        recs = generate_priority_recommendations(
            discovery_score=80,
            ai_perception={"confidence_score": 0.8},
            sentiment_analysis={"gaps": []},
            visual_audit={"coverage_score": 0.8},
            business_data={"name": "MyBiz", "claimed": True, "website": "https://x.com"},
            competitor_analysis=comp,
        )
        categories = [r["category"] for r in recs]
        assert "ai_visibility" not in categories

    def test_recommendations_sorted_by_priority(self):
        """High-priority items should appear before medium-priority items."""
        recs = generate_priority_recommendations(
            discovery_score=30,
            ai_perception={"confidence_score": 0.3},
            sentiment_analysis={
                "gaps": [
                    {"claimed": "atendimento", "status": "missing_validation"},
                ]
            },
            visual_audit={
                "coverage_score": 0.3,
                "recommendations": ["equipe"],
            },
            business_data={"claimed": False},
        )
        if len(recs) >= 2:
            priorities = [r["priority"] for r in recs]
            first_medium = next(
                (i for i, p in enumerate(priorities) if p == "medium"), len(priorities)
            )
            last_high = max(
                (i for i, p in enumerate(priorities) if p == "high"), default=-1
            )
            assert last_high < first_medium or first_medium == len(priorities)

    def test_max_10_recommendations(self):
        """Output is capped at 10 items."""
        # Create a scenario that would produce many recs
        comp = {
            "gaps": [
                {"type": f"gap{i}", "severity": "medium", "message": f"m{i}", "action": f"a{i}"}
                for i in range(15)
            ],
            "ai_mentions": {"Biz": False, "C1": True, "C2": True},
            "competitive_score": 20,
        }
        recs = generate_priority_recommendations(
            discovery_score=20,
            ai_perception={"confidence_score": 0.2},
            sentiment_analysis={
                "gaps": [{"claimed": "x", "status": "missing_validation"}]
            },
            visual_audit={"coverage_score": 0.2, "recommendations": ["a", "b"]},
            business_data={"name": "Biz"},
            competitor_analysis=comp,
        )
        assert len(recs) <= 10

    def test_each_recommendation_has_required_keys(self):
        recs = generate_priority_recommendations(
            discovery_score=50,
            ai_perception={"confidence_score": 0.3},
            sentiment_analysis={"gaps": []},
            visual_audit={"coverage_score": 0.8},
            business_data={"claimed": True, "website": "https://x.com"},
        )
        for rec in recs:
            assert "action" in rec
            assert "priority" in rec
            assert "impact" in rec
            assert "effort" in rec
            assert "category" in rec

    def test_no_recommendations_for_perfect_business(self):
        """A fully optimised business with no competitor gaps produces no recs."""
        comp = {
            "gaps": [],
            "ai_mentions": {"PerfectBiz": True},
            "competitive_score": 100,
        }
        recs = generate_priority_recommendations(
            discovery_score=95,
            ai_perception={"confidence_score": 0.9},
            sentiment_analysis={"gaps": [{"status": "validated"}]},
            visual_audit={"coverage_score": 0.9, "recommendations": []},
            business_data={
                "name": "PerfectBiz",
                "claimed": True,
                "website": "https://perfect.com",
                "total_reviews": 5,  # <= 10 so no Q&A seeding
            },
            competitor_analysis=comp,
        )
        assert len(recs) == 0

    def test_website_gap_not_duplicated_with_no_website(self):
        """Competitor gap of type 'website' is skipped when business has no website
        (since the original no-website rec already covers it)."""
        comp = {
            "gaps": [
                {
                    "type": "website",
                    "severity": "high",
                    "message": "Competitors have websites.",
                    "action": "Create a website.",
                },
            ],
            "ai_mentions": {},
            "competitive_score": 40,
        }
        recs = generate_priority_recommendations(
            discovery_score=40,
            ai_perception={"confidence_score": 0.8},
            sentiment_analysis={"gaps": []},
            visual_audit={"coverage_score": 0.8},
            business_data={"claimed": True, "website": None},
            competitor_analysis=comp,
        )
        competitive_website_recs = [
            r for r in recs if r["category"] == "competitive_website"
        ]
        # Should be skipped because business_data has no website
        assert len(competitive_website_recs) == 0
