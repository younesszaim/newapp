export interface AdjustmentAmounts {
  ldpImpactLcrReglementaire: number;
  ldpImpactLcrGestion: number;
  impactLcrInflow: number;
  impactLcrOutflow: number;
  impactLcrAsset: number;
  impactLcrAssetCash: number;
}

export interface AdjustmentBatchRequest {
  asofdate: string;
  asofdateflowVersion: string;
  adjustments: AdjustmentAmounts[];
}

export interface AdjustmentLine extends AdjustmentAmounts {
  biId: string;
  tradeNo: number;
}

export interface AdjustmentRegistryItem {
  adjustmentId: string;
  asofdate: string;
  asofdateflowVersion: string;
  createdAt: string;
  createdBy: string;
  status: 'ACTIVE' | 'DELETED';
  deletedAt: string | null;
  deletedBy: string | null;
  lines: AdjustmentLine[];
}
