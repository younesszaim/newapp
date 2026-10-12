"""Exemples de configuration de la connexion et de l'application Flask."""

from unittest import TestCase
from unittest.mock import MagicMock, patch
from psycopg2 import DatabaseError

from api.app import create_app
from api.config import Settings
from api.database import database_connection
from api.errors import ConfigurationError


class DatabaseAndAppTest(TestCase):
    @patch("api.database.get_settings")
    def test_database_connection_requires_database_url(
        self, get_settings: MagicMock
    ) -> None:
        get_settings.return_value = Settings(database_url=None, _env_file=None)

        with self.assertRaisesRegex(ConfigurationError, "DATABASE_URL"):
            with database_connection():
                pass

    @patch("api.database.psycopg2.connect")
    @patch("api.database.get_settings")
    def test_database_connection_yields_psycopg_connection(
        self,
        get_settings: MagicMock,
        connect: MagicMock,
    ) -> None:
        get_settings.return_value = Settings(
            database_url="postgresql://example",
            database_connect_timeout=5,
            _env_file=None,
        )
        expected_connection = MagicMock()
        connect.return_value.__enter__.return_value = expected_connection

        with database_connection() as connection:
            self.assertIs(connection, expected_connection)

        connect.assert_called_once()
        self.assertEqual(connect.call_args.kwargs["connect_timeout"], 5)

    def test_settings_have_safe_local_defaults(self) -> None:
        settings = Settings(_env_file=None)

        self.assertEqual(settings.created_by, "local_user")
        self.assertEqual(settings.database_connect_timeout, 10)

    def test_create_app_registers_health_and_swagger(self) -> None:
        client = create_app().test_client()

        self.assertEqual(client.get("/api/health").json, {"status": "ok"})
        self.assertEqual(client.get("/apidocs/").status_code, 200)

    @patch("api.context_routes.database_connection", side_effect=ConfigurationError("missing"))
    def test_global_handler_returns_json_for_application_error(
        self, _connection: MagicMock
    ) -> None:
        response = create_app().test_client().get("/api/asofdates")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, {"error": "missing"})

    @patch(
        "api.context_routes.database_connection",
        side_effect=DatabaseError("sensitive database detail"),
    )
    def test_global_database_handler_hides_technical_detail(
        self, _connection: MagicMock
    ) -> None:
        response = create_app().test_client().get("/api/asofdates")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, {"error": "Une erreur PostgreSQL est survenue."})
        self.assertNotIn("sensitive", response.get_data(as_text=True))
