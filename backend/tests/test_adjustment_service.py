"""Tests du cycle de vie d'un ajustement, sans connexion PostgreSQL réelle."""

from datetime import date, datetime
from decimal import Decimal
from unittest import TestCase
from unittest.mock import MagicMock, patch
from uuid import UUID

from fastapi import HTTPException

from app.schemas.adjustment import AdjustmentRequest
from app.services.adjustment_service import create_adjustment, delete_adjustment


class AdjustmentServiceTest(TestCase):
    """Les repositories sont simulés pour ne jamais modifier Supabase."""

    def setUp(self) -> None:
        self.connection = MagicMock(name="postgresql_connection")
        self.request = AdjustmentRequest(
            asofdate=date(2026, 10, 4),
            asofdateflowVersion=datetime(2026, 10, 5, 10, 30),
            ldpImpactLcrReglementaire=Decimal("5000000"),
            ldpImpactLcrGestion=Decimal("0"),
            impactLcrInflow=Decimal("0"),
            impactLcrOutflow=Decimal("0"),
            impactLcrAsset=Decimal("0"),
            impactLcrAssetCash=Decimal("0"),
        )

    @patch("app.services.adjustment_service.insert_registry_entry")
    @patch("app.services.adjustment_service.insert_adjustment_trade")
    @patch("app.services.adjustment_service.generate_trade_no", return_value=123456)
    @patch("app.services.adjustment_service.adjustment_exists", return_value=False)
    def test_create_adjustment_inserts_trade_then_registry(
        self,
        _exists: MagicMock,
        _trade_no: MagicMock,
        insert_trade: MagicMock,
        insert_registry: MagicMock,
    ) -> None:
        insert_registry.return_value = {
            "created_at": datetime(2026, 10, 7, 9, 0),
            "created_by": "local_user",
            "status": "ACTIVE",
        }

        result = create_adjustment(self.connection, self.request)

        self.assertEqual(result.trade_no, 123456)
        self.assertEqual(result.status, "ACTIVE")
        self.assertEqual(result.ldp_impact_lcr_reglementaire, 5_000_000)
        insert_trade.assert_called_once()
        insert_registry.assert_called_once()
        self.assertEqual(
            insert_trade.call_args.kwargs["bi_id"],
            insert_registry.call_args.kwargs["bi_id"],
        )

    @patch("app.services.adjustment_service.adjustment_exists", return_value=True)
    def test_create_adjustment_rejects_an_active_duplicate(
        self,
        _exists: MagicMock,
    ) -> None:
        with self.assertRaises(HTTPException) as context:
            create_adjustment(self.connection, self.request)

        self.assertEqual(context.exception.status_code, 409)

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

