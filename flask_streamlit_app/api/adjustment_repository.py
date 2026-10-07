"""Insertions SQL des ajustements manuels."""

from datetime import date, datetime
from typing import Any
from uuid import UUID

from psycopg2.extensions import connection as PostgreSQLConnection


def trade_no_exists(connection: PostgreSQLConnection, trade_no: int) -> bool:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM public.completude_table WHERE tradeno = %s LIMIT 1",
            (trade_no,),
        )
        return cursor.fetchone() is not None


def insert_adjustment_trade(
    connection: PostgreSQLConnection,
    *,
    bi_id: str,
    trade_no: int,
    asofdate: date,
    version: datetime,
    defaults: dict[str, Any],
    amounts: dict[str, float],
) -> None:
    """Insère une ligne fictive dans completude_table."""

    query = """
        INSERT INTO public.completude_table (
            bi_id, tradeno, cdr, target_instrument_type, product_line,
            business_line, fosystem, leg_type, reporting_entity_code,
            cpy_exposure_class, issuer_exposure_class, cash_amount_eur,
            security_amount_eur, eur_amount_od, eur_amount_30d,
            impact_lcr_inflow, impact_lcr_outflow, impact_lcr_asset,
            impact_lcr_asset_cash, ldp_impact_lcr_reglementaire,
            ldp_impact_lcr_gestion, asofdate, asofdateflow_version,
            able_conso_perimetre
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            0, 0, 0, 0, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """
    values = (
        bi_id, trade_no, defaults["cdr"], defaults["target_instrument_type"],
        defaults["product_line"], defaults["business_line"], defaults["fosystem"],
        defaults["leg_type"], defaults["reporting_entity_code"],
        defaults["cpy_exposure_class"], defaults["issuer_exposure_class"],
        amounts["impactLcrInflow"], amounts["impactLcrOutflow"],
        amounts["impactLcrAsset"], amounts["impactLcrAssetCash"],
        amounts["ldpImpactLcrReglementaire"], amounts["ldpImpactLcrGestion"],
        asofdate, version, defaults["able_conso_perimetre"],
    )
    with connection.cursor() as cursor:
        cursor.execute(query, values)


def insert_registry_block(
    connection: PostgreSQLConnection,
    *,
    adjustment_id: UUID,
    bi_ids: list[str],
    asofdate: date,
    version: datetime,
    created_by: str,
) -> None:
    """Lie toutes les lignes à un seul adjustment_id."""

    with connection.cursor() as cursor:
        cursor.execute(
            """INSERT INTO public.adjustment_registry (
                   adjustment_id, bi_ids, asofdate, asofdateflow_version,
                   created_by, status
               ) VALUES (%s, %s, %s, %s, %s, 'ACTIVE')""",
            (str(adjustment_id), bi_ids, asofdate, version, created_by),
        )


def list_registry_blocks(connection: PostgreSQLConnection) -> list[dict[str, Any]]:
    """Retourne les blocs et relit leurs lignes actives dans completude_table."""

    with connection.cursor() as cursor:
        cursor.execute(
            """SELECT adjustment_id, asofdate, asofdateflow_version, created_at,
                      created_by, status, deleted_at, deleted_by, bi_ids
               FROM public.adjustment_registry
               ORDER BY COALESCE(deleted_at, created_at) DESC"""
        )
        blocks = [dict(row) for row in cursor.fetchall()]

    active_bi_ids = [bi_id for block in blocks for bi_id in block["bi_ids"]]
    lines_by_bi_id = {}
    if active_bi_ids:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT bi_id, tradeno,
                          ldp_impact_lcr_reglementaire,
                          ldp_impact_lcr_gestion,
                          impact_lcr_inflow, impact_lcr_outflow,
                          impact_lcr_asset, impact_lcr_asset_cash
                   FROM public.completude_table
                   WHERE bi_id = ANY(%s)""",
                (active_bi_ids,),
            )
            lines_by_bi_id = {row["bi_id"]: dict(row) for row in cursor.fetchall()}

    for block in blocks:
        block["lines"] = [
            lines_by_bi_id[bi_id]
            for bi_id in block.pop("bi_ids")
            if bi_id in lines_by_bi_id
        ]
    return blocks


def get_registry_block_for_update(
    connection: PostgreSQLConnection,
    adjustment_id: UUID,
) -> dict[str, Any] | None:
    """Verrouille un bloc pendant sa suppression."""

    with connection.cursor() as cursor:
        cursor.execute(
            """SELECT adjustment_id, bi_ids, status
               FROM public.adjustment_registry
               WHERE adjustment_id = %s
               FOR UPDATE""",
            (str(adjustment_id),),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def delete_adjustment_trades(
    connection: PostgreSQLConnection,
    bi_ids: list[str],
) -> int:
    """Supprime physiquement toutes les lignes du bloc."""

    with connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM public.completude_table WHERE bi_id = ANY(%s)",
            (bi_ids,),
        )
        return cursor.rowcount


def mark_registry_block_deleted(
    connection: PostgreSQLConnection,
    adjustment_id: UUID,
    deleted_by: str,
) -> None:
    """Conserve uniquement l'audit du bloc après suppression."""

    with connection.cursor() as cursor:
        cursor.execute(
            """UPDATE public.adjustment_registry
               SET status = 'DELETED', deleted_at = CURRENT_TIMESTAMP,
                   deleted_by = %s, bi_ids = ARRAY[]::VARCHAR(36)[]
               WHERE adjustment_id = %s""",
            (deleted_by, str(adjustment_id)),
        )
