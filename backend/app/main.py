"""Point d'entrée HTTP de l'application FastAPI."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings

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


@app.get(f"{settings.api_prefix}/health", tags=["Système"])
def health() -> dict[str, str]:
    """Confirme que FastAPI fonctionne, sans interroger PostgreSQL.

    Exemple de réponse : {"status": "ok", "application": "LCR Adjustment API"}
    """

    return {"status": "ok", "application": settings.app_name}
