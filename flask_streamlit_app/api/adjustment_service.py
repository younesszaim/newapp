"""Validation et création transactionnelle d'un bloc d'ajustement."""

import math
import secrets
from datetime import date, datetime
from uuid import uuid4

from psycopg2.extensions import connection as PostgreSQLConnection

from api.adjustment_repository import (
    insert_adjustment_trade,
    insert_registry_block,
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
