"""Tests for the FastAPI API routes (app.api.routes.audit + health).

Every test mocks the audit_service singleton so no database, Supabase,
Google Places, or Gemini calls are made.  The FastAPI TestClient sends
real HTTP requests through the middleware stack.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, AsyncMock

from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Build a TestClient with all external dependencies mocked out.
#
# We patch:
#   - app.config.get_settings  (provides env vars)
#   - app.database (Supabase clients)
#   - app.services.audit_service.audit_service (the singleton used by routes)
#   - app.middleware.auth.SupabaseAuthMiddleware._verify_token (skip real JWT)
# ---------------------------------------------------------------------------

def _make_mock_settings():
    s = MagicMock()
    s.PROJECT_NAME = "GBP AI Discovery Optimizer"
    s.VERSION = "2.0.0"
    s.API_PREFIX = "/api/v1"
    s.DEBUG = False
    s.BACKEND_CORS_ORIGINS = "http://localhost:3000"
    s.cors_origins_list = ["http://localhost:3000"]
    s.RATE_LIMIT_PER_MINUTE = 100  # high limit so tests don't get throttled
    s.SENTRY_DSN = ""
    s.SUPABASE_URL = "https://fake.supabase.co"
    s.SUPABASE_ANON_KEY = "fake-anon"
    s.SUPABASE_SERVICE_KEY = "fake-service"
    s.GOOGLE_PLACES_API_KEY = "fake-places"
    s.GEMINI_API_KEY = "fake-gemini"
    s.OPENAI_API_KEY = None
    s.EVOLUTION_API_URL = "http://localhost:8080"
    s.EVOLUTION_API_KEY = ""
    s.EVOLUTION_INSTANCE_NAME = "default"
    s.OWNER_WHATSAPP = ""
    s.REDIS_URL = "redis://localhost:6379/0"
    s.CELERY_BROKER_URL = "redis://localhost:6379/0"
    s.CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
    s.MAX_REVIEWS_PER_AUDIT = 100
    s.AUDIT_CACHE_HOURS = 24
    s.AUDIT_PRICE_CENTS = 29700
    return s


@pytest.fixture(scope="module")
def client():
    """Create a TestClient for the FastAPI app with all services mocked."""
    mock_settings = _make_mock_settings()

    with patch("app.config.get_settings", return_value=mock_settings), \
         patch("app.database.get_supabase_client", return_value=MagicMock()), \
         patch("app.database.get_supabase_anon_client", return_value=MagicMock()):

        # Clear lru_cache so our patched settings are picked up
        from app.config import get_settings as _gs
        _gs.cache_clear()

        # Now import the app (triggers middleware + router registration)
        from app.main import app
        yield TestClient(app, raise_server_exceptions=False)

        _gs.cache_clear()


@pytest.fixture
def mock_audit_service():
    """Patch the audit_service singleton used by the route handlers."""
    with patch("app.api.routes.audit.audit_service") as mock_svc:
        yield mock_svc


# ---------------------------------------------------------------------------
# Helper to build a valid completed audit dict matching AuditResponse schema
# ---------------------------------------------------------------------------

def _completed_audit(audit_id="audit-001", **overrides):
    now = datetime.now(timezone.utc).isoformat()
    base = {
        "id": audit_id,
        "business_id": "biz-001",
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
    base.update(overrides)
    return base


def _pending_audit(audit_id="audit-002"):
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": audit_id,
        "business_id": "biz-001",
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


# ========================================================================
# Health endpoint
# ========================================================================


class TestHealthEndpoint:
    def test_health_check(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"


# ========================================================================
# Root endpoint
# ========================================================================


class TestRootEndpoint:
    def test_root_returns_info(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "GBP AI Discovery Optimizer" in data["message"]
        assert "version" in data
        assert "docs" in data


# ========================================================================
# POST /api/v1/audits
# ========================================================================


class TestCreateAudit:
    def test_create_audit_success(self, client, mock_audit_service):
        audit = _completed_audit()
        mock_audit_service.create_audit = AsyncMock(return_value=audit)

        resp = client.post(
            "/api/v1/audits",
            json={
                "business_name": "Clinica Sorriso",
                "location": "Sao Paulo",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] == "audit-001"
        assert data["status"] == "completed"
        mock_audit_service.create_audit.assert_awaited_once()

    def test_create_audit_with_whatsapp(self, client, mock_audit_service):
        audit = _completed_audit(delivery_mode="whatsapp", whatsapp_number="11999990000")
        mock_audit_service.create_audit = AsyncMock(return_value=audit)

        resp = client.post(
            "/api/v1/audits",
            json={
                "business_name": "Clinica Sorriso",
                "location": "Sao Paulo",
                "whatsapp": "11999990000",
                "delivery_mode": "whatsapp",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["delivery_mode"] == "whatsapp"

    def test_create_audit_business_not_found(self, client, mock_audit_service):
        mock_audit_service.create_audit = AsyncMock(
            side_effect=ValueError("Negocio nao encontrado")
        )
        resp = client.post(
            "/api/v1/audits",
            json={"business_name": "Nonexistent", "location": "Nowhere"},
        )
        assert resp.status_code == 404
        assert "Negocio nao encontrado" in resp.json()["detail"]

    def test_create_audit_internal_error(self, client, mock_audit_service):
        mock_audit_service.create_audit = AsyncMock(
            side_effect=RuntimeError("DB down")
        )
        resp = client.post(
            "/api/v1/audits",
            json={"business_name": "Biz", "location": "City"},
        )
        assert resp.status_code == 500

    def test_create_audit_validation_error_missing_fields(self, client, mock_audit_service):
        """Omitting required fields -> 422."""
        resp = client.post("/api/v1/audits", json={})
        assert resp.status_code == 422

    def test_create_audit_validation_error_short_name(self, client, mock_audit_service):
        """business_name too short (min_length=2) -> 422."""
        resp = client.post(
            "/api/v1/audits",
            json={"business_name": "X", "location": "Sao Paulo"},
        )
        assert resp.status_code == 422

    def test_create_audit_invalid_delivery_mode(self, client, mock_audit_service):
        """delivery_mode must be 'standalone' or 'whatsapp'."""
        resp = client.post(
            "/api/v1/audits",
            json={
                "business_name": "Clinica",
                "location": "SP",
                "delivery_mode": "email",
            },
        )
        assert resp.status_code == 422


# ========================================================================
# GET /api/v1/audits/{audit_id}
# ========================================================================


class TestGetAudit:
    def test_get_audit_success(self, client, mock_audit_service):
        audit = _completed_audit("audit-100")
        mock_audit_service.get_audit_status = AsyncMock(return_value=audit)

        resp = client.get("/api/v1/audits/audit-100")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "audit-100"
        assert data["discovery_score"] == 72

    def test_get_audit_not_found(self, client, mock_audit_service):
        mock_audit_service.get_audit_status = AsyncMock(
            side_effect=ValueError("Audit not found")
        )
        resp = client.get("/api/v1/audits/nonexistent")
        assert resp.status_code == 404

    def test_get_audit_processing(self, client, mock_audit_service):
        audit = _pending_audit()
        mock_audit_service.get_audit_status = AsyncMock(return_value=audit)

        resp = client.get("/api/v1/audits/audit-002")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "processing"
        assert data["discovery_score"] is None

    def test_get_audit_internal_error(self, client, mock_audit_service):
        mock_audit_service.get_audit_status = AsyncMock(
            side_effect=RuntimeError("Unexpected")
        )
        resp = client.get("/api/v1/audits/audit-err")
        assert resp.status_code == 500


# ========================================================================
# GET /api/v1/audits/{audit_id}/competitors
# ========================================================================


class TestGetCompetitors:
    def test_competitors_success(self, client, mock_audit_service):
        comp_data = {
            "competitive_score": 55.0,
            "competitors": [{"rank": 1, "name": "OdontoTop"}],
        }
        audit = _completed_audit(competitor_analysis=comp_data)
        mock_audit_service.get_audit_status = AsyncMock(return_value=audit)

        resp = client.get("/api/v1/audits/audit-001/competitors")
        assert resp.status_code == 200
        data = resp.json()
        assert data["competitive_score"] == 55.0

    def test_competitors_audit_not_completed(self, client, mock_audit_service):
        audit = _pending_audit()
        mock_audit_service.get_audit_status = AsyncMock(return_value=audit)

        resp = client.get("/api/v1/audits/audit-002/competitors")
        assert resp.status_code == 400

    def test_competitors_audit_not_found(self, client, mock_audit_service):
        mock_audit_service.get_audit_status = AsyncMock(
            side_effect=ValueError("Not found")
        )
        resp = client.get("/api/v1/audits/nope/competitors")
        assert resp.status_code == 404

    def test_competitors_returns_empty_when_none(self, client, mock_audit_service):
        audit = _completed_audit(competitor_analysis=None)
        mock_audit_service.get_audit_status = AsyncMock(return_value=audit)

        resp = client.get("/api/v1/audits/audit-001/competitors")
        assert resp.status_code == 200
        assert resp.json() == {}


# ========================================================================
# POST /api/v1/audits/{audit_id}/send-whatsapp
# ========================================================================


class TestSendWhatsApp:
    def test_send_whatsapp_success(self, client, mock_audit_service):
        mock_audit_service.send_whatsapp_report = AsyncMock(
            return_value={"success": True, "message_id": "msg-123"}
        )
        resp = client.post("/api/v1/audits/audit-001/send-whatsapp")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    def test_send_whatsapp_bad_request(self, client, mock_audit_service):
        mock_audit_service.send_whatsapp_report = AsyncMock(
            side_effect=ValueError("No WhatsApp number")
        )
        resp = client.post("/api/v1/audits/audit-001/send-whatsapp")
        assert resp.status_code == 400

    def test_send_whatsapp_internal_error(self, client, mock_audit_service):
        mock_audit_service.send_whatsapp_report = AsyncMock(
            side_effect=RuntimeError("Evolution API down")
        )
        resp = client.post("/api/v1/audits/audit-001/send-whatsapp")
        assert resp.status_code == 500


# ========================================================================
# GET /api/v1/audits/{audit_id}/report
# ========================================================================


class TestGetAuditReport:
    def test_report_not_found(self, client, mock_audit_service):
        mock_audit_service.get_audit_status = AsyncMock(
            side_effect=ValueError("Not found")
        )
        resp = client.get("/api/v1/audits/nope/report")
        assert resp.status_code == 404

    def test_report_not_completed(self, client, mock_audit_service):
        audit = _pending_audit()
        mock_audit_service.get_audit_status = AsyncMock(return_value=audit)

        resp = client.get("/api/v1/audits/audit-002/report")
        assert resp.status_code == 400

    def test_text_report_success(self, client, mock_audit_service):
        audit = _completed_audit()
        mock_audit_service.get_audit_status = AsyncMock(return_value=audit)

        with patch("app.api.routes.audit.build_report_text", return_value="Report text content"):
            resp = client.get("/api/v1/audits/audit-001/report?format=text")
            assert resp.status_code == 200
            assert "text/plain" in resp.headers["content-type"]

    def test_pdf_report_success(self, client, mock_audit_service):
        audit = _completed_audit(businesses={"name": "Clinica Test"})
        mock_audit_service.get_audit_status = AsyncMock(return_value=audit)

        with patch("app.api.routes.audit.build_report_pdf", return_value=b"%PDF-1.4 fake"):
            resp = client.get("/api/v1/audits/audit-001/report?format=pdf")
            assert resp.status_code == 200
            assert "application/pdf" in resp.headers["content-type"]

    def test_report_invalid_format(self, client, mock_audit_service):
        """format must be 'pdf' or 'text'; anything else -> 422."""
        audit = _completed_audit()
        mock_audit_service.get_audit_status = AsyncMock(return_value=audit)

        resp = client.get("/api/v1/audits/audit-001/report?format=csv")
        assert resp.status_code == 422


# ========================================================================
# Request body & content-type edge cases
# ========================================================================


class TestEdgeCases:
    def test_non_json_body_returns_422(self, client, mock_audit_service):
        resp = client.post(
            "/api/v1/audits",
            content=b"not json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 422

    def test_extra_fields_ignored(self, client, mock_audit_service):
        """Extra fields in request body are silently ignored by Pydantic."""
        audit = _completed_audit()
        mock_audit_service.create_audit = AsyncMock(return_value=audit)

        resp = client.post(
            "/api/v1/audits",
            json={
                "business_name": "Clinica",
                "location": "SP",
                "extra_field": "should be ignored",
            },
        )
        assert resp.status_code == 201
