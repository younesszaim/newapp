"""Connexion PostgreSQL partagée par les routes Flask."""

from contextlib import contextmanager
from collections.abc import Iterator

import psycopg2
from psycopg2.extensions import connection as PostgreSQLConnection
from psycopg2.extras import RealDictCursor

from api.config import get_settings
from api.errors import ConfigurationError


@contextmanager
def database_connection() -> Iterator[PostgreSQLConnection]:
    """Ouvre une connexion, puis commit ou rollback automatiquement.

    Exemple :
        with database_connection() as connection:
            cursor = connection.cursor()
    """

    settings = get_settings()
    if not settings.database_url:
        raise ConfigurationError("DATABASE_URL n'est pas configurée dans .env.")

    with psycopg2.connect(
        settings.database_url,
        cursor_factory=RealDictCursor,
        connect_timeout=settings.database_connect_timeout,
    ) as connection:
        yield connection
