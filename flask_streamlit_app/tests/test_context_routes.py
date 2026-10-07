"""Tests du endpoint des dates sans connexion PostgreSQL réelle."""

from unittest import TestCase
from unittest.mock import MagicMock, patch

from api.app import create_app


class ContextRoutesTest(TestCase):
    def setUp(self) -> None:
        self.client = create_app().test_client()

    @patch("api.context_routes.list_asofdates")
    @patch("api.context_routes.database_connection")
    def test_asofdates_are_returned_as_json(
        self,
        database_connection: MagicMock,
        list_asofdates: MagicMock,
    ) -> None:
        database_connection.return_value.__enter__.return_value = MagicMock()
        list_asofdates.return_value = ["2026-10-05", "2026-10-04"]

        response = self.client.get("/api/asofdates")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, ["2026-10-05", "2026-10-04"])

    @patch("api.context_routes.database_connection", side_effect=RuntimeError)
    def test_missing_database_configuration_returns_500(
        self,
        _database_connection: MagicMock,
    ) -> None:
        response = self.client.get("/api/asofdates")

        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.json)
