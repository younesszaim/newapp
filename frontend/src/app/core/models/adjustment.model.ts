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

export interface Adjustment extends AdjustmentRequest {
  adjustmentId: string;
  biId: string;
  tradeNo: number;
  createdAt: string;
  createdBy: string;
  status: 'ACTIVE' | 'DELETED';
}
