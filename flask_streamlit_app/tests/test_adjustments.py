"""Tests de validation et de création des ajustements."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from unittest import TestCase
from unittest.mock import MagicMock, patch
from pydantic import ValidationError

from api.adjustment_models import (
    AdjustmentAmounts,
    AdjustmentBatchRequest,
    AdjustmentCreationResponse,
    AdjustmentRegistryBlockResponse,
)
from api.adjustment_service import (
    _generate_trade_no,
    create_adjustment_block,
    delete_adjustment_block,
    get_adjustment_registry,
    get_latest_active_adjustment_before,
)
from api.app import create_app
from api.adjustment_records import (
    AdjustmentTradeRecord,
    RegistryBlockLockRecord,
    RegistryBlockRecord,
)
from api.errors import AdjustmentConflictError, AdjustmentNotFoundError


class AdjustmentTest(TestCase):
    def test_required_amounts_are_enforced(self) -> None:
        with self.assertRaises(ValidationError):
            AdjustmentAmounts.model_validate({"ldpImpactLcrReglementaire": 100})

    def test_batch_must_be_a_non_empty_list(self) -> None:
        for invalid_value in (None, {}, []):
            with self.subTest(value=invalid_value):
                with self.assertRaises(ValidationError):
                    AdjustmentBatchRequest.model_validate({
                        "asofdate": "2026-10-05",
                        "asofdateflowVersion": "2026-10-06T15:30:00",
                        "adjustments": invalid_value,
                    })

    def test_amounts_must_be_finite_numbers(self) -> None:
        for invalid_value in ("not-a-number", float("inf"), float("nan")):
            with self.subTest(value=invalid_value):
                with self.assertRaises(ValueError):
                    AdjustmentAmounts.model_validate({
                        "ldpImpactLcrReglementaire": invalid_value,
                        "ldpImpactLcrGestion": 100,
                    })

    def test_amount_model_converts_a_string_to_decimal(self) -> None:
        amounts = AdjustmentAmounts.model_validate({
            "ldpImpactLcrReglementaire": "12.5",
            "ldpImpactLcrGestion": "100",
        })

        self.assertEqual(amounts.lcr_reglementaire, Decimal("12.5"))

    @patch("api.adjustment_service.secrets.randbelow", side_effect=[9, 19])
    @patch("api.adjustment_service.trade_no_exists", side_effect=[True, False])
    def test_trade_number_is_retried_after_collision(
        self,
        trade_exists: MagicMock,
        _randbelow: MagicMock,
    ) -> None:
        result = _generate_trade_no(MagicMock())

        self.assertEqual(result, 20)
        self.assertEqual(trade_exists.call_count, 2)

    def test_optional_amounts_default_to_zero(self) -> None:
        amounts = AdjustmentAmounts.model_validate({
            "ldpImpactLcrReglementaire": 100,
            "ldpImpactLcrGestion": 200,
            "impactLcrInflow": None,
        })

        self.assertEqual(amounts.inflow, Decimal("0"))

    def test_unknown_json_field_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            AdjustmentAmounts.model_validate({
                "ldpImpactLcrReglementaire": 100,
                "ldpImpactLcrGestion": 200,
                "unexpectedField": 300,
            })

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
            AdjustmentBatchRequest.model_validate({
                "asofdate": "2026-10-05",
                "asofdateflowVersion": "2026-10-06T15:30:00",
                "adjustments": [
                {"ldpImpactLcrReglementaire": 100, "ldpImpactLcrGestion": 200},
                {"ldpImpactLcrReglementaire": 300, "ldpImpactLcrGestion": 400},
                ],
            }),
        )

        self.assertEqual(insert_trade.call_count, 2)
        insert_registry.assert_called_once()
        self.assertEqual(len(insert_registry.call_args.kwargs["bi_ids"]), 2)
        self.assertEqual(result.line_count, 2)

    @patch("api.adjustment_routes.create_adjustment_block")
    @patch("api.adjustment_routes.database_connection")
    def test_post_returns_created_block(
        self,
        database_connection: MagicMock,
        create_block: MagicMock,
    ) -> None:
        database_connection.return_value.__enter__.return_value = MagicMock()
        create_block.return_value = AdjustmentCreationResponse(
            adjustment_id=UUID("a2432f6a-2142-41de-a34b-6ec75625a346"),
            line_count=1,
        )
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
        list_blocks.return_value = [RegistryBlockRecord(
            adjustment_id=adjustment_id,
            asofdate=date(2026, 10, 5),
            version=datetime(2026, 10, 6, 15, 30),
            created_at=datetime(2026, 10, 8, 9, 0),
            created_by="local_user",
            status="ACTIVE",
            deleted_at=None,
            deleted_by=None,
            lines=(AdjustmentTradeRecord(
                bi_id="bi-id",
                trade_no=123,
                lcr_reglementaire=Decimal("100"),
                lcr_gestion=Decimal("200"),
                inflow=Decimal("0"),
                outflow=Decimal("0"),
                asset=Decimal("0"),
                asset_cash=Decimal("0"),
            ),),
        )]

        result = get_adjustment_registry(MagicMock())

        self.assertIsInstance(result[0], AdjustmentRegistryBlockResponse)
        self.assertEqual(result[0].adjustment_id, adjustment_id)
        self.assertEqual(result[0].lines[0].trade_no, 123)
        self.assertEqual(result[0].last_event_at, datetime(2026, 10, 8, 9, 0))
        self.assertEqual(result[0].lines[0].lcr_reglementaire, Decimal("100"))

        json_result = result[0].model_dump(mode="json", by_alias=True)
        self.assertEqual(json_result["lines"][0]["ldpImpactLcrReglementaire"], 100.0)

    @patch("api.adjustment_service.get_latest_active_registry_block_before")
    def test_latest_active_service_serializes_the_block(
        self,
        get_latest: MagicMock,
    ) -> None:
        get_latest.return_value = self._active_block_record()

        result = get_latest_active_adjustment_before(
            MagicMock(), date(2026, 10, 10)
        )

        self.assertIsInstance(result, AdjustmentRegistryBlockResponse)
        self.assertEqual(result.lines[0].trade_no, 123)

    @patch(
        "api.adjustment_service.get_latest_active_registry_block_before",
        return_value=None,
    )
    def test_latest_active_service_returns_none_when_unavailable(
        self,
        _get_latest: MagicMock,
    ) -> None:
        result = get_latest_active_adjustment_before(
            MagicMock(), date(2026, 10, 10)
        )

        self.assertIsNone(result)

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
        get_block.return_value = RegistryBlockLockRecord(
            adjustment_id=adjustment_id,
            status="ACTIVE",
            bi_ids=("bi-1", "bi-2"),
        )

        delete_adjustment_block(connection, adjustment_id)

        delete_trades.assert_called_once_with(connection, ["bi-1", "bi-2"])
        mark_deleted.assert_called_once_with(connection, adjustment_id, "local_user")

    @patch("api.adjustment_service.get_registry_block_for_update", return_value=None)
    def test_delete_rejects_unknown_adjustment(self, _get_block: MagicMock) -> None:
        with self.assertRaises(AdjustmentNotFoundError):
            delete_adjustment_block(MagicMock(), UUID(int=0))

    @patch("api.adjustment_service.get_registry_block_for_update")
    def test_delete_rejects_already_deleted_adjustment(
        self, get_block: MagicMock
    ) -> None:
        get_block.return_value = RegistryBlockLockRecord(
            adjustment_id=UUID(int=0),
            status="DELETED",
            bi_ids=(),
        )

        with self.assertRaisesRegex(AdjustmentConflictError, "déjà supprimé"):
            delete_adjustment_block(MagicMock(), UUID(int=0))

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

    def test_post_rejects_missing_required_amount(self) -> None:
        response = create_app().test_client().post(
            "/api/adjustments",
            json={
                "asofdate": "2026-10-05",
                "asofdateflowVersion": "2026-10-06T15:30:00",
                "adjustments": [{"ldpImpactLcrReglementaire": 100}],
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("ldpImpactLcrGestion", response.json["error"])

    @patch("api.adjustment_routes.get_adjustment_registry")
    @patch("api.adjustment_routes.database_connection")
    def test_get_route_returns_registry_blocks(
        self,
        database_connection: MagicMock,
        get_registry: MagicMock,
    ) -> None:
        database_connection.return_value.__enter__.return_value = MagicMock()
        get_registry.return_value = [AdjustmentRegistryBlockResponse(
            adjustment_id=UUID("a2432f6a-2142-41de-a34b-6ec75625a346"),
            asofdate=date(2026, 10, 5),
            version=datetime(2026, 10, 6, 15, 30),
            created_at=datetime(2026, 10, 8, 9, 0),
            created_by="local_user",
            status="ACTIVE",
            last_event_at=datetime(2026, 10, 8, 9, 0),
            lines=[],
        )]

        response = create_app().test_client().get("/api/adjustments")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json[0]["adjustmentId"],
            "a2432f6a-2142-41de-a34b-6ec75625a346",
        )

    @patch("api.adjustment_routes.get_latest_active_adjustment_before")
    @patch("api.adjustment_routes.database_connection")
    def test_latest_active_route_returns_the_block(
        self,
        database_connection: MagicMock,
        get_latest: MagicMock,
    ) -> None:
        database_connection.return_value.__enter__.return_value = MagicMock()
        get_latest.return_value = AdjustmentRegistryBlockResponse(
            adjustment_id=UUID("a2432f6a-2142-41de-a34b-6ec75625a346"),
            asofdate=date(2026, 10, 5),
            version=datetime(2026, 10, 6, 15, 30),
            created_at=datetime(2026, 10, 8, 9, 0),
            created_by="local_user",
            status="ACTIVE",
            last_event_at=datetime(2026, 10, 8, 9, 0),
            lines=[],
        )

        response = create_app().test_client().get(
            "/api/asofdates/2026-10-10/latest-active-adjustment"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["asofdate"], "2026-10-05")
        get_latest.assert_called_once_with(
            database_connection.return_value.__enter__.return_value,
            date(2026, 10, 10),
        )

    @patch(
        "api.adjustment_routes.get_latest_active_adjustment_before",
        return_value=None,
    )
    @patch("api.adjustment_routes.database_connection")
    def test_latest_active_route_returns_json_null_when_unavailable(
        self,
        database_connection: MagicMock,
        _get_latest: MagicMock,
    ) -> None:
        database_connection.return_value.__enter__.return_value = MagicMock()

        response = create_app().test_client().get(
            "/api/asofdates/2026-10-01/latest-active-adjustment"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json)

    def test_latest_active_route_rejects_invalid_date(self) -> None:
        response = create_app().test_client().get(
            "/api/asofdates/not-a-date/latest-active-adjustment"
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("YYYY-MM-DD", response.json["error"])

    def test_registry_model_rejects_unknown_status(self) -> None:
        with self.assertRaises(ValidationError):
            AdjustmentRegistryBlockResponse(
                adjustment_id=UUID(int=0),
                asofdate=date(2026, 10, 5),
                version=datetime(2026, 10, 6, 15, 30),
                created_at=datetime(2026, 10, 8, 9, 0),
                created_by="local_user",
                status="UNKNOWN",
                last_event_at=datetime(2026, 10, 8, 9, 0),
                lines=[],
            )

    def test_deleted_registry_model_requires_audit_and_no_lines(self) -> None:
        with self.assertRaisesRegex(ValidationError, "audit"):
            AdjustmentRegistryBlockResponse(
                adjustment_id=UUID(int=0),
                asofdate=date(2026, 10, 5),
                version=datetime(2026, 10, 6, 15, 30),
                created_at=datetime(2026, 10, 8, 9, 0),
                created_by="local_user",
                status="DELETED",
                last_event_at=datetime(2026, 10, 9, 10, 0),
                lines=[],
            )

    def test_delete_route_rejects_invalid_uuid(self) -> None:
        response = create_app().test_client().delete("/api/adjustments/not-an-uuid")

        self.assertEqual(response.status_code, 400)

    @staticmethod
    def _active_block_record() -> RegistryBlockRecord:
        return RegistryBlockRecord(
            adjustment_id=UUID("a2432f6a-2142-41de-a34b-6ec75625a346"),
            asofdate=date(2026, 10, 5),
            version=datetime(2026, 10, 6, 15, 30),
            created_at=datetime(2026, 10, 8, 9, 0),
            created_by="local_user",
            status="ACTIVE",
            deleted_at=None,
            deleted_by=None,
            lines=(AdjustmentTradeRecord(
                bi_id="bi-id",
                trade_no=123,
                lcr_reglementaire=Decimal("100"),
                lcr_gestion=Decimal("200"),
                inflow=Decimal("0"),
                outflow=Decimal("0"),
                asset=Decimal("0"),
                asset_cash=Decimal("0"),
            ),),
        )
