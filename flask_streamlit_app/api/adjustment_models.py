"""Contrats Pydantic de création et de registre des ajustements."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Self
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)


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


class AdjustmentLineResponse(ApiModel):
    """Deal fictif actif relu depuis completude_table."""

    bi_id: str = Field(alias="biId")
    trade_no: int = Field(alias="tradeNo")
    lcr_reglementaire: Decimal = Field(alias="ldpImpactLcrReglementaire")
    lcr_gestion: Decimal = Field(alias="ldpImpactLcrGestion")
    inflow: Decimal = Field(alias="impactLcrInflow")
    outflow: Decimal = Field(alias="impactLcrOutflow")
    asset: Decimal = Field(alias="impactLcrAsset")
    asset_cash: Decimal = Field(alias="impactLcrAssetCash")

    @field_serializer(
        "lcr_reglementaire",
        "lcr_gestion",
        "inflow",
        "outflow",
        "asset",
        "asset_cash",
        when_used="json",
    )
    def serialize_amount(self, value: Decimal) -> float:
        """Conserve Decimal en Python et un nombre JSON pour le frontend."""

        return float(value)


class AdjustmentRegistryBlockResponse(ApiModel):
    """Bloc d'historique actif ou supprimé affiché dans le registre."""

    adjustment_id: UUID = Field(alias="adjustmentId")
    asofdate: date
    version: datetime = Field(alias="asofdateflowVersion")
    created_at: datetime = Field(alias="createdAt")
    created_by: str = Field(alias="createdBy")
    status: Literal["ACTIVE", "DELETED"]
    deleted_at: datetime | None = Field(default=None, alias="deletedAt")
    deleted_by: str | None = Field(default=None, alias="deletedBy")
    last_event_at: datetime = Field(alias="lastEventAt")
    lines: list[AdjustmentLineResponse]

    @model_validator(mode="after")
    def validate_status_consistency(self) -> Self:
        """Garantit la cohérence entre statut, audit et lignes actives."""

        if self.status == "ACTIVE" and (self.deleted_at or self.deleted_by):
            raise ValueError("Un bloc actif ne peut pas avoir d'audit de suppression.")
        if self.status == "DELETED":
            if not self.deleted_at or not self.deleted_by:
                raise ValueError("Un bloc supprimé doit contenir son audit.")
            if self.lines:
                raise ValueError("Un bloc supprimé ne conserve aucune ligne.")
        return self
