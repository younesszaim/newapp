export interface AdjustmentAmounts {
  ldpImpactLcrReglementaire: number;
  ldpImpactLcrGestion: number;
  impactLcrInflow: number;
  impactLcrOutflow: number;
  impactLcrAsset: number;
  impactLcrAssetCash: number;
}

export interface AdjustmentRequest extends AdjustmentAmounts {
  asofdate: string;
  asofdateflowVersion: string;
}
