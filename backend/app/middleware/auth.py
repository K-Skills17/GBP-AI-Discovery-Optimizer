"""Optional Supabase JWT auth middleware.

When a valid Authorization: Bearer <token> header is present, the request
gets annotated with `request.state.user_id`.  When absent, the request
proceeds as anonymous (user_id = None).

Endpoints that REQUIRE auth should check `request.state.user_id` explicitly.
This keeps the audit creation endpoint open (for ad funnel) while still
supporting authenticated users.
"""

import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SupabaseAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.user_id = None

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            user_id = await self._verify_token(token)
            if user_id:
                request.state.user_id = user_id

        response = await call_next(request)
        return response

    async def _verify_token(self, token: str):
        """Verify Supabase JWT and return user id.

        Uses supabase-py's auth.get_user() which validates against
        the Supabase project's JWT secret.
        """
        try:
            from app.database import get_supabase_anon_client

            client = get_supabase_anon_client()
            user_response = client.auth.get_user(token)
            if user_response and user_response.user:
                return str(user_response.user.id)
        except Exception as e:
            logger.debug(f"Auth token invalid: {e}")
        return None
