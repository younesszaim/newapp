"""Tests de validation et de création des ajustements."""

from datetime import date, datetime
from unittest import TestCase
from unittest.mock import MagicMock, patch

from api.adjustment_service import create_adjustment_block, validate_adjustment_lines
from api.app import create_app


class AdjustmentTest(TestCase):
    def test_required_amounts_are_enforced(self) -> None:
        with self.assertRaisesRegex(ValueError, "obligatoires"):
            validate_adjustment_lines([{"ldpImpactLcrReglementaire": 100}])

    def test_optional_amounts_default_to_zero(self) -> None:
        lines = validate_adjustment_lines([
            {"ldpImpactLcrReglementaire": 100, "ldpImpactLcrGestion": 200}
        ])

        self.assertEqual(lines[0]["impactLcrInflow"], 0)

    @patch("api.adjustment_service.insert_registry_block")
    @patch("api.adjustment_service.insert_adjustment_trade")
    @patch("api.adjustment_service._generate_trade_no", side_effect=[10, 11])
    def test_lines_share_one_registry_block(
        self,
        _trade_no: MagicMock,
        insert_trade: MagicMock,
        insert_registry: MagicMock,
    ) -> None:
        result = create_adjustment_block(
            MagicMock(),
            date(2026, 10, 5),
            datetime(2026, 10, 6, 15, 30),
            validate_adjustment_lines([
                {"ldpImpactLcrReglementaire": 100, "ldpImpactLcrGestion": 200},
                {"ldpImpactLcrReglementaire": 300, "ldpImpactLcrGestion": 400},
            ]),
        )

        self.assertEqual(insert_trade.call_count, 2)
        insert_registry.assert_called_once()
        self.assertEqual(len(insert_registry.call_args.kwargs["bi_ids"]), 2)
        self.assertEqual(result["lineCount"], 2)

    @patch("api.adjustment_routes.create_adjustment_block")
    @patch("api.adjustment_routes.database_connection")
    def test_post_returns_created_block(
        self,
        database_connection: MagicMock,
        create_block: MagicMock,
    ) -> None:
        database_connection.return_value.__enter__.return_value = MagicMock()
        create_block.return_value = {
            "adjustmentId": "test-id", "lineCount": 1, "status": "ACTIVE"
        }
        response = create_app().test_client().post(
            "/api/adjustments",
            json={
                "asofdate": "2026-10-05",
                "asofdateflowVersion": "2026-10-06T15:30:00",
                "adjustments": [
                    {"ldpImpactLcrReglementaire": 100, "ldpImpactLcrGestion": 200}
                ],
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["lineCount"], 1)
