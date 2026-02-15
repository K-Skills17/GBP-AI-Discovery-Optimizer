from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List, Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "GBP AI Discovery Optimizer"
    VERSION: str = "2.0.0"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # Supabase
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_KEY: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Google Places API (New)
    GOOGLE_PLACES_API_KEY: str

    # Gemini API (primary AI engine)
    GEMINI_API_KEY: str

    # OpenAI (optional fallback)
    OPENAI_API_KEY: Optional[str] = None

    # Evolution API (WhatsApp)
    EVOLUTION_API_URL: str = "https://evolution-api-4mbe.onrender.com"
    EVOLUTION_API_KEY: str = ""
    EVOLUTION_INSTANCE_NAME: str = "GBP-AI-Discovery-Optimizer"

    # Owner notification
    OWNER_WHATSAPP: str = ""

    # Sentry (error monitoring)
    SENTRY_DSN: Optional[str] = None

    # CORS — accepts comma-separated string or JSON array in env var
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from string (comma-separated or JSON array)."""
        val = self.BACKEND_CORS_ORIGINS.strip()
        if val.startswith("["):
            import json
            return json.loads(val)
        return [origin.strip() for origin in val.split(",") if origin.strip()]

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 10

    # Limits
    MAX_REVIEWS_PER_AUDIT: int = 100
    AUDIT_CACHE_HOURS: int = 24

    # Pricing (in cents)
    AUDIT_PRICE_CENTS: int = 29700  # R$ 297.00

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()
