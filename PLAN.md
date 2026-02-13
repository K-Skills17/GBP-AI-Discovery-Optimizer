# GBP AI Discovery Optimizer — Transformation Plan

## Goal
Transform from a single-business audit tool into a **Competitive Diagnostic Platform** with:
- **Standalone mode**: Full results displayed on-page (no ads needed)
- **Funnel mode**: Results delivered via WhatsApp (for Facebook Ads workflow)
- Google Places API for real data (replaces Outscraper)
- Gemini API as primary AI engine
- Evolution API for WhatsApp delivery
- Micro-engagement progress UI
- Premium serif + gold aesthetic

---

## Phase 1: Backend — New Data Layer (Google Places API)

### 1.1 Create `backend/app/services/places_service.py` (NEW)
Replace Outscraper with Google Places API. This is the critical data foundation.

**Functions:**
- `search_business(name, city)` → Find clinic by name + city using Places Text Search
- `get_business_details(place_id)` → Full business details (rating, reviews, photos, hours, website)
- `get_business_reviews(place_id, max_results=100)` → Fetch reviews
- `find_competitors(place_id, category, lat, lng, radius_km=5, limit=3)` → Nearby Search for top 3 competitors in same category
- `get_competitor_details(place_ids: list)` → Batch fetch competitor details
- `_normalize_place_data(place)` → Convert Places API response to our schema

**API endpoints used:**
- `https://places.googleapis.com/v1/places:searchText` (Text Search)
- `https://places.googleapis.com/v1/places/{place_id}` (Place Details)
- `https://places.googleapis.com/v1/places:searchNearby` (Nearby Search for competitors)

**Key decisions:**
- Use Places API (New) not the legacy API — better data, field masks for cost control
- Use `httpx` for async HTTP calls (already in requirements)
- Field masks to only request what we need (controls billing)

### 1.2 Create `backend/app/services/whatsapp_service.py` (NEW)
Evolution API integration for WhatsApp delivery.

**Functions:**
- `send_diagnostic_report(phone, audit_data)` → Format and send the competitive report
- `format_report_message(audit_data)` → Build WhatsApp-friendly message (3 sections)
- `notify_owner(phone, business_name)` → Notify you that a lead responded
- `_format_phone_br(phone)` → Normalize Brazilian phone numbers

**Evolution API endpoints:**
- `POST /message/sendText/{instance}` — Send text message
- Message format: 3 sections (Competitors, Your Position, Gap Analysis)

### 1.3 Create `backend/app/services/competitor_service.py` (NEW)
Orchestrates the competitive analysis pipeline.

**Functions:**
- `analyze_competitors(business_data, competitor_places, reviews)` → Full competitive analysis
- `build_comparison_matrix(business, competitors)` → Side-by-side metrics
- `identify_gaps(business, competitors)` → Specific actionable gaps
- Uses Gemini API for narrative analysis of competitor strengths

### 1.4 Modify `backend/app/services/audit_service.py`
Update the main orchestrator to use new services.

**Changes:**
- Replace `outscraper_service.search_business()` → `places_service.search_business()`
- Replace `outscraper_service.get_reviews()` → `places_service.get_business_reviews()`
- Replace `openai_service.*` calls → `gemini_service.*` calls (Gemini is already built)
- Add Step: `places_service.find_competitors()` after business lookup
- Add Step: `competitor_service.analyze_competitors()` in processing pipeline
- Add Step: `whatsapp_service.send_diagnostic_report()` at end (if WhatsApp provided)
- Add `whatsapp` field to create_audit flow
- Update `_save_business()` for Places API data format
- Add `_save_competitors()` for competitor data

**New processing pipeline (10 steps):**
1. Search business (Places API)
2. Find top 3 competitors (Places API Nearby Search)
3. Fetch reviews for business (Places API)
4. Fetch competitor details (Places API)
5. AI Perception Analysis (Gemini)
6. Sentiment Gap Analysis (Gemini)
7. Conversational Query Analysis (Gemini) — "best [specialty] in [city]"
8. Competitive Analysis (Gemini + Places data)
9. Calculate Discovery Score (updated weights)
10. Generate recommendations (including competitor insights)
11. Send WhatsApp report (Evolution API, if phone provided)

### 1.5 Modify `backend/app/config.py`
**Add:**
- `GOOGLE_PLACES_API_KEY`
- `GEMINI_API_KEY` (may already exist)
- `EVOLUTION_API_URL`
- `EVOLUTION_API_KEY`
- `EVOLUTION_INSTANCE_NAME`
- `OWNER_WHATSAPP` (your number for notifications)

**Remove:**
- `OUTSCRAPER_API_KEY`

### 1.6 Modify `backend/app/schemas/audit.py`
**Extend `AuditCreateRequest`:**
- Add `whatsapp: Optional[str]` (optional = standalone mode)
- Add `delivery_mode: str = "standalone"` (standalone | whatsapp)

