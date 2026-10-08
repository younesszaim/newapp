"""Exemples unitaires de chaque requête du repository des ajustements."""

from datetime import date, datetime
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
        blocks_cursor = FakeCursor([{
            "adjustment_id": "adjustment-1",
            "bi_ids": ["bi-2", "bi-1"],
            "status": "ACTIVE",
        }])
        trades_cursor = FakeCursor([
            {"bi_id": "bi-1", "tradeno": 1},
            {"bi_id": "bi-2", "tradeno": 2},
        ])

        result = list_registry_blocks(
            FakeConnection(blocks_cursor, trades_cursor)
        )

        self.assertEqual(
            [line["bi_id"] for line in result[0]["lines"]],
            ["bi-2", "bi-1"],
        )
        self.assertEqual(trades_cursor.params, (["bi-2", "bi-1"],))

    def test_list_registry_blocks_skips_trade_query_when_all_are_deleted(self) -> None:
        blocks_cursor = FakeCursor([{
            "adjustment_id": "adjustment-1", "bi_ids": [], "status": "DELETED"
        }])

        result = list_registry_blocks(FakeConnection(blocks_cursor))

        self.assertEqual(result[0]["lines"], [])

    def test_get_registry_block_for_update_returns_first_row(self) -> None:
        adjustment_id = UUID("a2432f6a-2142-41de-a34b-6ec75625a346")
        cursor = FakeCursor([{"status": "ACTIVE", "bi_ids": ["bi-1"]}])

        result = get_registry_block_for_update(
            FakeConnection(cursor), adjustment_id
        )

        self.assertEqual(result["status"], "ACTIVE")
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
