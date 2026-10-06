"""Règles métier de création d'un ajustement."""

import secrets
from uuid import UUID, uuid4

from fastapi import HTTPException
from psycopg2 import errors
from psycopg2.extensions import connection as PostgreSQLConnection

from app.config import ADJUSTMENT_DEFAULTS
from app.repositories.adjustment_repository import (
    adjustment_exists,
    delete_adjustment_trade,
    get_registry_entry_for_update,
    insert_adjustment_trade,
    insert_registry_entry,
    list_adjustments,
    mark_registry_entry_deleted,
    trade_no_exists,
)
from app.schemas.adjustment import AdjustmentListItem, AdjustmentRequest, AdjustmentResponse

CREATED_BY = "local_user"
MAX_BIGINT = 9_000_000_000_000_000_000


def generate_trade_no(connection: PostgreSQLConnection) -> int:
    """Génère un entier positif et vérifie qu'il n'existe pas déjà."""

    for _ in range(5):
        trade_no = secrets.randbelow(MAX_BIGINT - 1) + 1
        if not trade_no_exists(connection, trade_no):
            return trade_no

    raise HTTPException(status_code=500, detail="Impossible de générer un TradeNo unique.")


def create_adjustment(
    connection: PostgreSQLConnection,
    request: AdjustmentRequest,
) -> AdjustmentResponse:
    """Insère le trade et son registre dans la transaction de la connexion."""

    if adjustment_exists(connection, request.asofdate, request.asofdateflow_version):
        raise HTTPException(
            status_code=409,
            detail="Un ajustement existe déjà pour cette date et cette version.",
        )

    adjustment_id = uuid4()
    bi_id = str(uuid4())
    trade_no = generate_trade_no(connection)

    try:
        insert_adjustment_trade(
            connection,
            bi_id=bi_id,
            trade_no=trade_no,
            asofdate=request.asofdate,
            version=request.asofdateflow_version,
            defaults=ADJUSTMENT_DEFAULTS,
            lcr_reglementaire=request.ldp_impact_lcr_reglementaire,
            lcr_gestion=request.ldp_impact_lcr_gestion,
            impact_inflow=request.impact_lcr_inflow,
            impact_outflow=request.impact_lcr_outflow,
            impact_asset=request.impact_lcr_asset,
            impact_asset_cash=request.impact_lcr_asset_cash,
        )
        registry = insert_registry_entry(
            connection,
            adjustment_id=adjustment_id,
            bi_id=bi_id,
            asofdate=request.asofdate,
            version=request.asofdateflow_version,
            created_by=CREATED_BY,
            trade_no=trade_no,
            lcr_reglementaire=request.ldp_impact_lcr_reglementaire,
            lcr_gestion=request.ldp_impact_lcr_gestion,
            impact_inflow=request.impact_lcr_inflow,
            impact_outflow=request.impact_lcr_outflow,
            impact_asset=request.impact_lcr_asset,
            impact_asset_cash=request.impact_lcr_asset_cash,
        )
    except errors.UniqueViolation as error:
        # L'index unique partiel protège aussi contre deux requêtes concurrentes.
        raise HTTPException(
            status_code=409,
            detail="Un ajustement existe déjà pour cette date et cette version.",
        ) from error

    return AdjustmentResponse(
        adjustment_id=adjustment_id,
        bi_id=bi_id,
        trade_no=trade_no,
        asofdate=request.asofdate,
        asofdateflow_version=request.asofdateflow_version,
        ldp_impact_lcr_reglementaire=request.ldp_impact_lcr_reglementaire,
        ldp_impact_lcr_gestion=request.ldp_impact_lcr_gestion,
        impact_lcr_inflow=request.impact_lcr_inflow,
        impact_lcr_outflow=request.impact_lcr_outflow,
        impact_lcr_asset=request.impact_lcr_asset,
        impact_lcr_asset_cash=request.impact_lcr_asset_cash,
        created_at=registry["created_at"],
        created_by=registry["created_by"],
        status=registry["status"],
    )


def get_adjustments(connection: PostgreSQLConnection) -> list[AdjustmentListItem]:
    """Convertit les lignes SQL du registre en contrats API."""

    return [AdjustmentListItem(**row) for row in list_adjustments(connection)]


def delete_adjustment(connection: PostgreSQLConnection, adjustment_id: UUID) -> None:
    """Supprime le trade et garde sa trace d'audit dans la même transaction."""

    registry = get_registry_entry_for_update(connection, adjustment_id)
    if registry is None:
        raise HTTPException(status_code=404, detail="Ajustement introuvable.")
    if registry["status"] == "DELETED":
        raise HTTPException(status_code=409, detail="Cet ajustement est déjà supprimé.")

    if not delete_adjustment_trade(connection, registry["bi_id"]):
        raise HTTPException(
            status_code=409,
            detail="Le trade associé à cet ajustement est introuvable.",
        )

    mark_registry_entry_deleted(connection, adjustment_id, CREATED_BY)
