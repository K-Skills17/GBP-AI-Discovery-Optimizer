from supabase import create_client, Client
from app.config import get_settings

settings = get_settings()

def get_supabase_client() -> Client:
    """Get Supabase client for database operations"""
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_KEY
    )

def get_supabase_anon_client() -> Client:
    """Get anonymous Supabase client (for public operations)"""
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_ANON_KEY
    )
