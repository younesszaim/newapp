"""Assemblage du résumé LCR renvoyé au frontend."""

from datetime import date, datetime

from psycopg2.extensions import connection as PostgreSQLConnection

from app.repositories.lcr_repository import get_active_adjustment, get_lcr_summary_rows
from app.schemas.lcr import ExistingAdjustment, LcrSummary, LcrSummaryRow, LcrSummaryTotal


def build_lcr_summary(
    connection: PostgreSQLConnection,
    asofdate: date,
    version: datetime,
) -> LcrSummary:
    """Charge les lignes, calcule les totaux et ajoute l'ajustement actif."""

    database_rows = get_lcr_summary_rows(connection, asofdate, version)
    rows = [LcrSummaryRow(**row) for row in database_rows]

    # Les sommes SQL restent exactes jusqu'ici. La conversion en float est faite
    # seulement par le schéma de sortie attendu par Angular.
    total = LcrSummaryTotal(
        amount_0d=sum(row.amount_0d for row in rows),
        amount_30d=sum(row.amount_30d for row in rows),
        lcr_reglementaire=sum(row.lcr_reglementaire for row in rows),
        lcr_gestion=sum(row.lcr_gestion for row in rows),
    )

    adjustment_data = get_active_adjustment(connection, asofdate, version)
    adjustment = ExistingAdjustment(**adjustment_data) if adjustment_data else None

    return LcrSummary(
        asofdate=asofdate,
        asofdateflow_version=version,
        rows=rows,
        total=total,
        has_adjustment=adjustment is not None,
        adjustment=adjustment,
    )
