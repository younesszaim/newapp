"""Construction de la réponse JSON du résumé LCR."""

from datetime import date, datetime

from psycopg2.extensions import connection as PostgreSQLConnection

from api.lcr_repository import get_lcr_summary_rows


def build_lcr_summary(
    connection: PostgreSQLConnection,
    asofdate: date,
    version: datetime,
) -> dict:
    """Convertit les montants PostgreSQL et calcule les quatre totaux."""

    rows = [
        {
            "productLine": row["product_line"],
            "amount0d": float(row["amount_0d"]),
            "amount30d": float(row["amount_30d"]),
            "lcrReglementaire": float(row["lcr_reglementaire"]),
            "lcrGestion": float(row["lcr_gestion"]),
        }
        for row in get_lcr_summary_rows(connection, asofdate, version)
    ]
    total_fields = ("amount0d", "amount30d", "lcrReglementaire", "lcrGestion")

    return {
        "asofdate": asofdate.isoformat(),
        "asofdateflowVersion": version.isoformat(),
        "rows": rows,
        "total": {
            field: sum(row[field] for row in rows)
            for field in total_fields
        },
    }
