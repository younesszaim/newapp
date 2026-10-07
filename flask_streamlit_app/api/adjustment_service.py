"""Validation et création transactionnelle d'un bloc d'ajustement."""

import math
import secrets
from datetime import date, datetime
from uuid import uuid4
from uuid import UUID

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
from api.config import ADJUSTMENT_DEFAULTS

REQUIRED_FIELDS = ("ldpImpactLcrReglementaire", "ldpImpactLcrGestion")
OPTIONAL_FIELDS = (
    "impactLcrInflow", "impactLcrOutflow", "impactLcrAsset", "impactLcrAssetCash"
)


def validate_adjustment_lines(lines: object) -> list[dict[str, float]]:
    """Valide 1 à 100 lignes et convertit les cellules en nombres."""

    if not isinstance(lines, list) or not 1 <= len(lines) <= 100:
        raise ValueError("Un ajustement doit contenir entre 1 et 100 lignes.")

    validated = []
    for line in lines:
        if not isinstance(line, dict):
            raise ValueError("Chaque ligne doit être un objet JSON.")
        result = {}
        for field in REQUIRED_FIELDS:
            if line.get(field) in (None, ""):
                raise ValueError("Toutes les colonnes obligatoires doivent être renseignées.")
            result[field] = _finite_number(line[field])
        for field in OPTIONAL_FIELDS:
            result[field] = _finite_number(line.get(field, 0) or 0)
        validated.append(result)
    return validated


def create_adjustment_block(
    connection: PostgreSQLConnection,
    asofdate: date,
    version: datetime,
    lines: list[dict[str, float]],
) -> dict:
    """Insère toutes les lignes, puis leur unique en-tête de registre."""

    adjustment_id = uuid4()
    bi_ids = []
    for amounts in lines:
        bi_id = str(uuid4())
        bi_ids.append(bi_id)
        insert_adjustment_trade(
            connection,
            bi_id=bi_id,
            trade_no=_generate_trade_no(connection),
            asofdate=asofdate,
            version=version,
            defaults=ADJUSTMENT_DEFAULTS,
            amounts=amounts,
        )

    insert_registry_block(
        connection,
        adjustment_id=adjustment_id,
        bi_ids=bi_ids,
        asofdate=asofdate,
        version=version,
        created_by="local_user",
    )
    return {"adjustmentId": str(adjustment_id), "lineCount": len(bi_ids), "status": "ACTIVE"}


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
        raise LookupError("Ajustement introuvable.")
    if block["status"] == "DELETED":
        raise ValueError("Cet ajustement est déjà supprimé.")

    bi_ids = block["bi_ids"]
    if not bi_ids or delete_adjustment_trades(connection, bi_ids) != len(bi_ids):
        raise ValueError("Une ou plusieurs lignes de l'ajustement sont introuvables.")
    mark_registry_block_deleted(connection, adjustment_id, "local_user")


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


def _finite_number(value: object) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError("Les montants doivent être numériques.") from error
    if not math.isfinite(number):
        raise ValueError("Les montants doivent être des nombres finis.")
    return number


def _generate_trade_no(connection: PostgreSQLConnection) -> int:
    for _ in range(5):
        trade_no = secrets.randbelow(9_000_000_000_000_000_000 - 1) + 1
        if not trade_no_exists(connection, trade_no):
            return trade_no
    raise RuntimeError("Impossible de générer un TradeNo unique.")
