"""Shared pytest fixtures for the GBP AI Discovery Optimizer backend test suite.

All fixtures produce deterministic, representative data so that tests exercise
pure business logic without hitting any external service (Google Places,
Gemini, Supabase, Redis, WhatsApp/Evolution API).
"""

import os
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, AsyncMock

# ---------------------------------------------------------------------------
# Environment – ensure Settings can be instantiated without a real .env file
# ---------------------------------------------------------------------------

os.environ.setdefault("SUPABASE_URL", "https://fake.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "fake-anon-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "fake-service-key")
os.environ.setdefault("GOOGLE_PLACES_API_KEY", "fake-places-key")
os.environ.setdefault("GEMINI_API_KEY", "fake-gemini-key")
os.environ.setdefault("OPENAI_API_KEY", "fake-openai-key")
os.environ.setdefault("EVOLUTION_API_KEY", "fake-evolution-key")
os.environ.setdefault("SENTRY_DSN", "")


# ---------------------------------------------------------------------------
# Reusable data factories
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_business_data():
    """A fully-populated business dict as returned by PlacesService._normalize_place."""
    return {
        "place_id": "ChIJabc123",
        "name": "Clinica Sorriso",
        "address": "Rua das Flores, 100, Sao Paulo, SP",
        "city": "Sao Paulo",
        "state": "SP",
        "category": "Dentista",
        "phone": "(11) 99999-0000",
        "website": "https://clinicasorriso.com.br",
        "rating": 4.5,
        "total_reviews": 120,
        "claimed": True,
        "latitude": -23.5505,
        "longitude": -46.6333,
        "description": "Clinica odontologica completa com implantes e ortodontia.",
        "hours": ["Mon: 8am-6pm", "Tue: 8am-6pm"],
        "photos": [
            "places/ChIJabc123/photos/photo1",
            "places/ChIJabc123/photos/photo2",
            "places/ChIJabc123/photos/photo3",
        ],
        "photos_count": 3,
        "google_maps_url": "https://maps.google.com/?cid=123",
        "raw_data": {},
    }


@pytest.fixture
def sample_competitors():
    """A list of competitor dicts (already normalised)."""
    return [
        {
            "place_id": "ChIJcomp1",
            "name": "OdontoTop",
            "address": "Av. Paulista, 200",
            "city": "Sao Paulo",
            "state": "SP",
            "category": "Dentista",
            "phone": "(11) 98888-0001",
            "website": "https://odontotop.com.br",
            "rating": 4.8,
            "total_reviews": 250,
            "claimed": True,
            "latitude": -23.5610,
            "longitude": -46.6550,
            "description": "Referencia em implantes.",
            "hours": None,
            "photos": ["p1", "p2", "p3", "p4", "p5"],
            "photos_count": 5,
            "google_maps_url": "https://maps.google.com/?cid=201",
            "raw_data": {},
        },
        {
            "place_id": "ChIJcomp2",
            "name": "DentalCare",
            "address": "Rua Augusta, 50",
            "city": "Sao Paulo",
            "state": "SP",
            "category": "Dentista",
            "phone": "(11) 97777-0002",
            "website": None,
            "rating": 4.2,
            "total_reviews": 80,
            "claimed": True,
            "latitude": -23.5520,
            "longitude": -46.6400,
            "description": None,
            "hours": None,
            "photos": ["p1"],
            "photos_count": 1,
            "google_maps_url": "https://maps.google.com/?cid=202",
            "raw_data": {},
        },
        {
            "place_id": "ChIJcomp3",
            "name": "SorrirMais",
            "address": "Rua Consolacao, 300",
            "city": "Sao Paulo",
            "state": "SP",
            "category": "Dentista",
            "phone": None,
            "website": "https://sorrirmais.com.br",
            "rating": 4.0,
            "total_reviews": 40,
            "claimed": False,
            "latitude": -23.5530,
            "longitude": -46.6430,
            "description": "Ortodontia e estetica dental.",
            "hours": None,
            "photos": ["p1", "p2"],
            "photos_count": 2,
            "google_maps_url": "https://maps.google.com/?cid=203",
            "raw_data": {},
        },
    ]


@pytest.fixture
def sample_ai_perception():
    """Gemini AI perception analysis result."""
    return {
        "confidence_score": 0.75,
        "summary": "Clinica Sorriso is a well-known dental clinic.",
        "strengths": ["implantes", "localizacao"],
        "weaknesses": ["pouca presenca digital"],
    }


@pytest.fixture
def sample_sentiment_analysis():
    """Gemini sentiment gap analysis result."""
    return {
        "topics": {"atendimento": 0.8, "limpeza": 0.6, "preco": 0.4},
        "gaps": [
            {"claimed": "atendimento rapido", "status": "validated"},
            {"claimed": "preco acessivel", "status": "missing_validation"},
            {"claimed": "tecnologia moderna", "status": "validated"},
        ],
    }


