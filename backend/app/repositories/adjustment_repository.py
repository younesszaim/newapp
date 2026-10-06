"""SQL explicite de création et de suivi des ajustements."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from psycopg2.extensions import connection as PostgreSQLConnection


def adjustment_exists(
    connection: PostgreSQLConnection,
    asofdate: date,
    version: datetime,
) -> bool:
    query = """
        SELECT 1
        FROM public.adjustment_registry
        WHERE asofdate = %s
          AND asofdateflow_version = %s
          AND status = 'ACTIVE'
        LIMIT 1
    """
    with connection.cursor() as cursor:
        cursor.execute(query, (asofdate, version))
        return cursor.fetchone() is not None


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
    lcr_reglementaire: Decimal,
    lcr_gestion: Decimal,
    impact_inflow: Decimal,
    impact_outflow: Decimal,
    impact_asset: Decimal,
    impact_asset_cash: Decimal,
) -> None:
    """Insère une ligne fictive complète dans completude_table."""

    query = """
        INSERT INTO public.completude_table (
            bi_id,
            tradeno,
            cdr,
            target_instrument_type,
            product_line,
            business_line,
            fosystem,
            leg_type,
            reporting_entity_code,
            cpy_exposure_class,
            issuer_exposure_class,
            cash_amount_eur,
            security_amount_eur,
            eur_amount_od,
            eur_amount_30d,
            impact_lcr_inflow,
            impact_lcr_outflow,
            impact_lcr_asset,
            impact_lcr_asset_cash,
            ldp_impact_lcr_reglementaire,
            ldp_impact_lcr_gestion,
            asofdate,
            asofdateflow_version,
            able_conso_perimetre
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            0, 0, 0, 0,
            %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """
    values = (
        bi_id,
        trade_no,
        defaults["cdr"],
        defaults["target_instrument_type"],
        defaults["product_line"],
        defaults["business_line"],
        defaults["fosystem"],
        defaults["leg_type"],
        defaults["reporting_entity_code"],
        defaults["cpy_exposure_class"],
        defaults["issuer_exposure_class"],
        impact_inflow,
        impact_outflow,
        impact_asset,
        impact_asset_cash,
        lcr_reglementaire,
        lcr_gestion,
        asofdate,
        version,
        defaults["able_conso_perimetre"],
    )
    with connection.cursor() as cursor:
        cursor.execute(query, values)


def insert_registry_entry(
    connection: PostgreSQLConnection,
    *,
    adjustment_id: UUID,
    bi_id: str,
    asofdate: date,
    version: datetime,
    created_by: str,
    trade_no: int,
    lcr_reglementaire: Decimal,
    lcr_gestion: Decimal,
    impact_inflow: Decimal,
    impact_outflow: Decimal,
    impact_asset: Decimal,
    impact_asset_cash: Decimal,
) -> dict[str, Any]:
    query = """
        INSERT INTO public.adjustment_registry (
            adjustment_id,
            bi_id,
            asofdate,
            asofdateflow_version,
            created_by,
            status,
            tradeno,
            ldp_impact_lcr_reglementaire,
            ldp_impact_lcr_gestion,
            impact_lcr_inflow,
            impact_lcr_outflow,
            impact_lcr_asset,
            impact_lcr_asset_cash
        ) VALUES (%s, %s, %s, %s, %s, 'ACTIVE', %s, %s, %s, %s, %s, %s, %s)
        RETURNING created_at, created_by, status
    """
    with connection.cursor() as cursor:
        cursor.execute(
            query,
            (
                str(adjustment_id),
                bi_id,
                asofdate,
                version,
                created_by,
                trade_no,
                lcr_reglementaire,
                lcr_gestion,
                impact_inflow,
                impact_outflow,
                impact_asset,
                impact_asset_cash,
            ),
        )
        return dict(cursor.fetchone())


def list_adjustments(connection: PostgreSQLConnection) -> list[dict[str, Any]]:
    """Liste le registre, y compris les ajustements supprimés."""

    query = """
        SELECT
            registry.adjustment_id,
            registry.bi_id,
            COALESCE(registry.tradeno, trade.tradeno) AS trade_no,
            registry.asofdate,
            registry.asofdateflow_version,
            COALESCE(
                registry.ldp_impact_lcr_reglementaire,
                trade.ldp_impact_lcr_reglementaire
            ) AS ldp_impact_lcr_reglementaire,
            COALESCE(
                registry.ldp_impact_lcr_gestion,
                trade.ldp_impact_lcr_gestion
            ) AS ldp_impact_lcr_gestion,
            COALESCE(registry.impact_lcr_inflow, trade.impact_lcr_inflow)
                AS impact_lcr_inflow,
            COALESCE(registry.impact_lcr_outflow, trade.impact_lcr_outflow)
                AS impact_lcr_outflow,
            COALESCE(registry.impact_lcr_asset, trade.impact_lcr_asset)
                AS impact_lcr_asset,
            COALESCE(registry.impact_lcr_asset_cash, trade.impact_lcr_asset_cash)
                AS impact_lcr_asset_cash,
            registry.created_at,
            registry.created_by,
            registry.status,
            registry.deleted_at,
            registry.deleted_by
        FROM public.adjustment_registry AS registry
        LEFT JOIN public.completude_table AS trade
          ON trade.bi_id = registry.bi_id
        ORDER BY registry.created_at DESC
    """
    with connection.cursor() as cursor:
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]
