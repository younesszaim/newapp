import { Component, Input } from '@angular/core';
import { AgGridAngular } from 'ag-grid-angular';
import {
  AllCommunityModule,
  ColDef,
  ModuleRegistry,
  RowClassParams,
  themeQuartz,
  ValueFormatterParams
} from 'ag-grid-community';

import { LcrSummary, LcrSummaryRow } from '../../../../core/models/lcr-summary.model';
import { CompactEuroPipe } from '../../../../core/pipes/compact-euro.pipe';

// Enregistre uniquement les fonctionnalités gratuites de l'édition Community.
ModuleRegistry.registerModules([AllCommunityModule]);

@Component({
  selector: 'app-lcr-summary-table',
  imports: [AgGridAngular],
  templateUrl: './lcr-summary-table.html'
})
export class LcrSummaryTable {
  @Input({ required: true }) summary!: LcrSummary;

  private readonly compactEuro = new CompactEuroPipe();

  readonly theme = themeQuartz.withParams({
    accentColor: '#008C7A',
    borderColor: '#E2E8F0',
    borderRadius: 0,
    fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif',
    foregroundColor: '#334155',
    headerBackgroundColor: '#F8FAFC',
    headerTextColor: '#64748B',
    rowHoverColor: '#F1F7F6',
    wrapperBorder: false,
    wrapperBorderRadius: 0
  });

  readonly defaultColDef: ColDef<LcrSummaryRow> = {
    sortable: true,
    resizable: true,
    suppressMovable: true
  };

  readonly columnDefs: ColDef<LcrSummaryRow>[] = [
    {
      field: 'productLine',
      headerName: 'Product Line',
      flex: 1.3,
      minWidth: 180,
      cellStyle: { fontWeight: '600', color: '#0F172A' }
    },
    this.moneyColumn('amount0d', '0D'),
    this.moneyColumn('amount30d', '30D'),
    this.moneyColumn('lcrReglementaire', 'LCR Réglementaire'),
    this.moneyColumn('lcrGestion', 'LCR Gestion')
  ];

  get pinnedBottomRowData(): LcrSummaryRow[] {
    return [{ productLine: 'TOTAL', ...this.summary.total }];
  }

  readonly getRowStyle = (params: RowClassParams<LcrSummaryRow>) =>
    params.node.rowPinned
      ? {
          backgroundColor: '#EAF6F3',
          color: '#18324A',
          fontWeight: '700',
          borderTop: '2px solid #008C7A'
        }
      : undefined;

  private moneyColumn(
    field: keyof Omit<LcrSummaryRow, 'productLine'>,
    headerName: string
  ): ColDef<LcrSummaryRow> {
    return {
      field,
      headerName,
      flex: 1,
      minWidth: 155,
      type: 'numericColumn',
      valueFormatter: (params: ValueFormatterParams<LcrSummaryRow, number>) =>
        this.compactEuro.transform(params.value ?? 0),
      tooltipValueGetter: (params) => this.preciseAmount(Number(params.value ?? 0))
    };
  }

  private preciseAmount(value: number): string {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  }
}
