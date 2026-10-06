"""Point d'entrée HTTP de l'application FastAPI."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers.context_router import router as context_router
from app.routers.lcr_router import router as lcr_router
from app.routers.adjustment_router import router as adjustment_router

settings = get_settings()
app = FastAPI(title=settings.app_name)

# Angular et FastAPI utilisent deux ports différents. Le navigateur les traite
# donc comme deux origines. Ce middleware autorise uniquement le frontend local.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Les routes métier vivent dans des fichiers séparés. Le préfixe centralisé
# garantit que toutes les URLs publiques commencent par /api.
app.include_router(context_router, prefix=settings.api_prefix)
app.include_router(lcr_router, prefix=settings.api_prefix)
app.include_router(adjustment_router, prefix=settings.api_prefix)


@app.get(f"{settings.api_prefix}/health", tags=["Système"])
def health() -> dict[str, str]:
    """Confirme que FastAPI fonctionne, sans interroger PostgreSQL.

    Exemple de réponse : {"status": "ok", "application": "LCR Adjustment API"}
    """

    return {"status": "ok", "application": settings.app_name}
