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

export interface Adjustment extends AdjustmentAmounts {
  adjustmentId: string;
  biId: string;
  tradeNo: number;
  asofdate: string;
  asofdateflowVersion: string;
  createdAt: string;
  createdBy: string;
  status: 'ACTIVE' | 'DELETED';
}

export interface AdjustmentRegistryItem {
  adjustmentId: string;
  biId: string;
  tradeNo: number | null;
  asofdate: string;
  asofdateflowVersion: string;
  ldpImpactLcrReglementaire: number | null;
  ldpImpactLcrGestion: number | null;
  impactLcrInflow: number | null;
  impactLcrOutflow: number | null;
  impactLcrAsset: number | null;
  impactLcrAssetCash: number | null;
  createdAt: string;
  createdBy: string;
  status: 'ACTIVE' | 'DELETED';
  deletedAt: string | null;
  deletedBy: string | null;
}
