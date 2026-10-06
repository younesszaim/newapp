"""Schémas de réponse du résumé LCR."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    """Autorise des noms Python lisibles et des noms JSON en camelCase."""

    model_config = ConfigDict(populate_by_name=True)


class LcrSummaryRow(ApiModel):
    product_line: str = Field(alias="productLine")
    amount_0d: float = Field(alias="amount0d")
    amount_30d: float = Field(alias="amount30d")
    lcr_reglementaire: float = Field(alias="lcrReglementaire")
    lcr_gestion: float = Field(alias="lcrGestion")


class LcrSummaryTotal(ApiModel):
    amount_0d: float = Field(alias="amount0d")
    amount_30d: float = Field(alias="amount30d")
    lcr_reglementaire: float = Field(alias="lcrReglementaire")
    lcr_gestion: float = Field(alias="lcrGestion")


class ExistingAdjustment(ApiModel):
    adjustment_id: UUID = Field(alias="adjustmentId")
    bi_id: str = Field(alias="biId")
    ldp_impact_lcr_reglementaire: float = Field(alias="ldpImpactLcrReglementaire")
    ldp_impact_lcr_gestion: float = Field(alias="ldpImpactLcrGestion")
    created_at: datetime = Field(alias="createdAt")
    created_by: str = Field(alias="createdBy")


class LcrSummary(ApiModel):
    asofdate: date
    asofdateflow_version: datetime = Field(alias="asofdateflowVersion")
    rows: list[LcrSummaryRow]
    total: LcrSummaryTotal
    has_adjustment: bool = Field(alias="hasAdjustment")
    adjustment: ExistingAdjustment | None = None
