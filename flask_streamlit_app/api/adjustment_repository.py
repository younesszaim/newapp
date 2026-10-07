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
