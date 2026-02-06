# GBP AI Discovery Optimizer

Uma ferramenta SaaS para o mercado brasileiro que audita como a IA do Google percebe negócios locais através de seus perfis no Google Meu Negócio.

## 🎯 Funcionalidades

- **Auditoria AI Gratuita**: Análise de como o Gemini percebe o negócio
- **Discovery Score**: Métrica proprietária de visibilidade AI (0-100)
- **Análise de Sentimento**: Gap entre o que o negócio afirma vs. o que reviews dizem
- **Queries Conversacionais**: 20 perguntas que deveriam encontrar o negócio
- **Auditoria Visual**: Cobertura de fotos e provas visuais
- **Recomendações Priorizadas**: Ações específicas para melhorar o score

## 🏗️ Arquitetura

### Backend (Python/FastAPI)
- **Framework**: FastAPI + Uvicorn
- **Database**: Supabase (PostgreSQL)
- **Queue**: Celery + Redis
- **AI**: Google Gemini 1.5 Flash
- **Scraping**: Outscraper API

### Frontend (Next.js)
- **Framework**: Next.js 14 (App Router)
- **Styling**: Tailwind CSS
- **Language**: TypeScript
- **UI**: Custom components (inspired by Stripe/Linear)

## 📋 Pré-requisitos

- Python 3.11+
- Node.js 18+
- Redis
- Conta Supabase
- API Keys:
  - Google Gemini API
  - Outscraper API

## 🚀 Setup Rápido

### 1. Configurar Supabase

1. Crie uma conta em [supabase.com](https://supabase.com)
2. Crie um novo projeto
3. No SQL Editor, execute o schema:

```sql
-- Copie e cole o conteúdo do schema SQL fornecido anteriormente
```

4. Anote as credenciais:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_KEY`

### 2. Obter API Keys

**Google Gemini:**
1. Acesse [aistudio.google.com](https://aistudio.google.com)
2. Crie uma API key
3. Anote a `GEMINI_API_KEY`

**Outscraper:**
1. Crie conta em [outscraper.com](https://outscraper.com)
2. Adquira créditos (plano básico funciona)
3. Anote a `OUTSCRAPER_API_KEY`

### 3. Backend Setup

```bash
cd backend

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais

# Testar a API
uvicorn app.main:app --reload
```

A API estará em: `http://localhost:8000`
Docs: `http://localhost:8000/api/v1/docs`

### 4. Frontend Setup

```bash
cd frontend

# Instalar dependências
npm install

# Configurar variáveis de ambiente
cp .env.local.example .env.local
# Edite .env.local com suas credenciais

# Iniciar dev server
npm run dev
```

Frontend estará em: `http://localhost:3000`

### 5. Iniciar Workers (Celery)

Em um terminal separado:

```bash
cd backend
source venv/bin/activate

# Iniciar Redis (se não estiver rodando)
redis-server

# Iniciar Celery worker
celery -A app.tasks.celery_app worker --loglevel=info

# (Opcional) Iniciar Flower para monitorar tasks
celery -A app.tasks.celery_app flower --port=5555
```

## 🐳 Deploy com Docker

```bash
# Iniciar todos os serviços
docker-compose up -d

# Ver logs
docker-compose logs -f

# Parar serviços
docker-compose down
```

Serviços disponíveis:
- Backend API: `http://localhost:8000`
- Flower (Monitor Celery): `http://localhost:5555`
- Redis: `localhost:6379`

## 📊 Fluxo de Funcionamento

1. **Usuário preenche formulário** (nome do negócio + cidade)
2. **Frontend cria audit request** → Backend API
3. **Backend:**
   - Busca negócio no Outscraper
   - Salva no Supabase
   - Enfileira task Celery
   - Retorna `audit_id` imediatamente
4. **Worker Celery processa:**
   - Busca reviews (até 100)
   - Análise AI (Gemini):
     - Percepção do negócio
     - Gaps de sentimento
     - Queries conversacionais
     - Cobertura visual
   - Calcula Discovery Score
   - Gera recomendações
   - Salva resultados
5. **Frontend faz polling** até status = `completed`
6. **Exibe resultados** com visualizações

## 🔧 Variáveis de Ambiente

### Backend (.env)
```env
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJxxx...
SUPABASE_SERVICE_KEY=eyJxxx...

# Redis
REDIS_URL=redis://localhost:6379/0

# APIs
OUTSCRAPER_API_KEY=xxx
GEMINI_API_KEY=xxx

# Config
MAX_REVIEWS_PER_AUDIT=100
AUDIT_CACHE_HOURS=24
AUDIT_PRICE_CENTS=29700
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJxxx...
```

## 📈 Algoritmo de Scoring

**Discovery Score (0-100 pontos):**

1. **AI Confidence (30%)**: Quão confiante a IA está sobre o negócio
2. **Data Completeness (25%)**: Completude do perfil GBP
3. **Sentiment Alignment (25%)**: Reviews confirmam alegações
4. **Visual Coverage (20%)**: Fotos provam atributos

## 🎨 Customização

### Alterar textos/idioma
- Frontend: `frontend/app/page.tsx` e `frontend/app/resultado/[auditId]/page.tsx`
- Backend prompts: `backend/app/services/gemini_service.py`

### Ajustar scoring
- Algoritmo: `backend/app/utils/scoring.py`
- Weights e thresholds podem ser ajustados

### Modificar recommendations
- Lógica: `backend/app/utils/scoring.py` → `generate_priority_recommendations()`

## 🚨 Troubleshooting

**Erro: Audit status stuck em "processing"**
- Verifique se Celery worker está rodando
- Veja logs: `docker-compose logs celery_worker`
- Verifique Gemini API key e quotas

**Erro: "Negócio não encontrado"**
- Outscraper pode não ter dados do negócio
- Tente variações no nome
- Verifique créditos Outscraper

**Frontend não conecta no backend**
- Verifique `NEXT_PUBLIC_API_URL` no `.env.local`
- Backend deve estar rodando em `http://localhost:8000`
- Check CORS settings em `backend/app/main.py`

## 📝 TODO / Roadmap

- [ ] Autenticação de usuários (Supabase Auth)
- [ ] Painel admin para ver todas audits
- [ ] Geração de PDF report
- [ ] Integração com WhatsApp para notificar quando pronto
- [ ] Sistema de pagamento (Stripe/Hotmart)
- [ ] Cache de audits recentes (< 24h)
- [ ] Rate limiting
- [ ] Testes automatizados

## 🤝 Contribuindo

Este é um projeto privado da LK Digital. Para modificações ou sugestões, contate stephen@lkdigital.com.br

## 📄 Licença

Propriedade da LK Digital - Todos os direitos reservados.

---

**Desenvolvido com ❤️ pela equipe LK Digital**
