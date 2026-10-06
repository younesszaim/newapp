"""Routes HTTP de gestion des ajustements."""

from uuid import UUID

from fastapi import APIRouter, status

from app.routers.context_router import DatabaseConnection
from app.schemas.adjustment import AdjustmentListItem, AdjustmentRequest, AdjustmentResponse
from app.services.adjustment_service import (
    create_adjustment,
    delete_adjustment,
    get_adjustments,
)

router = APIRouter(prefix="/adjustments", tags=["Ajustements"])


@router.get("", response_model=list[AdjustmentListItem], response_model_by_alias=True)
def list_manual_adjustments(connection: DatabaseConnection) -> list[AdjustmentListItem]:
    """Retourne les ajustements actifs et supprimés du registre."""

    return get_adjustments(connection)


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


@router.delete("/{adjustment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_manual_adjustment(
    adjustment_id: UUID,
    connection: DatabaseConnection,
) -> None:
    """Supprime le trade et conserve le registre avec le statut DELETED."""

    delete_adjustment(connection, adjustment_id)
