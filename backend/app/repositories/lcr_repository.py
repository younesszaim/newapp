"""Requêtes de lecture de la table public.completude_table."""

from datetime import date, datetime
from typing import Any

from psycopg2.extensions import connection as PostgreSQLConnection


def get_asofdates(connection: PostgreSQLConnection) -> list[date]:
    """Retourne les dates de reporting disponibles, de la plus récente à l'ancienne.

    Une seule requête est envoyée à PostgreSQL. ``DISTINCT`` supprime les
    doublons car plusieurs trades partagent normalement la même Asofdate.

    Exemple de retour Python :
        [date(2026, 10, 5), date(2026, 10, 4)]
    """

    query = """
        SELECT DISTINCT asofdate
        FROM public.completude_table
        WHERE asofdate IS NOT NULL
        ORDER BY asofdate DESC
    """

    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()

    return [row["asofdate"] for row in rows]


def get_versions(
    connection: PostgreSQLConnection,
    asofdate: date,
) -> list[datetime]:
    """Retourne les versions disponibles pour une Asofdate.

    ``%s`` est un paramètre psycopg2 : la date n'est jamais concaténée dans le
    SQL. Psycopg2 se charge de l'envoyer proprement à PostgreSQL.

    Exemple de retour Python :
        [datetime(2026, 10, 6, 11, 45), datetime(2026, 10, 6, 9, 30)]
    """

    query = """
        SELECT DISTINCT asofdateflow_version
        FROM public.completude_table
        WHERE asofdate = %s
          AND asofdateflow_version IS NOT NULL
        ORDER BY asofdateflow_version DESC
    """

    with connection.cursor() as cursor:
        cursor.execute(query, (asofdate,))
        rows = cursor.fetchall()

    return [row["asofdateflow_version"] for row in rows]


def get_lcr_summary_rows(
    connection: PostgreSQLConnection,
    asofdate: date,
    version: datetime,
) -> list[dict[str, Any]]:
    """Agrège toutes les lignes du contexte avec un seul GROUP BY."""

    query = """
        SELECT
            COALESCE(product_line, 'NON RENSEIGNÉ') AS product_line,
            COALESCE(SUM(eur_amount_od), 0) AS amount_0d,
            COALESCE(SUM(eur_amount_30d), 0) AS amount_30d,
            COALESCE(SUM(ldp_impact_lcr_reglementaire), 0)
                AS lcr_reglementaire,
            COALESCE(SUM(ldp_impact_lcr_gestion), 0)
                AS lcr_gestion
        FROM public.completude_table
        WHERE asofdate = %s
          AND asofdateflow_version = %s
        GROUP BY product_line
        ORDER BY product_line
    """

    with connection.cursor() as cursor:
        cursor.execute(query, (asofdate, version))
        rows = cursor.fetchall()

    return [dict(row) for row in rows]


def get_active_adjustment(
    connection: PostgreSQLConnection,
    asofdate: date,
    version: datetime,
) -> dict[str, Any] | None:
    """Retourne l'ajustement ACTIVE du registre et ses deux impacts principaux."""

    query = """
        SELECT
            registry.adjustment_id,
            registry.bi_id,
            trade.ldp_impact_lcr_reglementaire,
            trade.ldp_impact_lcr_gestion,
            registry.created_at,
            registry.created_by
        FROM public.adjustment_registry AS registry
        JOIN public.completude_table AS trade
          ON trade.bi_id = registry.bi_id
        WHERE registry.asofdate = %s
          AND registry.asofdateflow_version = %s
          AND registry.status = 'ACTIVE'
        LIMIT 1
    """

    with connection.cursor() as cursor:
        cursor.execute(query, (asofdate, version))
        row = cursor.fetchone()

    return dict(row) if row else None
