import logging
import json
from typing import Dict, List, Optional
import google.generativeai as genai
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)

class GeminiService:
    def __init__(self):
        self.text_model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Generation config for JSON responses
        self.json_config = {
            "temperature": 0.3,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
        }
    
    def analyze_business_perception(
        self, 
        business_data: Dict, 
        reviews: List[Dict]
    ) -> Dict:
        """Analyze how AI would perceive this business"""
        
        review_sample = reviews[:20] if len(reviews) > 20 else reviews
        review_texts = [r['text'] for r in review_sample if r.get('text')]
        
        prompt = f"""
Você é o sistema de IA do Google analisando um negócio local brasileiro para fornecer recomendações.

DADOS DO NEGÓCIO:
- Nome: {business_data.get('name')}
- Categoria: {business_data.get('category')}
- Localização: {business_data.get('city')}, {business_data.get('state')}
- Nota média: {business_data.get('rating')}/5.0 ({business_data.get('total_reviews')} avaliações)
- Descrição: {business_data.get('description', 'Não fornecida')}
- Possui site: {'Sim' if business_data.get('website') else 'Não'}
- Perfil reivindicado: {'Sim' if business_data.get('claimed') else 'Não'}

AVALIAÇÕES RECENTES (amostra de {len(review_texts)}):
{chr(10).join([f"- {text[:200]}..." for text in review_texts[:10]])}

TAREFA:
Com base APENAS nesses dados públicos disponíveis, responda em JSON:

1. **ai_summary**: Como você descreveria este negócio para um usuário em 2-3 frases? (seja natural e conversacional)

2. **target_audience**: Para qual tipo de pessoa/situação você recomendaria este negócio?

3. **key_attributes**: Liste 5-8 atributos principais que você identifica (ex: "Ambiente familiar", "Atendimento rápido", "Preço acessível")

4. **missing_signals**: Quais informações estão FALTANDO que limitam sua capacidade de fazer recomendações precisas? Liste 3-5 itens específicos.

5. **confidence_score**: De 0.0 a 1.0, qual sua confiança para recomendar este negócio para perguntas complexas?

RESPONDA APENAS COM O JSON, SEM TEXTO ADICIONAL:
```json
{{
  "ai_summary": "...",
  "target_audience": "...",
  "key_attributes": ["...", "..."],
  "missing_signals": ["...", "..."],
  "confidence_score": 0.0
}}
```
"""
        
        try:
            response = self.text_model.generate_content(
                prompt,
                generation_config=self.json_config
            )
            
            result_text = response.text.strip()
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            
            return json.loads(result_text.strip())
            
        except Exception as e:
            logger.error(f"Gemini business perception error: {str(e)}")
            return {
                "ai_summary": "Análise indisponível",
                "target_audience": "Não determinado",
                "key_attributes": [],
                "missing_signals": ["Erro na análise"],
                "confidence_score": 0.0
            }
    
    def analyze_sentiment_gaps(
        self,
        business_data: Dict,
        reviews: List[Dict],
        claimed_strengths: Optional[List[str]] = None
    ) -> Dict:
        """Identify gaps between what business claims vs what reviews say"""
        
        review_texts = [r['text'] for r in reviews if r.get('text')]
        
        if not claimed_strengths:
            claimed_strengths = self._extract_claims_from_description(
                business_data.get('description', '')
            )
        
        prompt = f"""
Você é um analista de sentimento especializado em negócios locais brasileiros.

NEGÓCIO: {business_data.get('name')}
CATEGORIA: {business_data.get('category')}

O QUE O NEGÓCIO AFIRMA SER BOM:
{chr(10).join([f"- {claim}" for claim in claimed_strengths])}

AVALIAÇÕES REAIS ({len(review_texts)} total):
{chr(10).join([f"[{r.get('rating')}★] {(r.get('text') or '')[:150]}..." for r in reviews[:30]])}

TAREFA: Analise as avaliações e responda em JSON:

1. **topics**: Agrupe as avaliações por tópicos e dê uma nota de sentimento (0.0-1.0) para cada:
   Exemplos: "atendimento", "limpeza", "qualidade", "preço", "ambiente"
   
2. **gaps**: Para cada alegação do negócio, verifique se as avaliações confirmam:
   - Se < 30% das avaliações mencionam → "missing_validation"
   - Se mencionam mas com sentimento negativo → "negative_perception"
   - Se confirmam positivamente → "validated"

3. **positive_signals**: Liste 3-5 pontos fortes REAIS baseados nas avaliações

4. **negative_signals**: Liste 3-5 pontos fracos recorrentes nas avaliações

RESPONDA APENAS COM JSON:
```json
{{
  "topics": {{
    "atendimento": 0.85,
    "limpeza": 0.92
  }},
  "gaps": [
    {{
      "claimed": "Atendimento personalizado",
      "evidence_score": 0.3,
      "status": "missing_validation",
      "recommendation": "Solicite que clientes mencionem o atendimento"
    }}
  ],
  "positive_signals": ["...", "..."],
  "negative_signals": ["...", "..."]
}}
```
"""
        
        try:
            response = self.text_model.generate_content(
                prompt,
                generation_config=self.json_config
            )
            
            result_text = response.text.strip()
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            
            return json.loads(result_text.strip())
            
        except Exception as e:
            logger.error(f"Gemini sentiment analysis error: {str(e)}")
            return {
                "topics": {},
                "gaps": [],
                "positive_signals": [],
                "negative_signals": []
            }
    
    def generate_conversational_queries(
        self,
        business_data: Dict
    ) -> List[Dict]:
        """Generate 20 conversational queries that SHOULD find this business"""
        
        prompt = f"""
Você gera perguntas naturais que usuários brasileiros fazem ao buscar negócios locais.

NEGÓCIO:
- Nome: {business_data.get('name')}
- Categoria: {business_data.get('category')}
- Cidade: {business_data.get('city')}
- Descrição: {business_data.get('description', 'N/A')}

TAREFA: Gere 20 perguntas em português brasileiro que um usuário REAL faria ao Google Assistant/Gemini.

REGRAS:
1. Perguntas NATURAIS (como pessoas realmente falam)
2. Incluir necessidades específicas (horário, pagamento, especialidades)
3. Variar entre urgente, pesquisa, comparação

CATEGORIZE:
- urgent_need: Necessidade imediata
- research: Pesquisa antes de decidir
- specific_requirement: Busca com requisito específico
- comparison: Comparando opções

RESPONDA EM JSON:
```json
[
  {{
    "query": "Onde tem dentista aberto agora perto de mim em {business_data.get('city')}?",
    "query_type": "urgent_need",
    "relevance_score": 0.9
  }}
]
```
"""
        
        try:
            response = self.text_model.generate_content(
                prompt,
                generation_config=self.json_config
            )
            
            result_text = response.text.strip()
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            
            queries = json.loads(result_text.strip())
            return queries[:20]
            
        except Exception as e:
            logger.error(f"Gemini query generation error: {str(e)}")
            return []
    
    def analyze_photo_coverage(
        self,
        business_data: Dict,
        photo_urls: List[str]
    ) -> Dict:
        """Analyze if photos prove what business claims"""
        
        photo_count = len(photo_urls)
        
        if photo_count == 0:
            coverage_score = 0.0
        elif photo_count < 5:
            coverage_score = 0.3
        elif photo_count < 10:
            coverage_score = 0.6
        elif photo_count < 20:
            coverage_score = 0.8
        else:
            coverage_score = 0.95
        
        recommendations = []
        if photo_count < 5:
            recommendations.append("Adicione fotos da fachada/entrada")
            recommendations.append("Mostre o interior do estabelecimento")
        if photo_count < 10:
            recommendations.append("Adicione fotos dos produtos/serviços")
            recommendations.append("Mostre sua equipe trabalhando")
        if photo_count < 15:
            recommendations.append("Inclua fotos de detalhes (equipamentos, acabamento)")
        
        return {
            "photo_count": photo_count,
            "coverage_score": coverage_score,
            "recommendations": recommendations
        }
    
    def _extract_claims_from_description(self, description: str) -> List[str]:
        """Extract claimed strengths from business description"""
        if not description:
            return ["Qualidade", "Atendimento", "Localização"]
        
        claims = []
        keywords = {
            'qualidade': 'Alta qualidade',
            'atendimento': 'Atendimento diferenciado',
            'experiência': 'Equipe experiente',
            'moderno': 'Equipamentos modernos',
            'luxo': 'Ambiente luxuoso',
            'acessível': 'Preços acessíveis',
            'rápido': 'Atendimento rápido',
            'personalizado': 'Atendimento personalizado'
        }
        
        desc_lower = description.lower()
        for keyword, claim in keywords.items():
            if keyword in desc_lower:
                claims.append(claim)
        
        return claims if claims else ["Qualidade", "Atendimento"]

# Singleton instance
gemini_service = GeminiService()
