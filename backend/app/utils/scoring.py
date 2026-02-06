from typing import Dict, List

def calculate_discovery_score(
    ai_perception: Dict,
    sentiment_analysis: Dict,
    visual_audit: Dict,
    business_data: Dict
) -> int:
    """
    Calculate overall AI Discovery Score (0-100)
    
    Components:
    - AI Confidence (30%): How confident AI is about the business
    - Data Completeness (25%): Profile completeness
    - Sentiment Alignment (25%): Reviews match claimed strengths
    - Visual Coverage (20%): Photos prove claims
    """
    
    # 1. AI Confidence Score (0-30 points)
    ai_confidence = ai_perception.get('confidence_score', 0.0)
    ai_score = ai_confidence * 30
    
    # 2. Data Completeness (0-25 points)
    completeness_factors = {
        'description': 5 if business_data.get('description') else 0,
        'website': 3 if business_data.get('website') else 0,
        'phone': 2 if business_data.get('phone') else 0,
        'claimed': 5 if business_data.get('claimed') else 0,
        'reviews': min(business_data.get('total_reviews', 0) / 10, 5),
        'rating': (business_data.get('rating', 0) / 5) * 5
    }
    completeness_score = sum(completeness_factors.values())
    
    # 3. Sentiment Alignment (0-25 points)
    gaps = sentiment_analysis.get('gaps', [])
    validated_count = len([g for g in gaps if g.get('status') == 'validated'])
    total_gaps = len(gaps) if gaps else 1
    sentiment_score = (validated_count / total_gaps) * 25
    
    # 4. Visual Coverage (0-20 points)
    visual_coverage = visual_audit.get('coverage_score', 0.0)
    visual_score = visual_coverage * 20
    
    # Total score
    total = int(ai_score + completeness_score + sentiment_score + visual_score)
    
    return min(max(total, 0), 100)

def get_score_interpretation(score: int) -> Dict:
    """Get human-readable interpretation of the score"""
    
    if score >= 80:
        return {
            "level": "Excelente",
            "color": "#22c55e",
            "message": "Seu negócio está muito bem posicionado para ser descoberto pela IA do Google!",
            "icon": "🎯"
        }
    elif score >= 60:
        return {
            "level": "Bom",
            "color": "#3b82f6",
            "message": "Bom posicionamento, mas há oportunidades de melhoria.",
            "icon": "👍"
        }
    elif score >= 40:
        return {
            "level": "Regular",
            "color": "#f59e0b",
            "message": "A IA tem dificuldade para entender seu negócio. Otimização necessária.",
            "icon": "⚠️"
        }
    else:
        return {
            "level": "Crítico",
            "color": "#ef4444",
            "message": "Seu negócio está praticamente invisível para buscas com IA. Ação urgente necessária!",
            "icon": "🚨"
        }

def generate_priority_recommendations(
    discovery_score: int,
    ai_perception: Dict,
    sentiment_analysis: Dict,
    visual_audit: Dict,
    business_data: Dict
) -> List[Dict]:
    """Generate prioritized action items"""
    
    recommendations = []
    
    # Critical: Low AI confidence
    if ai_perception.get('confidence_score', 0) < 0.5:
        recommendations.append({
            "action": "Complete seu perfil com descrição detalhada e serviços específicos",
            "priority": "high",
            "impact": "+15 pontos",
            "effort": "low",
            "category": "profile_completion"
        })
    
    # Missing claimed profile
    if not business_data.get('claimed'):
        recommendations.append({
            "action": "Reivindique e verifique seu perfil no Google Meu Negócio",
            "priority": "high",
            "impact": "+10 pontos",
            "effort": "low",
            "category": "verification"
        })
    
    # Missing website
    if not business_data.get('website'):
        recommendations.append({
            "action": "Adicione um site ou landing page ao seu perfil",
            "priority": "medium",
            "impact": "+5 pontos",
            "effort": "medium",
            "category": "profile_completion"
        })
    
    # Sentiment gaps
    gaps = sentiment_analysis.get('gaps', [])
    high_priority_gaps = [g for g in gaps if g.get('status') == 'missing_validation']
    if high_priority_gaps:
        gap_example = high_priority_gaps[0]
        recommendations.append({
            "action": f"Solicite avaliações mencionando '{gap_example.get('claimed')}'",
            "priority": "high",
            "impact": "+8 pontos",
            "effort": "low",
            "category": "review_generation",
            "template": f"Adoraríamos saber sua opinião sobre nosso {gap_example.get('claimed').lower()}!"
        })
    
    # Low photo coverage
    if visual_audit.get('coverage_score', 0) < 0.6:
        photo_recs = visual_audit.get('recommendations', [])[:3]
        recommendations.append({
            "action": "Adicione fotos profissionais: " + ", ".join(photo_recs),
            "priority": "medium",
            "impact": "+12 pontos",
            "effort": "medium",
            "category": "visual_optimization"
        })
    
    # Missing Q&A seeding
    if business_data.get('total_reviews', 0) > 10:
        recommendations.append({
            "action": "Publique perguntas e respostas estratégicas no seu perfil",
            "priority": "medium",
            "impact": "+7 pontos",
            "effort": "low",
            "category": "content_seeding",
            "detail": "Exemplo: 'Vocês atendem emergências?' - 'Sim, atendemos de segunda a sábado até 20h'"
        })
    
    # Sort by priority and impact
    priority_order = {"high": 0, "medium": 1, "low": 2}
    recommendations.sort(
        key=lambda x: (priority_order[x['priority']], -int(x['impact'].replace('+', '').replace(' pontos', '')))
    )
    
    return recommendations[:8]