**Extend `AuditResponse`:**
- Add `competitor_analysis: Optional[Dict]`
- Add `whatsapp_sent: Optional[bool]`
- Add `whatsapp_sent_at: Optional[datetime]`

**Add `CompetitorResponse` model:**
- rank, name, place_id, rating, review_count, category, distance, strengths, weaknesses

### 1.7 Modify `backend/app/api/routes/audit.py`
**Add endpoints:**
- `POST /audits/{id}/send-whatsapp` — manually trigger WhatsApp send (for standalone→WhatsApp)
- `GET /audits/{id}/competitors` — get competitor breakdown

**Modify existing:**
- `POST /audits` — accept `whatsapp` and `delivery_mode` fields

### 1.8 Modify `backend/app/utils/scoring.py`
**Update Discovery Score weights:**
- AI Confidence: 25% (was 30%)
- Data Completeness: 20% (was 25%)
- Sentiment Alignment: 20% (was 25%)
- Visual Coverage: 15% (was 20%)
- **Competitive Position: 20% (NEW)** — how you compare to top 3

**Add competitive scoring:**
- Rating vs competitor average
- Review count vs competitor average
- Photo count vs competitor average
- AI mention rate vs competitors

### 1.9 Modify `backend/app/utils/reporting.py`
**Add to reports (PDF + text):**
- Section: "Quem domina sua região" — Top 3 competitors with metrics
- Section: "Onde sua clínica está" — Side-by-side comparison
- Section: "O que separa você do Top 3" — Specific gaps with numbers

### 1.10 Update `backend/requirements.txt`
- Remove: `outscraper==3.0.3`
- Add: `googlemaps==4.10.0` (or use httpx directly for Places API New)
- Ensure: `google-generativeai` is present
- Keep: everything else

### 1.11 Delete `backend/app/services/outscraper_service.py`
No longer needed.

---

## Phase 2: Database Schema Updates

### 2.1 Update `supabase_schema.sql`

**Add `competitors` table:**
```sql
CREATE TABLE public.competitors (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    audit_id UUID REFERENCES public.audits(id) ON DELETE CASCADE,
    rank INTEGER NOT NULL,
    name TEXT NOT NULL,
    place_id TEXT,
    address TEXT,
    city TEXT,
    rating DECIMAL(2,1),
    review_count INTEGER DEFAULT 0,
    category TEXT,
    photos_count INTEGER DEFAULT 0,
    website TEXT,
    distance_meters INTEGER,
    strengths JSONB DEFAULT '[]',
    weaknesses JSONB DEFAULT '[]',
    ai_mentioned BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_competitors_audit_id ON public.competitors(audit_id);
```

**Add `whatsapp_messages` table:**
```sql
CREATE TABLE public.whatsapp_messages (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    audit_id UUID REFERENCES public.audits(id) ON DELETE CASCADE,
    phone_number TEXT NOT NULL,
    message_type TEXT DEFAULT 'diagnostic_report',
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending','sent','delivered','read','failed')),
    evolution_message_id TEXT,
    error_message TEXT,
    sent_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_whatsapp_messages_audit_id ON public.whatsapp_messages(audit_id);
CREATE INDEX idx_whatsapp_messages_status ON public.whatsapp_messages(status);
```

**Modify `audits` table:**
- Add `competitor_analysis JSONB`
- Add `whatsapp_number TEXT`
- Add `delivery_mode TEXT DEFAULT 'standalone'`
- Add `whatsapp_sent BOOLEAN DEFAULT false`
- Add `whatsapp_sent_at TIMESTAMPTZ`
- Add `competitive_score DECIMAL(5,2)`

**Modify `businesses` table:**
- Add `data_source TEXT DEFAULT 'google_places'`
- Rename/ensure `place_id` is Google Places compatible

---

## Phase 3: Frontend — Form + Micro-Engagement UI

### 3.1 Modify `frontend/app/page.tsx` (Landing Page)
**Complete redesign:**
- 3-field form: `Nome da clínica`, `Cidade`, `WhatsApp (opcional)`
- WhatsApp field is optional — if empty, results show on page (standalone)
- If WhatsApp provided, results sent there AND shown on page
- Premium serif + gold aesthetic
- Clean, minimal, high-trust design
- After submit → redirect to micro-engagement page

### 3.2 Create `frontend/app/diagnostico/[auditId]/page.tsx` (NEW — Micro-Engagement + Results)
**This is the core UX page. Two phases:**

**Phase A: Micro-Engagement Sequence (while backend processes)**
Full-page takeover with animated progress steps:
1. "Localizando sua clínica..." (fade in, 1-2s)
2. "Identificando seus principais concorrentes..." (3-4s)
3. "Analisando presença no Google..." (5-6s)
4. "Consultando inteligência artificial..." (8-10s)
5. "Comparando com o Top 3 da sua região..." (5-6s)
6. "Gerando seu relatório personalizado..." (3-4s)

