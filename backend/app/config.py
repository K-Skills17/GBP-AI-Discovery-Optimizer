from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "GBP AI Discovery Optimizer"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_KEY: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Outscraper
    OUTSCRAPER_API_KEY: str
    
    # Google Gemini
    GEMINI_API_KEY: str
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
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
