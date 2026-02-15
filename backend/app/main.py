from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.routes import audit, health
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.auth import SupabaseAuthMiddleware

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

settings = get_settings()

# ------------------------------------------------------------------
# Sentry (optional — only initialised when SENTRY_DSN is set)
# ------------------------------------------------------------------
if settings.SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            traces_sample_rate=0.2,
            integrations=[
                StarletteIntegration(transaction_style="endpoint"),
                FastApiIntegration(transaction_style="endpoint"),
            ],
        )
        logging.getLogger(__name__).info("Sentry initialised")
    except ImportError:
        logging.getLogger(__name__).warning(
            "sentry-sdk not installed — error monitoring disabled"
        )

# ------------------------------------------------------------------
# FastAPI app
# ------------------------------------------------------------------
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "API para diagnóstico competitivo e auditoria de descoberta AI "
        "em perfis do Google Meu Negócio.  "
        "Usa Google Places API + Gemini API + Evolution API (WhatsApp)."
    ),
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
)

# ------------------------------------------------------------------
# Middleware — last add_middleware() call = outermost in Starlette.
# CORS must be outermost so preflight OPTIONS requests get handled
# before auth or rate-limiting can reject them.
# ------------------------------------------------------------------
app.add_middleware(SupabaseAuthMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# Routers
# ------------------------------------------------------------------
app.include_router(health.router, prefix=settings.API_PREFIX, tags=["health"])
app.include_router(audit.router, prefix=settings.API_PREFIX, tags=["audits"])


@app.get("/")
def root():
    return {
        "message": "GBP AI Discovery Optimizer API",
        "version": settings.VERSION,
        "docs": f"{settings.API_PREFIX}/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
