"""Requêtes de lecture de la table public.completude_table."""

from datetime import date, datetime

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
