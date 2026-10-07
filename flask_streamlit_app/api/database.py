"""Connexion PostgreSQL partagée par les routes Flask."""

import os
from contextlib import contextmanager
from collections.abc import Iterator

import psycopg2
from dotenv import load_dotenv
from psycopg2.extensions import connection as PostgreSQLConnection
from psycopg2.extras import RealDictCursor

load_dotenv()


@contextmanager
def database_connection() -> Iterator[PostgreSQLConnection]:
    """Ouvre une connexion, puis commit ou rollback automatiquement.

    Exemple :
        with database_connection() as connection:
            cursor = connection.cursor()
    """

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL n'est pas configurée dans .env.")

    with psycopg2.connect(
        database_url,
        cursor_factory=RealDictCursor,
        connect_timeout=10,
    ) as connection:
        yield connection
