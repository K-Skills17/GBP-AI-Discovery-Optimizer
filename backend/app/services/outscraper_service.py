"""
DEPRECATED: This module has been replaced by places_service.py which uses
the Google Places API (New) directly instead of the Outscraper wrapper.

All business search, details, and review fetching is now handled by
app.services.places_service.places_service

This file is kept only as a reference. Do not import from here.
"""

raise ImportError(
    "outscraper_service is deprecated. Use places_service instead: "
    "from app.services.places_service import places_service"
)
