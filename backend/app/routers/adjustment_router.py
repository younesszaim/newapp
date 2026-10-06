"""Routes HTTP de gestion des ajustements."""

from fastapi import APIRouter, status

from app.routers.context_router import DatabaseConnection
from app.schemas.adjustment import AdjustmentRequest, AdjustmentResponse
from app.services.adjustment_service import create_adjustment

router = APIRouter(prefix="/adjustments", tags=["Ajustements"])


@router.post(
    "",
    response_model=AdjustmentResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
def create_manual_adjustment(
    request: AdjustmentRequest,
    connection: DatabaseConnection,
) -> AdjustmentResponse:
    """Crée un trade fictif et son registre dans une seule transaction."""

    return create_adjustment(connection, request)
