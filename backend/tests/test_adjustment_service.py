"""Tests du cycle de vie d'un ajustement, sans connexion PostgreSQL réelle."""

from datetime import date, datetime
from decimal import Decimal
from unittest import TestCase
from unittest.mock import MagicMock, patch
from uuid import UUID

from fastapi import HTTPException

from app.schemas.adjustment import AdjustmentBatchRequest
from app.services.adjustment_service import create_adjustments, delete_adjustment


class AdjustmentServiceTest(TestCase):
    """Les repositories sont simulés pour ne jamais modifier Supabase."""

    def setUp(self) -> None:
        self.connection = MagicMock(name="postgresql_connection")
        self.request = AdjustmentBatchRequest(
            asofdate=date(2026, 10, 4),
            asofdateflowVersion=datetime(2026, 10, 5, 10, 30),
            adjustments=[
                {
                    "ldpImpactLcrReglementaire": Decimal("5000000"),
                    "ldpImpactLcrGestion": Decimal("0"),
                },
                {
                    "ldpImpactLcrReglementaire": Decimal("1000000"),
                    "ldpImpactLcrGestion": Decimal("250000"),
                },
            ],
        )

    @patch("app.services.adjustment_service.insert_registry_entry")
    @patch("app.services.adjustment_service.insert_adjustment_trade")
    @patch(
        "app.services.adjustment_service.generate_trade_no",
        side_effect=[123456, 123457],
    )
    def test_create_adjustments_inserts_each_trade_and_registry(
        self,
        _trade_no: MagicMock,
        insert_trade: MagicMock,
        insert_registry: MagicMock,
    ) -> None:
        insert_registry.return_value = {
            "created_at": datetime(2026, 10, 7, 9, 0),
            "created_by": "local_user",
            "status": "ACTIVE",
        }

        result = create_adjustments(self.connection, self.request)

        self.assertEqual([item.trade_no for item in result], [123456, 123457])
        self.assertTrue(all(item.status == "ACTIVE" for item in result))
        self.assertEqual(insert_trade.call_count, 2)
        self.assertEqual(insert_registry.call_count, 2)
        for trade_call, registry_call in zip(
            insert_trade.call_args_list,
            insert_registry.call_args_list,
            strict=True,
        ):
            self.assertEqual(
                trade_call.kwargs["bi_id"],
                registry_call.kwargs["bi_id"],
            )

    def test_batch_requires_at_least_one_line(self) -> None:
        with self.assertRaises(ValueError):
            AdjustmentBatchRequest(
                asofdate=date(2026, 10, 4),
                asofdateflowVersion=datetime(2026, 10, 5, 10, 30),
                adjustments=[],
            )

    @patch("app.services.adjustment_service.mark_registry_entry_deleted")
    @patch("app.services.adjustment_service.delete_adjustment_trade", return_value=True)
    @patch("app.services.adjustment_service.get_registry_entry_for_update")
    def test_delete_adjustment_deletes_trade_then_preserves_audit(
        self,
        get_registry: MagicMock,
        delete_trade: MagicMock,
        mark_deleted: MagicMock,
    ) -> None:
        adjustment_id = UUID("a2432f6a-2142-41de-a34b-6ec75625a346")
        get_registry.return_value = {
            "adjustment_id": adjustment_id,
            "bi_id": "trade-bi-id",
            "status": "ACTIVE",
        }

        delete_adjustment(self.connection, adjustment_id)

        delete_trade.assert_called_once_with(self.connection, "trade-bi-id")
        mark_deleted.assert_called_once_with(
            self.connection,
            adjustment_id,
            "local_user",
        )

    @patch("app.services.adjustment_service.get_registry_entry_for_update", return_value=None)
    def test_delete_adjustment_rejects_an_unknown_id(
        self,
        _get_registry: MagicMock,
    ) -> None:
        with self.assertRaises(HTTPException) as context:
            delete_adjustment(self.connection, UUID(int=0))

        self.assertEqual(context.exception.status_code, 404)
