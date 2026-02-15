from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class AuditCreateRequest(BaseModel):
    business_name: str = Field(..., min_length=2, max_length=200)
    location: str = Field(..., min_length=2, max_length=100)
    whatsapp: Optional[str] = Field(None, min_length=10, max_length=20)
    utm_source: Optional[str] = Field(None, max_length=100)
    utm_medium: Optional[str] = Field(None, max_length=100)
    utm_campaign: Optional[str] = Field(None, max_length=200)
    utm_content: Optional[str] = Field(None, max_length=200)

    @field_validator("whatsapp")
    @classmethod
    def validate_whatsapp(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        digits = "".join(c for c in v if c.isdigit())
        if len(digits) < 10 or len(digits) > 13:
            raise ValueError(
                "Número de WhatsApp inválido. Use o formato: DDD + número (ex: 11999991234)"
            )
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "business_name": "Clínica Dental Sorriso",
                "location": "São Paulo",
                "whatsapp": "11999991234",
                "utm_source": "facebook",
                "utm_campaign": "dental_sp_jan",
            }
        }


class CompetitorResponse(BaseModel):
    rank: int
    name: str
    place_id: Optional[str] = None
    address: Optional[str] = None
    rating: Optional[float] = None
    total_reviews: int = 0
    photos_count: int = 0
    category: Optional[str] = None
    website: Optional[str] = None
    google_maps_url: Optional[str] = None
    ai_mentioned: bool = False

    class Config:
        from_attributes = True


class AuditResponse(BaseModel):
    id: str
    business_id: Optional[str] = None
    status: str
    discovery_score: Optional[int] = None
    competitive_score: Optional[float] = None
    sentiment_score: Optional[float] = None
    visual_coverage_score: Optional[float] = None
    ai_summary: Optional[Dict[str, Any]] = None
    sentiment_analysis: Optional[Dict[str, Any]] = None
    conversational_queries: Optional[List[Dict[str, Any]]] = None
    visual_audit: Optional[Dict[str, Any]] = None
    competitor_analysis: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[Dict[str, Any]]] = None
    processing_time_seconds: Optional[int] = None
    error_message: Optional[str] = None
    whatsapp_number: Optional[str] = None
    whatsapp_sent: Optional[bool] = None
    whatsapp_sent_at: Optional[datetime] = None
    whatsapp_error: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_content: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BusinessResponse(BaseModel):
    id: str
    place_id: str
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    category: Optional[str] = None
    rating: Optional[float] = None
    total_reviews: int = 0

    class Config:
        from_attributes = True
