"""Exemple unitaire de l'agrégation SQL LCR."""

from datetime import date, datetime
from decimal import Decimal
from unittest import TestCase

from api.lcr_repository import get_lcr_summary_rows
from tests.fakes import FakeConnection, FakeCursor


class LcrRepositoryTest(TestCase):
    def test_summary_groups_by_product_line_and_passes_context(self) -> None:
        selected_date = date(2026, 10, 5)
        version = datetime(2026, 10, 6, 15, 30)
        expected_row = {
            "product_line": "LOAN",
            "amount_0d": Decimal("100"),
            "amount_30d": Decimal("200"),
            "lcr_reglementaire": Decimal("300"),
            "lcr_gestion": Decimal("400"),
        }
        cursor = FakeCursor([expected_row])

        result = get_lcr_summary_rows(
            FakeConnection(cursor), selected_date, version
        )

        self.assertEqual(result, [expected_row])
        self.assertIn("GROUP BY product_line", cursor.query)
        self.assertEqual(cursor.params, (selected_date, version))
