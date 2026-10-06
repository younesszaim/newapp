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


class AdjustmentListItem(AdjustmentResponse):
    # Les anciens enregistrements créés avant l'ajout du snapshot peuvent ne
    # plus avoir de montants si leur trade a déjà été supprimé.
    trade_no: int | None = Field(default=None, alias="tradeNo")
    ldp_impact_lcr_reglementaire: float | None = Field(
        default=None,
        alias="ldpImpactLcrReglementaire",
    )
    ldp_impact_lcr_gestion: float | None = Field(
        default=None,
        alias="ldpImpactLcrGestion",
    )
    impact_lcr_inflow: float | None = Field(default=None, alias="impactLcrInflow")
    impact_lcr_outflow: float | None = Field(default=None, alias="impactLcrOutflow")
    impact_lcr_asset: float | None = Field(default=None, alias="impactLcrAsset")
    impact_lcr_asset_cash: float | None = Field(default=None, alias="impactLcrAssetCash")
    deleted_at: datetime | None = Field(default=None, alias="deletedAt")
    deleted_by: str | None = Field(default=None, alias="deletedBy")
