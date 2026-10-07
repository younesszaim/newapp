"""Tests de validation et de création des ajustements."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from unittest import TestCase
from unittest.mock import MagicMock, patch

from api.adjustment_service import (
    create_adjustment_block,
    delete_adjustment_block,
    get_adjustment_registry,
    validate_adjustment_lines,
)
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

    @patch("api.adjustment_service.list_registry_blocks")
    def test_registry_serializes_active_lines(self, list_blocks: MagicMock) -> None:
        adjustment_id = UUID("a2432f6a-2142-41de-a34b-6ec75625a346")
        list_blocks.return_value = [{
            "adjustment_id": adjustment_id,
            "asofdate": date(2026, 10, 5),
            "asofdateflow_version": datetime(2026, 10, 6, 15, 30),
            "created_at": datetime(2026, 10, 8, 9, 0),
            "created_by": "local_user",
            "status": "ACTIVE",
            "deleted_at": None,
            "deleted_by": None,
            "lines": [{
                "bi_id": "bi-id",
                "tradeno": 123,
                "ldp_impact_lcr_reglementaire": Decimal("100"),
                "ldp_impact_lcr_gestion": Decimal("200"),
                "impact_lcr_inflow": Decimal("0"),
                "impact_lcr_outflow": Decimal("0"),
                "impact_lcr_asset": Decimal("0"),
                "impact_lcr_asset_cash": Decimal("0"),
            }],
        }]

        result = get_adjustment_registry(MagicMock())

        self.assertEqual(result[0]["adjustmentId"], str(adjustment_id))
        self.assertEqual(result[0]["lines"][0]["tradeNo"], 123)
        self.assertEqual(result[0]["lastEventAt"], "2026-10-08T09:00:00")

    @patch("api.adjustment_service.mark_registry_block_deleted")
    @patch("api.adjustment_service.delete_adjustment_trades", return_value=2)
    @patch("api.adjustment_service.get_registry_block_for_update")
    def test_delete_removes_all_lines_and_marks_block(
        self,
        get_block: MagicMock,
        delete_trades: MagicMock,
        mark_deleted: MagicMock,
    ) -> None:
        adjustment_id = UUID("a2432f6a-2142-41de-a34b-6ec75625a346")
        connection = MagicMock()
        get_block.return_value = {
            "status": "ACTIVE", "bi_ids": ["bi-1", "bi-2"]
        }

        delete_adjustment_block(connection, adjustment_id)

        delete_trades.assert_called_once_with(connection, ["bi-1", "bi-2"])
        mark_deleted.assert_called_once_with(connection, adjustment_id, "local_user")

    @patch("api.adjustment_routes.delete_adjustment_block")
    @patch("api.adjustment_routes.database_connection")
    def test_delete_route_returns_204(
        self,
        database_connection: MagicMock,
        _delete_block: MagicMock,
    ) -> None:
        database_connection.return_value.__enter__.return_value = MagicMock()
        response = create_app().test_client().delete(
            "/api/adjustments/a2432f6a-2142-41de-a34b-6ec75625a346"
        )

        self.assertEqual(response.status_code, 204)
