"""Tests du calcul et de la route du résumé LCR."""

from datetime import date, datetime
from decimal import Decimal
from unittest import TestCase
from unittest.mock import MagicMock, patch

from api.app import create_app
from api.lcr_service import build_lcr_summary


class LcrSummaryTest(TestCase):
    @patch("api.lcr_service.get_lcr_summary_rows")
    def test_service_calculates_totals(self, get_rows: MagicMock) -> None:
        get_rows.return_value = [
            {
                "product_line": "LOAN",
                "amount_0d": Decimal("100"),
                "amount_30d": Decimal("200"),
                "lcr_reglementaire": Decimal("300"),
                "lcr_gestion": Decimal("400"),
            },
            {
                "product_line": "BOND",
                "amount_0d": Decimal("10"),
                "amount_30d": Decimal("20"),
                "lcr_reglementaire": Decimal("30"),
                "lcr_gestion": Decimal("40"),
            },
        ]

        result = build_lcr_summary(
            MagicMock(), date(2026, 10, 5), datetime(2026, 10, 6, 15, 30)
        )

        self.assertEqual(result["total"]["amount0d"], 110)
        self.assertEqual(result["total"]["lcrGestion"], 440)

    def test_route_rejects_missing_parameters(self) -> None:
        response = create_app().test_client().get("/api/lcr-summary")

        self.assertEqual(response.status_code, 400)

    @patch("api.lcr_routes.build_lcr_summary")
    @patch("api.lcr_routes.database_connection")
    def test_route_returns_summary(
        self,
        database_connection: MagicMock,
        build_summary: MagicMock,
    ) -> None:
        database_connection.return_value.__enter__.return_value = MagicMock()
        build_summary.return_value = {"rows": [], "total": {}}

        response = create_app().test_client().get(
            "/api/lcr-summary",
            query_string={
                "asofdate": "2026-10-05",
                "version": "2026-10-06T15:30:00",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["rows"], [])
