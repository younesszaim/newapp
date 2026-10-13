"""Exemples unitaires de chaque requête du repository des ajustements."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from unittest import TestCase

from api.adjustment_repository import (
    delete_adjustment_trades,
    get_registry_block_for_update,
    insert_adjustment_trade,
    insert_registry_block,
    list_registry_blocks,
    mark_registry_block_deleted,
    trade_no_exists,
)
from api.config import ADJUSTMENT_DEFAULTS
from api.adjustment_records import RegistryBlockLockRecord, RegistryBlockRecord
from tests.fakes import FakeConnection, FakeCursor


class AdjustmentRepositoryTest(TestCase):
    def test_trade_no_exists_returns_true_when_one_row_is_found(self) -> None:
        cursor = FakeCursor([{"exists": 1}])

        result = trade_no_exists(FakeConnection(cursor), 123)

        self.assertTrue(result)
        self.assertEqual(cursor.params, (123,))

    def test_insert_adjustment_trade_sends_generated_values(self) -> None:
        cursor = FakeCursor()
        amounts = {
            "ldpImpactLcrReglementaire": 100,
            "ldpImpactLcrGestion": 200,
            "impactLcrInflow": 10,
            "impactLcrOutflow": 20,
            "impactLcrAsset": 30,
            "impactLcrAssetCash": 40,
        }

        insert_adjustment_trade(
            FakeConnection(cursor),
            bi_id="bi-example",
            trade_no=123,
            asofdate=date(2026, 10, 5),
            version=datetime(2026, 10, 6, 15, 30),
            defaults=ADJUSTMENT_DEFAULTS,
            amounts=amounts,
        )

        self.assertIn("INSERT INTO public.completude_table", cursor.query)
        self.assertEqual(cursor.params[0:2], ("bi-example", 123))
        self.assertIn(100, cursor.params)

    def test_insert_registry_block_groups_bi_ids(self) -> None:
        cursor = FakeCursor()
        adjustment_id = UUID("a2432f6a-2142-41de-a34b-6ec75625a346")

        insert_registry_block(
            FakeConnection(cursor),
            adjustment_id=adjustment_id,
            bi_ids=["bi-1", "bi-2"],
            asofdate=date(2026, 10, 5),
            version=datetime(2026, 10, 6, 15, 30),
            created_by="local_user",
        )

        self.assertIn("INSERT INTO public.adjustment_registry", cursor.query)
        self.assertEqual(cursor.params[1], ["bi-1", "bi-2"])

    def test_list_registry_blocks_attaches_trades_by_bi_id(self) -> None:
        adjustment_id = UUID("a2432f6a-2142-41de-a34b-6ec75625a346")
        blocks_cursor = FakeCursor([{
            "adjustment_id": adjustment_id,
            "asofdate": date(2026, 10, 5),
            "asofdateflow_version": datetime(2026, 10, 6, 15, 30),
            "created_at": datetime(2026, 10, 8, 9, 0),
            "created_by": "local_user",
            "bi_ids": ["bi-2", "bi-1"],
            "status": "ACTIVE",
            "deleted_at": None,
            "deleted_by": None,
        }])
        trades_cursor = FakeCursor([
            self._trade_row("bi-1", 1),
            self._trade_row("bi-2", 2),
        ])

        result = list_registry_blocks(
            FakeConnection(blocks_cursor, trades_cursor)
        )

        self.assertIsInstance(result[0], RegistryBlockRecord)
        self.assertEqual([line.bi_id for line in result[0].lines], ["bi-2", "bi-1"])
        self.assertEqual(trades_cursor.params, (["bi-2", "bi-1"],))

    def test_list_registry_blocks_skips_trade_query_when_all_are_deleted(self) -> None:
        blocks_cursor = FakeCursor([{
            "adjustment_id": UUID("a2432f6a-2142-41de-a34b-6ec75625a346"),
            "asofdate": date(2026, 10, 5),
            "asofdateflow_version": datetime(2026, 10, 6, 15, 30),
            "created_at": datetime(2026, 10, 8, 9, 0),
            "created_by": "local_user",
            "bi_ids": [],
            "status": "DELETED",
            "deleted_at": datetime(2026, 10, 9, 10, 0),
            "deleted_by": "local_user",
        }])

        result = list_registry_blocks(FakeConnection(blocks_cursor))

        self.assertEqual(result[0].lines, ())

    def test_get_registry_block_for_update_returns_first_row(self) -> None:
        adjustment_id = UUID("a2432f6a-2142-41de-a34b-6ec75625a346")
        cursor = FakeCursor([{
            "adjustment_id": adjustment_id,
            "status": "ACTIVE",
            "bi_ids": ["bi-1"],
        }])

        result = get_registry_block_for_update(
            FakeConnection(cursor), adjustment_id
        )

        self.assertIsInstance(result, RegistryBlockLockRecord)
        self.assertEqual(result.status, "ACTIVE")
        self.assertEqual(result.bi_ids, ("bi-1",))
        self.assertIn("FOR UPDATE", cursor.query)
        self.assertEqual(cursor.params, (str(adjustment_id),))

    def test_delete_adjustment_trades_returns_deleted_row_count(self) -> None:
        cursor = FakeCursor(rowcount=2)

        result = delete_adjustment_trades(
            FakeConnection(cursor), ["bi-1", "bi-2"]
        )

        self.assertEqual(result, 2)
        self.assertEqual(cursor.params, (["bi-1", "bi-2"],))

    def test_mark_registry_block_deleted_clears_bi_ids(self) -> None:
        adjustment_id = UUID("a2432f6a-2142-41de-a34b-6ec75625a346")
        cursor = FakeCursor()

        mark_registry_block_deleted(
            FakeConnection(cursor), adjustment_id, "local_user"
        )

        self.assertIn("status = 'DELETED'", cursor.query)
        self.assertIn("bi_ids = ARRAY[]", cursor.query)
        self.assertEqual(cursor.params, ("local_user", str(adjustment_id)))

    @staticmethod
    def _trade_row(bi_id: str, trade_no: int) -> dict:
        return {
            "bi_id": bi_id,
            "tradeno": trade_no,
            "ldp_impact_lcr_reglementaire": Decimal("100"),
            "ldp_impact_lcr_gestion": Decimal("200"),
            "impact_lcr_inflow": Decimal("0"),
            "impact_lcr_outflow": Decimal("0"),
            "impact_lcr_asset": Decimal("0"),
            "impact_lcr_asset_cash": Decimal("0"),
        }
