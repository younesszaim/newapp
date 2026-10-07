"""Requêtes SQL pour sélectionner le contexte LCR."""

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
