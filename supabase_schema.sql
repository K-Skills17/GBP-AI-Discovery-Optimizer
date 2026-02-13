-- GBP AI Discovery Optimizer - Supabase Schema (v2)
-- Execute this in your Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================
-- PROFILES TABLE
-- =============================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    company_name TEXT,
    phone TEXT,
    role TEXT DEFAULT 'client' CHECK (role IN ('client', 'admin')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Users can view own profile' AND tablename = 'profiles') THEN
    CREATE POLICY "Users can view own profile" ON public.profiles FOR SELECT USING (auth.uid() = id);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Users can update own profile' AND tablename = 'profiles') THEN
    CREATE POLICY "Users can update own profile" ON public.profiles FOR UPDATE USING (auth.uid() = id);
  END IF;
END $$;

-- =============================================
-- BUSINESSES TABLE
-- =============================================
CREATE TABLE IF NOT EXISTS public.businesses (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    place_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    address TEXT,
    city TEXT,
    state TEXT DEFAULT 'SP',
    category TEXT,
    phone TEXT,
    website TEXT,
    rating DECIMAL(2,1),
    total_reviews INTEGER DEFAULT 0,
    claimed BOOLEAN DEFAULT false,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    description TEXT,
    hours JSONB,
    photos JSONB,
    questions_and_answers JSONB,
    data_source TEXT DEFAULT 'google_places',
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_businesses_place_id ON public.businesses(place_id);
CREATE INDEX IF NOT EXISTS idx_businesses_city ON public.businesses(city);
CREATE INDEX IF NOT EXISTS idx_businesses_name ON public.businesses(name);

-- =============================================
-- AUDITS TABLE (v2 — with competitor + WhatsApp fields)
-- =============================================
CREATE TABLE IF NOT EXISTS public.audits (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    business_id UUID REFERENCES public.businesses(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,

    -- Status
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),

    -- Delivery
    delivery_mode TEXT DEFAULT 'standalone' CHECK (delivery_mode IN ('standalone', 'whatsapp')),
    whatsapp_number TEXT,
    whatsapp_sent BOOLEAN DEFAULT false,
    whatsapp_sent_at TIMESTAMPTZ,

    -- Scores
    discovery_score INTEGER CHECK (discovery_score >= 0 AND discovery_score <= 100),
    competitive_score DECIMAL(5,2),
    sentiment_score DECIMAL(3,2) CHECK (sentiment_score >= 0 AND sentiment_score <= 1),
    visual_coverage_score DECIMAL(3,2) CHECK (visual_coverage_score >= 0 AND visual_coverage_score <= 1),

    -- AI Analysis Results (stored as JSONB)
    ai_summary JSONB,
    sentiment_analysis JSONB,
    conversational_queries JSONB,
    visual_audit JSONB,
    competitor_analysis JSONB,
    recommendations JSONB,

    -- Report
    pdf_url TEXT,
    report_expires_at TIMESTAMPTZ,

    -- Metadata
    processing_time_seconds INTEGER,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audits_business_id ON public.audits(business_id);
CREATE INDEX IF NOT EXISTS idx_audits_user_id ON public.audits(user_id);
CREATE INDEX IF NOT EXISTS idx_audits_status ON public.audits(status);
CREATE INDEX IF NOT EXISTS idx_audits_created_at ON public.audits(created_at DESC);

ALTER TABLE public.audits ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Users can view own audits' AND tablename = 'audits') THEN
    CREATE POLICY "Users can view own audits" ON public.audits FOR SELECT
      USING (auth.uid() = user_id OR auth.uid() IN (SELECT id FROM public.profiles WHERE role = 'admin'));
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Anyone can create audits' AND tablename = 'audits') THEN
    CREATE POLICY "Anyone can create audits" ON public.audits FOR INSERT WITH CHECK (true);
  END IF;
END $$;

-- =============================================
-- REVIEWS TABLE
-- =============================================
CREATE TABLE IF NOT EXISTS public.reviews (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    business_id UUID REFERENCES public.businesses(id) ON DELETE CASCADE,
    author_name TEXT,
    author_url TEXT,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    text TEXT,
    published_at TIMESTAMPTZ,
    owner_reply TEXT,
    owner_reply_at TIMESTAMPTZ,
    likes INTEGER,
    photos JSONB,
    sentiment_score DECIMAL(3,2),
    extracted_topics JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reviews_business_id ON public.reviews(business_id);
CREATE INDEX IF NOT EXISTS idx_reviews_published_at ON public.reviews(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_reviews_rating ON public.reviews(rating);

-- =============================================
-- COMPETITORS TABLE (NEW in v2)
-- =============================================
CREATE TABLE IF NOT EXISTS public.competitors (
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

CREATE INDEX IF NOT EXISTS idx_competitors_audit_id ON public.competitors(audit_id);

-- =============================================
-- WHATSAPP MESSAGES TABLE (NEW in v2)
-- =============================================
CREATE TABLE IF NOT EXISTS public.whatsapp_messages (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    audit_id UUID REFERENCES public.audits(id) ON DELETE CASCADE,
    phone_number TEXT NOT NULL,
    message_type TEXT DEFAULT 'diagnostic_report',
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'delivered', 'read', 'failed')),
    evolution_message_id TEXT,
    error_message TEXT,
    sent_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_audit_id ON public.whatsapp_messages(audit_id);
CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_status ON public.whatsapp_messages(status);

-- =============================================
-- PAYMENTS TABLE (Future use)
-- =============================================
CREATE TABLE IF NOT EXISTS public.payments (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    audit_id UUID REFERENCES public.audits(id) ON DELETE SET NULL,
    amount_cents INTEGER NOT NULL,
    currency TEXT DEFAULT 'BRL',
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'failed', 'refunded')),
    payment_method TEXT,
    transaction_id TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_payments_user_id ON public.payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON public.payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_created_at ON public.payments(created_at DESC);

-- =============================================
-- TRIGGERS
-- =============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_profiles_updated_at ON public.profiles;
CREATE TRIGGER update_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_businesses_updated_at ON public.businesses;
CREATE TRIGGER update_businesses_updated_at
    BEFORE UPDATE ON public.businesses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_audits_updated_at ON public.audits;
CREATE TRIGGER update_audits_updated_at
    BEFORE UPDATE ON public.audits
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_payments_updated_at ON public.payments;
CREATE TRIGGER update_payments_updated_at
    BEFORE UPDATE ON public.payments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================
-- VIEWS
-- =============================================

CREATE OR REPLACE VIEW public.recent_audits AS
SELECT
    a.id,
    a.status,
    a.discovery_score,
    a.competitive_score,
    a.delivery_mode,
    a.whatsapp_sent,
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
-- MIGRATION: Add v2 columns to existing tables
-- =============================================
ALTER TABLE public.businesses ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE public.businesses ADD COLUMN IF NOT EXISTS hours JSONB;
ALTER TABLE public.businesses ADD COLUMN IF NOT EXISTS photos JSONB;
ALTER TABLE public.businesses ADD COLUMN IF NOT EXISTS questions_and_answers JSONB;
ALTER TABLE public.businesses ADD COLUMN IF NOT EXISTS data_source TEXT DEFAULT 'google_places';
ALTER TABLE public.reviews ADD COLUMN IF NOT EXISTS likes INTEGER;
ALTER TABLE public.reviews ADD COLUMN IF NOT EXISTS photos JSONB;
ALTER TABLE public.audits ADD COLUMN IF NOT EXISTS delivery_mode TEXT DEFAULT 'standalone';
ALTER TABLE public.audits ADD COLUMN IF NOT EXISTS whatsapp_number TEXT;
ALTER TABLE public.audits ADD COLUMN IF NOT EXISTS whatsapp_sent BOOLEAN DEFAULT false;
ALTER TABLE public.audits ADD COLUMN IF NOT EXISTS whatsapp_sent_at TIMESTAMPTZ;
ALTER TABLE public.audits ADD COLUMN IF NOT EXISTS competitive_score DECIMAL(5,2);
ALTER TABLE public.audits ADD COLUMN IF NOT EXISTS competitor_analysis JSONB;

-- =============================================
-- COMPLETED — Verify
-- =============================================
SELECT
    'Profiles' as table_name, COUNT(*) as count FROM public.profiles
UNION ALL SELECT 'Businesses', COUNT(*) FROM public.businesses
UNION ALL SELECT 'Audits', COUNT(*) FROM public.audits
UNION ALL SELECT 'Reviews', COUNT(*) FROM public.reviews
UNION ALL SELECT 'Competitors', COUNT(*) FROM public.competitors
UNION ALL SELECT 'WhatsApp Messages', COUNT(*) FROM public.whatsapp_messages
UNION ALL SELECT 'Payments', COUNT(*) FROM public.payments;
