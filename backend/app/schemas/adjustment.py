"""Contrats JSON de création d'un ajustement."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AdjustmentRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    asofdate: date
    asofdateflow_version: datetime = Field(alias="asofdateflowVersion")
    ldp_impact_lcr_reglementaire: Decimal = Field(alias="ldpImpactLcrReglementaire")
    ldp_impact_lcr_gestion: Decimal = Field(alias="ldpImpactLcrGestion")
    impact_lcr_inflow: Decimal = Field(default=Decimal("0"), alias="impactLcrInflow")
    impact_lcr_outflow: Decimal = Field(default=Decimal("0"), alias="impactLcrOutflow")
    impact_lcr_asset: Decimal = Field(default=Decimal("0"), alias="impactLcrAsset")
    impact_lcr_asset_cash: Decimal = Field(default=Decimal("0"), alias="impactLcrAssetCash")


class AdjustmentResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    adjustment_id: UUID = Field(alias="adjustmentId")
    bi_id: str = Field(alias="biId")
    trade_no: int = Field(alias="tradeNo")
    asofdate: date
    asofdateflow_version: datetime = Field(alias="asofdateflowVersion")
    ldp_impact_lcr_reglementaire: float = Field(alias="ldpImpactLcrReglementaire")
    ldp_impact_lcr_gestion: float = Field(alias="ldpImpactLcrGestion")
    impact_lcr_inflow: float = Field(alias="impactLcrInflow")
    impact_lcr_outflow: float = Field(alias="impactLcrOutflow")
    impact_lcr_asset: float = Field(alias="impactLcrAsset")
    impact_lcr_asset_cash: float = Field(alias="impactLcrAssetCash")
    created_at: datetime = Field(alias="createdAt")
    created_by: str = Field(alias="createdBy")
    status: str
