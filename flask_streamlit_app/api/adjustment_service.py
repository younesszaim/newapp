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
from api.adjustment_records import RegistryBlockRecord
from api.config import ADJUSTMENT_DEFAULTS, get_settings
from api.errors import (
    AdjustmentConflictError,
    AdjustmentNotFoundError,
    TradeNumberGenerationError,
)
from api.adjustment_models import (
    AdjustmentBatchRequest,
    AdjustmentCreationResponse,
    AdjustmentLineResponse,
    AdjustmentRegistryBlockResponse,
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


def get_adjustment_registry(
    connection: PostgreSQLConnection,
) -> list[AdjustmentRegistryBlockResponse]:
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
    if block.status == "DELETED":
        raise AdjustmentConflictError("Cet ajustement est déjà supprimé.")

    bi_ids = list(block.bi_ids)
    if not bi_ids or delete_adjustment_trades(connection, bi_ids) != len(bi_ids):
        raise AdjustmentConflictError(
            "Une ou plusieurs lignes de l'ajustement sont introuvables."
        )
    mark_registry_block_deleted(
        connection,
        adjustment_id,
        get_settings().created_by,
    )


def _serialize_block(block: RegistryBlockRecord) -> AdjustmentRegistryBlockResponse:
    """Convertit une ligne SQL en bloc de registre Pydantic."""

    lines = [
        AdjustmentLineResponse(
            bi_id=line.bi_id,
            trade_no=line.trade_no,
            lcr_reglementaire=line.lcr_reglementaire,
            lcr_gestion=line.lcr_gestion,
            inflow=line.inflow,
            outflow=line.outflow,
            asset=line.asset,
            asset_cash=line.asset_cash,
        )
        for line in block.lines
    ]
    return AdjustmentRegistryBlockResponse(
        adjustment_id=block.adjustment_id,
        asofdate=block.asofdate,
        version=block.version,
        created_at=block.created_at,
        created_by=block.created_by,
        status=block.status,
        deleted_at=block.deleted_at,
        deleted_by=block.deleted_by,
        last_event_at=block.deleted_at or block.created_at,
        lines=lines,
    )


def _generate_trade_no(connection: PostgreSQLConnection) -> int:
    for _ in range(5):
        trade_no = secrets.randbelow(9_000_000_000_000_000_000 - 1) + 1
        if not trade_no_exists(connection, trade_no):
            return trade_no
    raise TradeNumberGenerationError("Impossible de générer un TradeNo unique.")
