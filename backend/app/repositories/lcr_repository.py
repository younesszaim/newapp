"""Requêtes de lecture de la table public.completude_table."""

from datetime import date

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
