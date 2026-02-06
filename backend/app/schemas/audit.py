from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class AuditCreateRequest(BaseModel):
    business_name: str = Field(..., min_length=2, max_length=200)
    location: str = Field(..., min_length=2, max_length=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "business_name": "Clínica Dental Sorriso",
                "location": "São Paulo"
            }
        }

class AuditResponse(BaseModel):
    id: str
    business_id: str
    status: str
    discovery_score: Optional[int] = None
    sentiment_score: Optional[float] = None
    visual_coverage_score: Optional[float] = None
    ai_summary: Optional[Dict[str, Any]] = None
    sentiment_analysis: Optional[Dict[str, Any]] = None
    conversational_queries: Optional[List[Dict[str, Any]]] = None
    visual_audit: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[Dict[str, Any]]] = None
    processing_time_seconds: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
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
