export interface LcrSummaryRow {
  productLine: string;
  amount0d: number;
  amount30d: number;
  lcrReglementaire: number;
  lcrGestion: number;
}

export interface LcrSummaryTotal {
  amount0d: number;
  amount30d: number;
  lcrReglementaire: number;
  lcrGestion: number;
}

export interface ExistingAdjustment {
  adjustmentId: string;
  biId: string;
  ldpImpactLcrReglementaire: number;
  ldpImpactLcrGestion: number;
  createdAt: string;
  createdBy: string;
}

export interface LcrSummary {
  asofdate: string;
  asofdateflowVersion: string;
  rows: LcrSummaryRow[];
  total: LcrSummaryTotal;
  hasAdjustment: boolean;
  adjustment: ExistingAdjustment | null;
}