- Each step: subtle checkmark animation when complete
- Progress bar filling across all steps
- Minimum display time: 45-60 seconds (even if backend finishes faster)
- Premium gold accents, serif typography
- Brand logo at top

**Phase B: Results Display (after processing completes)**
Smooth transition from progress → results. Three sections matching the WhatsApp report:

**Section 1: "Quem domina sua região"**
- Top 3 competitors in cards with: name, rating, review count, photos, AI mention status
- Visual ranking (gold/silver/bronze or numbered)

**Section 2: "Onde sua clínica está"**
- Your clinic metrics side-by-side with competitor averages
- Discovery Score with circular gauge
- Color-coded gaps (red = behind, green = ahead)

**Section 3: "O que separa você do Top 3"**
- 3-4 specific, numbered gaps with real data
- e.g., "Seus concorrentes têm em média 120 avaliações. Você tem 23."
- e.g., "O Gemini recomenda [Concorrente A] para implantes na sua cidade."

**CTA Footer:**
- If WhatsApp was provided: "Pronto! Seu diagnóstico foi enviado para o WhatsApp (XX) XXXXX-XXXX"
- Below: "Fique atento ao WhatsApp. Nosso especialista vai te explicar os resultados em seguida."
- If standalone: "Quer saber como fechamos essas lacunas?" + WhatsApp CTA button

### 3.3 Modify `frontend/lib/api-client.ts`
- Update `AuditRequest` interface: add `whatsapp?: string`, `delivery_mode?: string`
- Update `Audit` interface: add competitor_analysis, whatsapp_sent fields
- Add `CompetitorData` interface
- Add `sendWhatsApp(auditId: string)` function

### 3.4 Modify `frontend/app/layout.tsx`
- Import Playfair Display (serif) + Inter (sans-serif) from Google Fonts
- Update metadata for new positioning

### 3.5 Modify `frontend/app/globals.css`
- Update CSS variables for gold palette:
  - Primary: gold (#C5A55A or #D4AF37)
  - Background: warm white (#FAFAF5)
  - Accents: dark charcoal (#1A1A1A), cream (#F5F0E8)
- Add animation keyframes for progress steps

### 3.6 Modify `frontend/tailwind.config.ts`
- Add gold color palette
- Add serif font family
- Add custom animations (fadeInSlide, checkmarkDraw, progressFill, pulseGold)

### 3.7 Install `framer-motion` for smooth animations

### 3.8 Remove/redirect old `resultado/[auditId]` route
Redirect to new `diagnostico/[auditId]` route, or remove entirely.

---

## Phase 4: Integration & Polish

### 4.1 Update `backend/.env.example`
New template with all required keys.

### 4.2 Update `docker-compose.yml`
Keep for local dev, update env vars.

### 4.3 Update `frontend/.env.local.example`
Add any new public env vars.

### 4.4 Update `supabase_schema.sql`
Apply all schema changes from Phase 2.

---

## Implementation Order

| Step | What | Files | Priority |
|------|------|-------|----------|
| 1 | Google Places service | `places_service.py` (new) | CRITICAL |
| 2 | Config updates | `config.py`, `.env.example` | CRITICAL |
| 3 | Schema updates | `supabase_schema.sql`, `schemas/audit.py` | CRITICAL |
| 4 | Competitor service | `competitor_service.py` (new) | HIGH |
| 5 | WhatsApp service | `whatsapp_service.py` (new) | HIGH |
| 6 | Audit service rewrite | `audit_service.py` | HIGH |
| 7 | Scoring updates | `scoring.py` | MEDIUM |
| 8 | Route updates | `audit.py` routes | MEDIUM |
| 9 | Reporting updates | `reporting.py` | MEDIUM |
| 10 | Frontend form + aesthetic | `page.tsx`, `globals.css`, `layout.tsx`, `tailwind.config.ts` | HIGH |
| 11 | Micro-engagement page | `diagnostico/[auditId]/page.tsx` (new) | HIGH |
| 12 | API client updates | `api-client.ts` | MEDIUM |
| 13 | Delete Outscraper | `outscraper_service.py` | LOW |
| 14 | Requirements update | `requirements.txt` | LOW |
| 15 | Cleanup & docs | README, env examples | LOW |

---

## Key Architecture Decisions

1. **WhatsApp is optional** — standalone mode works without it, making the tool useful outside ad funnels
2. **Gemini is primary AI** — already built as service, has direct access to Google's knowledge graph
3. **Places API (New)** — not legacy, uses field masks for cost optimization
4. **Minimum 45s UI delay** — micro-engagement runs on timer, not just backend status
5. **Backend processes everything** — frontend only displays results, no API keys exposed client-side
6. **Celery kept for async** — competitor analysis + Gemini calls can take 30-60s, need background processing
