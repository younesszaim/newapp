"""Requêtes SQL pour sélectionner le contexte LCR."""

from datetime import date

from psycopg2.extensions import connection as PostgreSQLConnection


def list_asofdates(connection: PostgreSQLConnection) -> list[str]:
    """Retourne les dates distinctes, de la plus récente à la plus ancienne."""

    query = """
        SELECT DISTINCT asofdate
        FROM public.completude_table
        WHERE asofdate IS NOT NULL
        ORDER BY asofdate DESC
    """
    with connection.cursor() as cursor:
        cursor.execute(query)
        return [row["asofdate"].isoformat() for row in cursor.fetchall()]


def list_versions(connection: PostgreSQLConnection, asofdate: date) -> list[str]:
    """Retourne les versions disponibles pour une date d'arrêté."""

    query = """
        SELECT DISTINCT asofdateflow_version
        FROM public.completude_table
        WHERE asofdate = %s
          AND asofdateflow_version IS NOT NULL
        ORDER BY asofdateflow_version DESC
    """
    with connection.cursor() as cursor:
        cursor.execute(query, (asofdate,))
        return [row["asofdateflow_version"].isoformat() for row in cursor.fetchall()]
