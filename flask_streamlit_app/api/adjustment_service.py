"""Validation et création transactionnelle d'un bloc d'ajustement."""

import secrets
from uuid import UUID
from uuid import uuid4

from psycopg2.extensions import connection as PostgreSQLConnection

from api.adjustment_repository import (
    insert_adjustment_trade,
    insert_registry_block,
    list_registry_blocks,
    get_registry_block_for_update,
    delete_adjustment_trades,
    mark_registry_block_deleted,
    trade_no_exists,
)
from api.config import ADJUSTMENT_DEFAULTS, get_settings
from api.errors import (
    AdjustmentConflictError,
    AdjustmentNotFoundError,
    TradeNumberGenerationError,
)
from api.adjustment_models import (
    AdjustmentBatchRequest,
    AdjustmentCreationResponse,
)


def create_adjustment_block(
    connection: PostgreSQLConnection,
    request: AdjustmentBatchRequest,
) -> AdjustmentCreationResponse:
    """Insère toutes les lignes, puis leur unique en-tête de registre."""

    adjustment_id = uuid4()
    settings = get_settings()
    bi_ids = []
    for amounts in request.adjustments:
        bi_id = str(uuid4())
        bi_ids.append(bi_id)
        insert_adjustment_trade(
            connection,
            bi_id=bi_id,
            trade_no=_generate_trade_no(connection),
            asofdate=request.asofdate,
            version=request.version,
            defaults=ADJUSTMENT_DEFAULTS,
            amounts=amounts.model_dump(by_alias=True),
        )

    insert_registry_block(
        connection,
        adjustment_id=adjustment_id,
        bi_ids=bi_ids,
        asofdate=request.asofdate,
        version=request.version,
        created_by=settings.created_by,
    )
    return AdjustmentCreationResponse(
        adjustment_id=adjustment_id,
        line_count=len(bi_ids),
    )


def get_adjustment_registry(connection: PostgreSQLConnection) -> list[dict]:
    """Prépare les blocs PostgreSQL pour leur sérialisation JSON."""

    return [_serialize_block(block) for block in list_registry_blocks(connection)]


def delete_adjustment_block(
    connection: PostgreSQLConnection,
    adjustment_id: UUID,
) -> None:
    """Supprime toutes les lignes et conserve seulement l'audit du bloc."""

    block = get_registry_block_for_update(connection, adjustment_id)
    if block is None:
        raise AdjustmentNotFoundError("Ajustement introuvable.")
    if block["status"] == "DELETED":
        raise AdjustmentConflictError("Cet ajustement est déjà supprimé.")

    bi_ids = block["bi_ids"]
    if not bi_ids or delete_adjustment_trades(connection, bi_ids) != len(bi_ids):
        raise AdjustmentConflictError(
            "Une ou plusieurs lignes de l'ajustement sont introuvables."
        )
    mark_registry_block_deleted(
        connection,
        adjustment_id,
        get_settings().created_by,
    )


def _serialize_block(block: dict) -> dict:
    """Convertit UUID, dates, Decimal et noms SQL vers le contrat JSON."""

    return {
        "adjustmentId": str(block["adjustment_id"]),
        "asofdate": block["asofdate"].isoformat(),
        "asofdateflowVersion": block["asofdateflow_version"].isoformat(),
        "createdAt": block["created_at"].isoformat(),
        "createdBy": block["created_by"],
        "status": block["status"],
        "deletedAt": block["deleted_at"].isoformat() if block["deleted_at"] else None,
        "deletedBy": block["deleted_by"],
        "lastEventAt": (block["deleted_at"] or block["created_at"]).isoformat(),
        "lines": [
            {
                "biId": line["bi_id"],
                "tradeNo": line["tradeno"],
                "ldpImpactLcrReglementaire": float(line["ldp_impact_lcr_reglementaire"]),
                "ldpImpactLcrGestion": float(line["ldp_impact_lcr_gestion"]),
                "impactLcrInflow": float(line["impact_lcr_inflow"]),
                "impactLcrOutflow": float(line["impact_lcr_outflow"]),
                "impactLcrAsset": float(line["impact_lcr_asset"]),
                "impactLcrAssetCash": float(line["impact_lcr_asset_cash"]),
            }
            for line in block["lines"]
        ],
    }


def _generate_trade_no(connection: PostgreSQLConnection) -> int:
    for _ in range(5):
        trade_no = secrets.randbelow(9_000_000_000_000_000_000 - 1) + 1
        if not trade_no_exists(connection, trade_no):
            return trade_no
    raise TradeNumberGenerationError("Impossible de générer un TradeNo unique.")
