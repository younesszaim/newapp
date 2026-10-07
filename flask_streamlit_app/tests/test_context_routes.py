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

    @patch("api.context_routes.list_versions")
    @patch("api.context_routes.database_connection")
    def test_versions_are_filtered_by_asofdate(
        self,
        database_connection: MagicMock,
        list_versions: MagicMock,
    ) -> None:
        connection = MagicMock()
        database_connection.return_value.__enter__.return_value = connection
        list_versions.return_value = ["2026-10-06T15:30:00"]

        response = self.client.get("/api/asofdates/2026-10-05/versions")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, ["2026-10-06T15:30:00"])
        list_versions.assert_called_once()
        self.assertEqual(list_versions.call_args.args[1].isoformat(), "2026-10-05")

    def test_invalid_asofdate_returns_400(self) -> None:
        response = self.client.get("/api/asofdates/not-a-date/versions")

        self.assertEqual(response.status_code, 400)
        self.assertIn("YYYY-MM-DD", response.json["error"])
