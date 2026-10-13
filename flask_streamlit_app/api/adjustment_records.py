"""Objets internes représentant les résultats PostgreSQL des ajustements."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class AdjustmentTradeRecord:
    """Ligne active chargée depuis public.completude_table."""

    bi_id: str
    trade_no: int
    lcr_reglementaire: Decimal
    lcr_gestion: Decimal
    inflow: Decimal
    outflow: Decimal
    asset: Decimal
    asset_cash: Decimal


@dataclass(frozen=True, slots=True)
class RegistryBlockRecord:
    """Bloc du registre enrichi de ses lignes encore actives."""

    adjustment_id: UUID
    asofdate: date
    version: datetime
    created_at: datetime
    created_by: str
    status: Literal["ACTIVE", "DELETED"]
    deleted_at: datetime | None
    deleted_by: str | None
    lines: tuple[AdjustmentTradeRecord, ...]


@dataclass(frozen=True, slots=True)
class RegistryBlockLockRecord:
    """Projection minimale verrouillée pendant une suppression."""

    adjustment_id: UUID
    bi_ids: tuple[str, ...]
    status: Literal["ACTIVE", "DELETED"]
