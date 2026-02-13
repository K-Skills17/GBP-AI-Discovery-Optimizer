"""Discovery Score calculation and recommendation generation.

Updated weights (v2):
  - AI Confidence:      25%
  - Data Completeness:  20%
  - Sentiment Alignment:20%
  - Visual Coverage:    15%
  - Competitive Position:20%  (NEW)
"""

from typing import Dict, List, Optional


def calculate_discovery_score(
    ai_perception: Dict,
    sentiment_analysis: Dict,
    visual_audit: Dict,
    business_data: Dict,
    competitor_analysis: Optional[Dict] = None,
) -> int:
    """Calculate overall AI Discovery Score (0-100)."""

    # 1. AI Confidence Score (0-25 points)
    ai_confidence = ai_perception.get("confidence_score", 0.0)
    ai_score = ai_confidence * 25

    # 2. Data Completeness (0-20 points)
    total_reviews = business_data.get("total_reviews", 0)
    rating = business_data.get("rating", 0)
    try:
        total_reviews = int(total_reviews) if total_reviews is not None else 0
    except (TypeError, ValueError):
        total_reviews = 0
    try:
        rating = float(rating) if rating is not None else 0
    except (TypeError, ValueError):
        rating = 0

    completeness_factors = {
        "description": 4 if business_data.get("description") else 0,
        "website": 3 if business_data.get("website") else 0,
        "phone": 2 if business_data.get("phone") else 0,
        "claimed": 4 if business_data.get("claimed") else 0,
        "reviews": min(total_reviews / 10, 4),
        "rating": (rating / 5) * 3,
    }
    completeness_score = sum(completeness_factors.values())

    # 3. Sentiment Alignment (0-20 points)
    gaps = sentiment_analysis.get("gaps", [])
    gap_dicts = [g for g in gaps if isinstance(g, dict)]
    validated_count = len(
        [g for g in gap_dicts if g.get("status") == "validated"]
    )
    total_gaps = len(gap_dicts) if gap_dicts else 1
    sentiment_score = (validated_count / total_gaps) * 20

    # 4. Visual Coverage (0-15 points)
    visual_coverage = visual_audit.get("coverage_score", 0.0)
    visual_score = visual_coverage * 15

    # 5. Competitive Position (0-20 points)
    comp_score_raw = 10  # default middle ground
    if competitor_analysis:
        comp_score_raw = competitor_analysis.get("competitive_score", 50) / 100 * 20

    # Total
    total = int(ai_score + completeness_score + sentiment_score + visual_score + comp_score_raw)
    return min(max(total, 0), 100)


def get_score_interpretation(score: int) -> Dict:
    """Get human-readable interpretation of the score."""
    if score >= 80:
        return {
            "level": "Excelente",
            "color": "#22c55e",
            "message": "Seu negócio está muito bem posicionado para ser descoberto pela IA do Google!",
        }
    elif score >= 60:
        return {
            "level": "Bom",
            "color": "#3b82f6",
            "message": "Bom posicionamento, mas há oportunidades de melhoria.",
        }
    elif score >= 40:
        return {
            "level": "Regular",
            "color": "#f59e0b",
            "message": "A IA tem dificuldade para entender seu negócio. Otimização necessária.",
        }
    else:
        return {
            "level": "Crítico",
            "color": "#ef4444",
            "message": "Seu negócio está praticamente invisível para buscas com IA. Ação urgente necessária!",
        }


