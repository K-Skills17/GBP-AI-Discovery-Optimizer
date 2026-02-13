-- Migration v2 → v3: WhatsApp required, UTM tracking, schema fixes
-- Run this in your Supabase SQL Editor to add missing columns

-- =============================================
-- BUSINESSES: add photos_count and google_maps_url
-- =============================================
ALTER TABLE public.businesses ADD COLUMN IF NOT EXISTS photos_count INTEGER DEFAULT 0;
ALTER TABLE public.businesses ADD COLUMN IF NOT EXISTS google_maps_url TEXT;

-- =============================================
-- AUDITS: add UTM tracking + WhatsApp error column
-- =============================================
ALTER TABLE public.audits ADD COLUMN IF NOT EXISTS utm_source TEXT;
ALTER TABLE public.audits ADD COLUMN IF NOT EXISTS utm_medium TEXT;
ALTER TABLE public.audits ADD COLUMN IF NOT EXISTS utm_campaign TEXT;
ALTER TABLE public.audits ADD COLUMN IF NOT EXISTS utm_content TEXT;
ALTER TABLE public.audits ADD COLUMN IF NOT EXISTS whatsapp_error TEXT;

-- =============================================
-- COMPETITORS: add total_reviews and google_maps_url
-- =============================================
ALTER TABLE public.competitors ADD COLUMN IF NOT EXISTS total_reviews INTEGER DEFAULT 0;
ALTER TABLE public.competitors ADD COLUMN IF NOT EXISTS google_maps_url TEXT;

-- =============================================
-- WHATSAPP MESSAGES: add retry_count
-- =============================================
ALTER TABLE public.whatsapp_messages ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0;

-- =============================================
-- INDEXES for UTM tracking
-- =============================================
CREATE INDEX IF NOT EXISTS idx_audits_utm_source ON public.audits(utm_source);
CREATE INDEX IF NOT EXISTS idx_audits_utm_campaign ON public.audits(utm_campaign);

-- =============================================
-- Update the recent_audits view
-- =============================================
CREATE OR REPLACE VIEW public.recent_audits AS
SELECT
    a.id,
    a.status,
    a.discovery_score,
    a.competitive_score,
    a.whatsapp_number,
    a.whatsapp_sent,
    a.utm_source,
    a.utm_campaign,
    a.created_at,
    a.processing_time_seconds,
    b.name as business_name,
    b.city,
    b.category,
    b.rating
FROM public.audits a
JOIN public.businesses b ON a.business_id = b.id
ORDER BY a.created_at DESC;

-- =============================================
-- Verify columns exist
-- =============================================
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'audits'
  AND column_name IN ('utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'whatsapp_error')
ORDER BY column_name;