@pytest.fixture
def sample_visual_audit():
    """Gemini visual coverage audit result."""
    return {
        "coverage_score": 0.5,
        "categories_found": ["fachada", "interior"],
        "categories_missing": ["equipe", "servicos"],
        "recommendations": ["foto da equipe", "foto dos equipamentos", "foto da recepcao"],
    }


@pytest.fixture
def sample_competitor_analysis():
    """Complete competitor analysis result dict."""
    return {
        "competitors": [
            {
                "rank": 1,
                "name": "OdontoTop",
                "place_id": "ChIJcomp1",
                "address": "Av. Paulista, 200",
                "rating": 4.8,
                "total_reviews": 250,
                "photos_count": 5,
                "category": "Dentista",
                "website": "https://odontotop.com.br",
                "google_maps_url": "https://maps.google.com/?cid=201",
                "ai_mentioned": True,
            },
        ],
        "comparison_matrix": {},
        "gaps": [
            {
                "type": "reviews",
                "severity": "high",
                "message": "Concorrentes tem mais avaliacoes.",
                "action": "Solicite mais avaliacoes.",
            },
        ],
        "ai_mentions": {
            "Clinica Sorriso": False,
            "OdontoTop": True,
        },
        "competitive_score": 55.0,
    }


@pytest.fixture
def sample_audit_response():
    """A completed audit dict as returned by the audit service / database."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": "audit-uuid-001",
        "business_id": "biz-uuid-001",
        "status": "completed",
        "discovery_score": 72,
        "competitive_score": 55.0,
        "sentiment_score": 0.6,
        "visual_coverage_score": 0.5,
        "ai_summary": {"confidence_score": 0.75},
        "sentiment_analysis": {"topics": {}, "gaps": []},
        "conversational_queries": [],
        "visual_audit": {"coverage_score": 0.5},
        "competitor_analysis": {"competitive_score": 55.0, "competitors": []},
        "recommendations": [],
        "processing_time_seconds": 12,
        "error_message": None,
        "delivery_mode": "standalone",
        "whatsapp_number": None,
        "whatsapp_sent": None,
        "whatsapp_sent_at": None,
        "created_at": now,
        "updated_at": now,
    }


@pytest.fixture
def sample_pending_audit_response():
    """An audit that is still processing."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": "audit-uuid-002",
        "business_id": "biz-uuid-001",
        "status": "processing",
        "discovery_score": None,
        "competitive_score": None,
        "sentiment_score": None,
        "visual_coverage_score": None,
        "ai_summary": None,
        "sentiment_analysis": None,
        "conversational_queries": None,
        "visual_audit": None,
        "competitor_analysis": None,
        "recommendations": None,
        "processing_time_seconds": None,
        "error_message": None,
        "delivery_mode": "standalone",
        "whatsapp_number": None,
        "whatsapp_sent": None,
        "whatsapp_sent_at": None,
        "created_at": now,
        "updated_at": now,
    }


# ---------------------------------------------------------------------------
# Raw Places API response fixtures (for _normalize_place / _normalize_review)
# ---------------------------------------------------------------------------

@pytest.fixture
def raw_places_api_place():
    """Raw JSON as returned by Google Places API (New) Text Search."""
    return {
        "id": "places/ChIJraw123",
        "displayName": {"text": "Clinica Exemplo", "languageCode": "pt-BR"},
        "formattedAddress": "Rua Exemplo, 42, Campinas, SP, Brasil",
        "addressComponents": [
            {
                "longText": "Campinas",
                "shortText": "Campinas",
                "types": ["administrative_area_level_2"],
            },
            {
                "longText": "Sao Paulo",
                "shortText": "SP",
                "types": ["administrative_area_level_1"],
            },
        ],
        "location": {"latitude": -22.9064, "longitude": -47.0616},
        "rating": 4.3,
        "userRatingCount": 95,
        "websiteUri": "https://exemplo.com.br",
        "nationalPhoneNumber": "(19) 3333-4444",
        "primaryType": "dentist",
        "primaryTypeDisplayName": {"text": "Dentista"},
        "businessStatus": "OPERATIONAL",
        "currentOpeningHours": {
            "weekdayDescriptions": [
                "Monday: 8:00 AM - 6:00 PM",
                "Tuesday: 8:00 AM - 6:00 PM",
            ],
        },
        "photos": [
            {"name": "places/ChIJraw123/photos/p1"},
            {"name": "places/ChIJraw123/photos/p2"},
        ],
        "editorialSummary": {"text": "Clinica de referencia em odontologia."},
        "googleMapsUri": "https://maps.google.com/?cid=999",
    }


@pytest.fixture
def raw_places_api_review():
    """Raw JSON of a single review from Places API (New)."""
    return {
        "authorAttribution": {
            "displayName": "Joao Silva",
            "uri": "https://maps.google.com/contrib/12345",
        },
        "rating": 5,
        "text": {"text": "Otimo atendimento, super recomendo!"},
        "publishTime": "2024-06-15T14:30:00Z",
        "flagContentUri": None,
    }
