import { Component, Input } from '@angular/core';
import { AgGridAngular } from 'ag-grid-angular';
import {
  AllCommunityModule,
  ColDef,
  ModuleRegistry,
  themeQuartz,
  ValueFormatterParams
} from 'ag-grid-community';

import { LcrSummary, LcrSummaryRow } from '../../../../core/models/lcr-summary.model';
import { CompactEuroPipe } from '../../../../core/pipes/compact-euro.pipe';

// Enregistre uniquement les fonctionnalités gratuites de l'édition Community.
ModuleRegistry.registerModules([AllCommunityModule]);

@Component({
  selector: 'app-lcr-summary-table',
  standalone: true,
  imports: [AgGridAngular, CompactEuroPipe],
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
