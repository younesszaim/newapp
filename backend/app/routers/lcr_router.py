"""Route HTTP du résumé LCR."""

from datetime import date, datetime

from fastapi import APIRouter

from app.routers.context_router import DatabaseConnection
from app.schemas.lcr import LcrSummary
from app.services.lcr_service import build_lcr_summary

router = APIRouter(tags=["LCR"])


@router.get("/lcr-summary", response_model=LcrSummary, response_model_by_alias=True)
def get_lcr_summary(
    asofdate: date,
    version: datetime,
    connection: DatabaseConnection,
) -> LcrSummary:
    """Retourne l'agrégation par product line et les totaux du contexte."""

    return build_lcr_summary(connection, asofdate, version)
