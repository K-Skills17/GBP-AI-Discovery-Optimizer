"""Competitive analysis service — orchestrates Places + Gemini for competitor diagnostics."""

import logging
from typing import Dict, List, Optional

from app.services.places_service import places_service
from app.services.gemini_service import gemini_service

logger = logging.getLogger(__name__)


class CompetitorService:
    """Builds a competitive diagnostic report for a business vs. its local rivals."""

    async def run_competitive_analysis(
        self,
        business: Dict,
        competitors: List[Dict],
    ) -> Dict:
        """Full competitive analysis pipeline.

        Returns:
            {
                "competitors": [ {...}, ... ],
                "comparison_matrix": { ... },
                "gaps": [ ... ],
                "ai_mentions": { ... },
                "competitive_score": float,  # 0-100
            }
        """
        if not competitors:
            return self._empty_result()

        # 1. Build comparison matrix (hard data from Places)
        matrix = self._build_comparison_matrix(business, competitors)

        # 2. Check AI mentions via Gemini
        ai_mentions = await self._check_ai_mentions(business, competitors)

        # 3. Identify specific gaps
        gaps = self._identify_gaps(business, competitors, ai_mentions)

        # 4. Calculate competitive score
        competitive_score = self._calculate_competitive_score(
            business, competitors, ai_mentions
        )

        # 5. Rank competitors
        ranked = sorted(
            competitors,
            key=lambda c: (c.get("rating", 0) or 0) * (c.get("total_reviews", 0) or 0),
            reverse=True,
        )[:3]

        return {
            "competitors": [
                {
                    "rank": i + 1,
                    "name": c.get("name"),
                    "place_id": c.get("place_id"),
                    "address": c.get("address"),
                    "rating": c.get("rating"),
                    "total_reviews": c.get("total_reviews", 0),
                    "photos_count": c.get("photos_count", 0),
                    "category": c.get("category"),
                    "website": c.get("website"),
                    "google_maps_url": c.get("google_maps_url"),
                    "ai_mentioned": ai_mentions.get(c.get("name", ""), False),
                }
                for i, c in enumerate(ranked)
            ],
            "comparison_matrix": matrix,
            "gaps": gaps,
            "ai_mentions": ai_mentions,
            "competitive_score": competitive_score,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_comparison_matrix(
        self, business: Dict, competitors: List[Dict]
    ) -> Dict:
        """Side-by-side hard metrics."""
        comp_ratings = [c.get("rating") or 0 for c in competitors]
        comp_reviews = [c.get("total_reviews") or 0 for c in competitors]
        comp_photos = [c.get("photos_count") or 0 for c in competitors]

        avg_rating = sum(comp_ratings) / len(comp_ratings) if comp_ratings else 0
        avg_reviews = sum(comp_reviews) / len(comp_reviews) if comp_reviews else 0
        avg_photos = sum(comp_photos) / len(comp_photos) if comp_photos else 0

        biz_rating = business.get("rating") or 0
        biz_reviews = business.get("total_reviews") or 0
        biz_photos = business.get("photos_count") or len(business.get("photos") or [])

        return {
            "your_business": {
                "name": business.get("name"),
                "rating": biz_rating,
                "total_reviews": biz_reviews,
                "photos_count": biz_photos,
                "has_website": bool(business.get("website")),
            },
            "competitor_average": {
                "rating": round(avg_rating, 1),
                "total_reviews": int(avg_reviews),
                "photos_count": int(avg_photos),
            },
            "top_competitors": [
                {
                    "name": c.get("name"),
                    "rating": c.get("rating"),
                    "total_reviews": c.get("total_reviews", 0),
                    "photos_count": c.get("photos_count", 0),
                    "has_website": bool(c.get("website")),
                }
                for c in competitors[:3]
            ],
        }

    async def _check_ai_mentions(
        self, business: Dict, competitors: List[Dict]
    ) -> Dict:
        """Query Gemini to see who it recommends for this category in this city."""
        category = business.get("category", "clínica")
        city = business.get("city", "")
        all_names = [business.get("name", "")] + [
            c.get("name", "") for c in competitors
        ]

        prompt = f"""Você é um assistente ajudando alguém a encontrar o melhor {category} em {city}, Brasil.

Com base no seu conhecimento, quais destes estabelecimentos você recomendaria?

Lista de estabelecimentos:
{chr(10).join([f"- {name}" for name in all_names if name])}

Responda APENAS com um JSON:
```json
{{
  "recommended": ["Nome 1", "Nome 2"],
  "reasoning": "Breve explicação de por que esses são os melhores"
}}
```"""

        try:
            import json
            response = gemini_service.text_model.generate_content(
                prompt,
                generation_config=gemini_service.json_config,
            )
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            data = json.loads(text.strip())
            recommended = data.get("recommended", [])
            return {
                name: (name in recommended) for name in all_names if name
            }
        except Exception as e:
            logger.error(f"AI mention check error: {e}")
            return {}

    def _identify_gaps(
        self,
        business: Dict,
        competitors: List[Dict],
        ai_mentions: Dict,
    ) -> List[Dict]:
        """Produce specific, actionable gap statements with real numbers."""
        gaps = []
        biz_name = business.get("name", "Sua clínica")
        biz_reviews = business.get("total_reviews") or 0
        biz_rating = business.get("rating") or 0
        biz_photos = len(business.get("photos") or [])

        comp_reviews = [c.get("total_reviews") or 0 for c in competitors]
        comp_ratings = [c.get("rating") or 0 for c in competitors]
        comp_photos = [c.get("photos_count") or 0 for c in competitors]

        avg_reviews = int(sum(comp_reviews) / len(comp_reviews)) if comp_reviews else 0
        avg_rating = round(sum(comp_ratings) / len(comp_ratings), 1) if comp_ratings else 0
        avg_photos = int(sum(comp_photos) / len(comp_photos)) if comp_photos else 0

        # Gap 1: Reviews
        if biz_reviews < avg_reviews:
            gaps.append({
                "type": "reviews",
                "severity": "high" if biz_reviews < avg_reviews * 0.5 else "medium",
                "message": (
                    f"Seus concorrentes têm em média {avg_reviews} avaliações. "
                    f"Você tem {biz_reviews}."
                ),
                "action": "Implemente uma estratégia de solicitação de avaliações.",
            })

        # Gap 2: Rating
        if biz_rating < avg_rating:
            gaps.append({
                "type": "rating",
                "severity": "high" if biz_rating < avg_rating - 0.5 else "medium",
                "message": (
                    f"Nota média dos concorrentes: {avg_rating}. "
                    f"Sua nota: {biz_rating}."
                ),
                "action": "Responda avaliações negativas e melhore pontos críticos.",
            })

        # Gap 3: Photos
        if biz_photos < avg_photos:
            gaps.append({
                "type": "photos",
                "severity": "medium",
                "message": (
                    f"Concorrentes têm em média {avg_photos} fotos. "
                    f"Você tem {biz_photos}."
                ),
                "action": "Adicione fotos profissionais do espaço, equipe e serviços.",
            })

        # Gap 4: AI Visibility
        business_mentioned = ai_mentions.get(biz_name, False)
        mentioned_competitors = [
            name for name, mentioned in ai_mentions.items()
            if mentioned and name != biz_name
        ]
        if not business_mentioned and mentioned_competitors:
            gaps.append({
                "type": "ai_visibility",
                "severity": "high",
                "message": (
                    f"O Gemini recomenda {', '.join(mentioned_competitors[:2])} "
                    f"na sua cidade. Sua clínica não é mencionada."
                ),
                "action": "Otimize seu conteúdo online para ser reconhecido pela IA.",
            })

        # Gap 5: Website
        if not business.get("website"):
            competitors_with_site = sum(
                1 for c in competitors if c.get("website")
            )
            if competitors_with_site > 0:
                gaps.append({
                    "type": "website",
                    "severity": "high",
                    "message": (
                        f"{competitors_with_site} de {len(competitors)} concorrentes "
                        f"têm site. Você não tem."
                    ),
                    "action": "Crie um site profissional com informações de serviços.",
                })

        return gaps

    def _calculate_competitive_score(
        self,
        business: Dict,
        competitors: List[Dict],
        ai_mentions: Dict,
    ) -> float:
        """0-100 score for how the business compares to competitors."""
        if not competitors:
            return 50.0

        biz_rating = business.get("rating") or 0
        biz_reviews = business.get("total_reviews") or 0
        biz_photos = len(business.get("photos") or [])

        comp_ratings = [c.get("rating") or 0 for c in competitors]
        comp_reviews = [c.get("total_reviews") or 0 for c in competitors]
        comp_photos = [c.get("photos_count") or 0 for c in competitors]

        max_rating = max(comp_ratings) if comp_ratings else 5.0
        max_reviews = max(comp_reviews) if comp_reviews else 1
        max_photos = max(comp_photos) if comp_photos else 1

        # Rating percentile (0-30)
        rating_score = min(biz_rating / max_rating, 1.0) * 30 if max_rating else 15

        # Review count percentile (0-30)
        review_score = min(biz_reviews / max_reviews, 1.0) * 30 if max_reviews else 0

        # Photo percentile (0-15)
        photo_score = min(biz_photos / max_photos, 1.0) * 15 if max_photos else 0

        # AI mention bonus (0-15)
        biz_name = business.get("name", "")
        ai_score = 15 if ai_mentions.get(biz_name, False) else 0

        # Website bonus (0-10)
        website_score = 10 if business.get("website") else 0

        total = rating_score + review_score + photo_score + ai_score + website_score
        return round(min(max(total, 0), 100), 1)

    def _empty_result(self) -> Dict:
        return {
            "competitors": [],
            "comparison_matrix": {},
            "gaps": [],
            "ai_mentions": {},
            "competitive_score": 50.0,
        }


# Singleton
competitor_service = CompetitorService()
