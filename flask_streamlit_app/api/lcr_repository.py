"""Agrégation SQL du résumé LCR."""

from datetime import date, datetime
from typing import Any

from psycopg2.extensions import connection as PostgreSQLConnection


def get_lcr_summary_rows(
    connection: PostgreSQLConnection,
    asofdate: date,
    version: datetime,
) -> list[dict[str, Any]]:
    """Agrège le contexte par Product Line dans une seule requête."""

    query = """
        SELECT
            COALESCE(product_line, 'NON RENSEIGNÉ') AS product_line,
            COALESCE(SUM(eur_amount_od), 0) AS amount_0d,
            COALESCE(SUM(eur_amount_30d), 0) AS amount_30d,
            COALESCE(SUM(ldp_impact_lcr_reglementaire), 0) AS lcr_reglementaire,
            COALESCE(SUM(ldp_impact_lcr_gestion), 0) AS lcr_gestion
        FROM public.completude_table
        WHERE asofdate = %s
          AND asofdateflow_version = %s
        GROUP BY product_line
        ORDER BY product_line
    """
    with connection.cursor() as cursor:
        cursor.execute(query, (asofdate, version))
        return [dict(row) for row in cursor.fetchall()]