def generate_priority_recommendations(
    discovery_score: int,
    ai_perception: Dict,
    sentiment_analysis: Dict,
    visual_audit: Dict,
    business_data: Dict,
    competitor_analysis: Optional[Dict] = None,
) -> List[Dict]:
    """Generate prioritized action items including competitor-based insights."""

    recommendations: List[Dict] = []

    # ---- Original recommendations ----

    # Low AI confidence
    if ai_perception.get("confidence_score", 0) < 0.5:
        recommendations.append({
            "action": "Complete seu perfil com descrição detalhada e serviços específicos",
            "priority": "high",
            "impact": "+15 pontos",
            "effort": "low",
            "category": "profile_completion",
        })

    # Unclaimed profile
    if not business_data.get("claimed"):
        recommendations.append({
            "action": "Reivindique e verifique seu perfil no Google Meu Negócio",
            "priority": "high",
            "impact": "+10 pontos",
            "effort": "low",
            "category": "verification",
        })

    # No website
    if not business_data.get("website"):
        recommendations.append({
            "action": "Adicione um site ou landing page ao seu perfil",
            "priority": "medium",
            "impact": "+5 pontos",
            "effort": "medium",
            "category": "profile_completion",
        })

    # Sentiment gaps
    gaps = sentiment_analysis.get("gaps", [])
    high_priority_gaps = [
        g for g in gaps if isinstance(g, dict) and g.get("status") == "missing_validation"
    ]
    if high_priority_gaps:
        gap_example = high_priority_gaps[0]
        claimed = gap_example.get("claimed") or "atendimento"
        claimed_str = str(claimed).lower() if claimed else "atendimento"
        recommendations.append({
            "action": f"Solicite avaliações mencionando '{claimed}'",
            "priority": "high",
            "impact": "+8 pontos",
            "effort": "low",
            "category": "review_generation",
            "template": f"Adoraríamos saber sua opinião sobre nosso {claimed_str}!",
        })

    # Low photo coverage
    if visual_audit.get("coverage_score", 0) < 0.6:
        photo_recs = visual_audit.get("recommendations", [])[:3]
        recommendations.append({
            "action": "Adicione fotos profissionais: " + ", ".join(photo_recs),
            "priority": "medium",
            "impact": "+12 pontos",
            "effort": "medium",
            "category": "visual_optimization",
        })

    # Q&A seeding
    if business_data.get("total_reviews", 0) and int(business_data.get("total_reviews", 0)) > 10:
        recommendations.append({
            "action": "Publique perguntas e respostas estratégicas no seu perfil",
            "priority": "medium",
            "impact": "+7 pontos",
            "effort": "low",
            "category": "content_seeding",
            "detail": "Exemplo: 'Vocês atendem emergências?' — 'Sim, atendemos de segunda a sábado até 20h'",
        })

    # ---- Competitor-based recommendations ----
    if competitor_analysis:
        comp_gaps = competitor_analysis.get("gaps", [])
        for gap in comp_gaps:
            if not isinstance(gap, dict):
                continue
            gap_type = gap.get("type", "")
            severity = gap.get("severity", "medium")
            message = gap.get("message", "")
            action = gap.get("action", "")

            # Don't duplicate website rec
            if gap_type == "website" and not business_data.get("website"):
                continue

            impact = "+10 pontos" if severity == "high" else "+5 pontos"
            recommendations.append({
                "action": action or message,
                "priority": "high" if severity == "high" else "medium",
                "impact": impact,
                "effort": "medium",
                "category": f"competitive_{gap_type}",
                "detail": message,
            })

        # AI visibility rec
        ai_mentions = competitor_analysis.get("ai_mentions", {})
        biz_name = business_data.get("name", "")
        if ai_mentions and not ai_mentions.get(biz_name, False):
            mentioned = [
                n for n, m in ai_mentions.items() if m and n != biz_name
            ]
            if mentioned:
                recommendations.append({
                    "action": "Otimize sua presença online para aparecer nas recomendações da IA",
                    "priority": "high",
                    "impact": "+15 pontos",
                    "effort": "high",
                    "category": "ai_visibility",
                    "detail": (
                        f"Concorrentes mencionados pela IA: {', '.join(mentioned[:2])}. "
                        "Melhore conteúdo do site, avaliações e dados estruturados."
                    ),
                })

    # Sort by priority and impact
    priority_order = {"high": 0, "medium": 1, "low": 2}
    recommendations.sort(
        key=lambda x: (
            priority_order.get(x["priority"], 2),
            -int(x["impact"].replace("+", "").replace(" pontos", "")),
        )
    )

    return recommendations[:10]
