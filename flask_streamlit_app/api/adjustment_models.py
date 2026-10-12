"""Contrats Pydantic de création des ajustements."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ApiModel(BaseModel):
    """Configuration commune aux contrats JSON de l'API."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )


class AdjustmentAmounts(ApiModel):
    """Montants d'un deal fictif saisi dans une ligne Streamlit."""

    lcr_reglementaire: Decimal = Field(
        alias="ldpImpactLcrReglementaire",
        allow_inf_nan=False,
    )
    lcr_gestion: Decimal = Field(
        alias="ldpImpactLcrGestion",
        allow_inf_nan=False,
    )
    inflow: Decimal = Field(
        default=Decimal("0"), alias="impactLcrInflow", allow_inf_nan=False
    )
    outflow: Decimal = Field(
        default=Decimal("0"), alias="impactLcrOutflow", allow_inf_nan=False
    )
    asset: Decimal = Field(
        default=Decimal("0"), alias="impactLcrAsset", allow_inf_nan=False
    )
    asset_cash: Decimal = Field(
        default=Decimal("0"), alias="impactLcrAssetCash", allow_inf_nan=False
    )

    @field_validator("inflow", "outflow", "asset", "asset_cash", mode="before")
    @classmethod
    def empty_optional_amount_is_zero(cls, value: object) -> object:
        """Interprète une cellule optionnelle vide comme 0 €."""

        return Decimal("0") if value in (None, "") else value


class AdjustmentBatchRequest(ApiModel):
    """Contexte commun et lignes d'un ajustement transactionnel."""

    asofdate: date
    version: datetime = Field(alias="asofdateflowVersion")
    adjustments: list[AdjustmentAmounts] = Field(min_length=1, max_length=100)


class AdjustmentCreationResponse(ApiModel):
    """Réponse minimale renvoyée après la création du bloc."""

    adjustment_id: UUID = Field(alias="adjustmentId")
    line_count: int = Field(alias="lineCount", ge=1)
    status: Literal["ACTIVE"] = "ACTIVE"
