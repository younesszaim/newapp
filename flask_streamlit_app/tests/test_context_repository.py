"""Exemples unitaires des requêtes de contexte."""

from datetime import date, datetime
from unittest import TestCase

from api.context_repository import list_asofdates, list_versions
from tests.fakes import FakeConnection, FakeCursor


class ContextRepositoryTest(TestCase):
    def test_list_asofdates_converts_dates_to_iso_strings(self) -> None:
        cursor = FakeCursor([{"asofdate": date(2026, 10, 5)}])

        result = list_asofdates(FakeConnection(cursor))

        self.assertEqual(result, ["2026-10-05"])
        self.assertIn("DISTINCT asofdate", cursor.query)

    def test_list_versions_uses_asofdate_as_sql_parameter(self) -> None:
        selected_date = date(2026, 10, 5)
        cursor = FakeCursor([
            {"asofdateflow_version": datetime(2026, 10, 6, 15, 30)}
        ])

        result = list_versions(FakeConnection(cursor), selected_date)

        self.assertEqual(result, ["2026-10-06T15:30:00"])
        self.assertEqual(cursor.params, (selected_date,))
