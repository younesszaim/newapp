"""Exemples de configuration de la connexion et de l'application Flask."""

from unittest import TestCase
from unittest.mock import MagicMock, patch

from api.app import create_app
from api.database import database_connection


class DatabaseAndAppTest(TestCase):
    @patch("api.database.os.getenv", return_value=None)
    def test_database_connection_requires_database_url(self, _getenv: MagicMock) -> None:
        with self.assertRaisesRegex(RuntimeError, "DATABASE_URL"):
            with database_connection():
                pass

    @patch("api.database.psycopg2.connect")
    @patch("api.database.os.getenv", return_value="postgresql://example")
    def test_database_connection_yields_psycopg_connection(
        self,
        _getenv: MagicMock,
        connect: MagicMock,
    ) -> None:
        expected_connection = MagicMock()
        connect.return_value.__enter__.return_value = expected_connection

        with database_connection() as connection:
            self.assertIs(connection, expected_connection)

        connect.assert_called_once()

    def test_create_app_registers_health_and_swagger(self) -> None:
        client = create_app().test_client()

        self.assertEqual(client.get("/api/health").json, {"status": "ok"})
        self.assertEqual(client.get("/apidocs/").status_code, 200)
