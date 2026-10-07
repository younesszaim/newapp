"""Règles métier de création d'un ajustement."""

import secrets
from datetime import date, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException
from psycopg2.extensions import connection as PostgreSQLConnection

from app.config import ADJUSTMENT_DEFAULTS
from app.repositories.adjustment_repository import (
    delete_adjustment_trade,
    get_registry_entry_for_update,
    insert_adjustment_trade,
    insert_registry_entry,
    list_adjustments,
    mark_registry_entry_deleted,
    trade_no_exists,
)
from app.schemas.adjustment import (
    AdjustmentAmounts,
    AdjustmentBatchRequest,
    AdjustmentListItem,
    AdjustmentResponse,
)

CREATED_BY = "local_user"
MAX_BIGINT = 9_000_000_000_000_000_000


def generate_trade_no(connection: PostgreSQLConnection) -> int:
    """Génère un entier positif et vérifie qu'il n'existe pas déjà."""

    for _ in range(5):
        trade_no = secrets.randbelow(MAX_BIGINT - 1) + 1
        if not trade_no_exists(connection, trade_no):
            return trade_no

    raise HTTPException(status_code=500, detail="Impossible de générer un TradeNo unique.")


def _create_adjustment(
    connection: PostgreSQLConnection,
    *,
    asofdate: date,
    version: datetime,
    amounts: AdjustmentAmounts,
) -> AdjustmentResponse:
    """Insère un deal fictif dans la transaction courante."""

    adjustment_id = uuid4()
    bi_id = str(uuid4())
    trade_no = generate_trade_no(connection)

    insert_adjustment_trade(
        connection,
        bi_id=bi_id,
        trade_no=trade_no,
        asofdate=asofdate,
        version=version,
        defaults=ADJUSTMENT_DEFAULTS,
        lcr_reglementaire=amounts.ldp_impact_lcr_reglementaire,
        lcr_gestion=amounts.ldp_impact_lcr_gestion,
        impact_inflow=amounts.impact_lcr_inflow,
        impact_outflow=amounts.impact_lcr_outflow,
        impact_asset=amounts.impact_lcr_asset,
        impact_asset_cash=amounts.impact_lcr_asset_cash,
    )
    registry = insert_registry_entry(
        connection,
        adjustment_id=adjustment_id,
        bi_id=bi_id,
        asofdate=asofdate,
        version=version,
        created_by=CREATED_BY,
        trade_no=trade_no,
        lcr_reglementaire=amounts.ldp_impact_lcr_reglementaire,
        lcr_gestion=amounts.ldp_impact_lcr_gestion,
        impact_inflow=amounts.impact_lcr_inflow,
        impact_outflow=amounts.impact_lcr_outflow,
        impact_asset=amounts.impact_lcr_asset,
        impact_asset_cash=amounts.impact_lcr_asset_cash,
    )

    return AdjustmentResponse(
        adjustment_id=adjustment_id,
        bi_id=bi_id,
        trade_no=trade_no,
        asofdate=asofdate,
        asofdateflow_version=version,
        ldp_impact_lcr_reglementaire=amounts.ldp_impact_lcr_reglementaire,
        ldp_impact_lcr_gestion=amounts.ldp_impact_lcr_gestion,
        impact_lcr_inflow=amounts.impact_lcr_inflow,
        impact_lcr_outflow=amounts.impact_lcr_outflow,
        impact_lcr_asset=amounts.impact_lcr_asset,
        impact_lcr_asset_cash=amounts.impact_lcr_asset_cash,
        created_at=registry["created_at"],
        created_by=registry["created_by"],
        status=registry["status"],
    )


def create_adjustments(
    connection: PostgreSQLConnection,
    request: AdjustmentBatchRequest,
) -> list[AdjustmentResponse]:
    """Crée toutes les lignes AG Grid dans une seule transaction."""

    return [
        _create_adjustment(
            connection,
            asofdate=request.asofdate,
            version=request.asofdateflow_version,
            amounts=amounts,
        )
        for amounts in request.adjustments
    ]


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
