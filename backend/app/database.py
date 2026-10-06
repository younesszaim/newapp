"""Ouverture des connexions PostgreSQL avec psycopg2."""

from collections.abc import Iterator
import os

from fastapi import HTTPException
import psycopg2
from psycopg2 import DatabaseError
from psycopg2.extensions import connection as PostgreSQLConnection
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Charge les variables du fichier backend/.env dans l'environnement local.
load_dotenv()


def get_connection() -> Iterator[PostgreSQLConnection]:
    """Fournit une connexion à une route FastAPI, puis la ferme.

    FastAPI appelle cette fonction avant la route. Le mot-clé ``yield`` remet
    temporairement la connexion à la route, puis le bloc ``with`` la ferme.

    Exemple de trajet :
        route GET /api/asofdates -> get_connection() -> PostgreSQL
    """

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise HTTPException(
            status_code=500,
            detail="DATABASE_URL n'est pas configurée sur le backend.",
        )

    try:
        # RealDictCursor rend les résultats lisibles : row["asofdate"] au lieu
        # de row[0]. Le context manager ferme correctement la transaction.
        with psycopg2.connect(
            database_url,
            cursor_factory=RealDictCursor,
            connect_timeout=10,
        ) as connection:
            yield connection
    except DatabaseError as error:
        # Le détail psycopg2 peut contenir des informations techniques. Il ne doit
        # pas être renvoyé au frontend.
        raise HTTPException(
            status_code=500,
            detail="Impossible de se connecter à la base de données.",
        ) from error
