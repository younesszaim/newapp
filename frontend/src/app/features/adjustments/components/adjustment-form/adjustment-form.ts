import { Component, EventEmitter, Output, signal } from '@angular/core';
import { AgGridAngular } from 'ag-grid-angular';
import {
  AllCommunityModule,
  CellClickedEvent,
  ColDef,
  GridApi,
  GridReadyEvent,
  ModuleRegistry,
  themeQuartz,
  ValueParserParams
} from 'ag-grid-community';

import { AdjustmentAmounts } from '../../../../core/models/adjustment.model';

ModuleRegistry.registerModules([AllCommunityModule]);

interface AdjustmentGridRow {
  id: number;
  ldpImpactLcrReglementaire: number | null;
  ldpImpactLcrGestion: number | null;
  impactLcrInflow: number | null;
  impactLcrOutflow: number | null;
  impactLcrAsset: number | null;
  impactLcrAssetCash: number | null;
}

@Component({
  selector: 'app-adjustment-form',
  standalone: true,
  imports: [AgGridAngular],
  templateUrl: './adjustment-form.html'
})
export class AdjustmentForm {
  @Output() preview = new EventEmitter<AdjustmentAmounts[]>();

  private nextId = 2;
  private gridApi: GridApi<AdjustmentGridRow> | null = null;
  readonly rows = signal<AdjustmentGridRow[]>([this.emptyRow(1)]);
  readonly maxRows = 100;
  readonly validationError = signal<string | null>(null);

  readonly theme = themeQuartz.withParams({
    accentColor: '#008C7A',
    borderColor: '#E2E8F0',
    fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif',
    headerBackgroundColor: '#F8FAFC',
    headerTextColor: '#475569',
    rowHoverColor: '#F1F7F6',
    wrapperBorder: false
  });

  readonly defaultColDef: ColDef<AdjustmentGridRow> = {
    editable: true,
    resizable: true,
    suppressMovable: true,
    minWidth: 155,
    flex: 1,
    type: 'numericColumn',
    valueParser: (params: ValueParserParams<AdjustmentGridRow>) =>
      this.parseAmount(params.newValue)
  };

  readonly columnDefs: ColDef<AdjustmentGridRow>[] = [
    this.requiredColumn('ldpImpactLcrReglementaire', 'LCR réglementaire *'),
    this.requiredColumn('ldpImpactLcrGestion', 'LCR gestion *'),
    this.optionalColumn('impactLcrInflow', 'Inflow · Optionnel'),
    this.optionalColumn('impactLcrOutflow', 'Outflow · Optionnel'),
    this.optionalColumn('impactLcrAsset', 'Asset · Optionnel'),
    this.optionalColumn('impactLcrAssetCash', 'Asset Cash · Optionnel'),
    {
      colId: 'actions',
      headerName: 'Action',
      editable: false,
      sortable: false,
      filter: false,
      width: 110,
      minWidth: 110,
      maxWidth: 110,
      flex: 0,
      cellRenderer: () => '<span class="text-red-600 font-semibold">Supprimer</span>'
    }
  ];

  onGridReady(event: GridReadyEvent<AdjustmentGridRow>): void {
    this.gridApi = event.api;
  }

  addRow(): void {
    if (this.rows().length >= this.maxRows) {
      return;
    }
    this.rows.update((rows) => [...rows, this.emptyRow(this.nextId++)]);
    this.validationError.set(null);
  }

  reset(): void {
    this.rows.set([this.emptyRow(this.nextId++)]);
    this.validationError.set(null);
  }

  handleCellClicked(event: CellClickedEvent<AdjustmentGridRow>): void {
    if (event.colDef.colId !== 'actions' || !event.data) {
      return;
    }
    this.rows.update((rows) =>
      rows.length === 1
        ? [this.emptyRow(this.nextId++)]
        : rows.filter((row) => row.id !== event.data?.id)
    );
    this.validationError.set(null);
  }

  submit(): void {
    this.gridApi?.stopEditing();
    const rows = this.rows();
    if (
      rows.some(
        (row) =>
          !Number.isFinite(row.ldpImpactLcrReglementaire) ||
          !Number.isFinite(row.ldpImpactLcrGestion)
      )
    ) {
      this.validationError.set('Renseignez les deux colonnes obligatoires sur chaque ligne.');
      this.gridApi?.redrawRows();
      return;
    }

    this.validationError.set(null);
    this.preview.emit(
      rows.map((row) => ({
        ldpImpactLcrReglementaire: row.ldpImpactLcrReglementaire as number,
        ldpImpactLcrGestion: row.ldpImpactLcrGestion as number,
        impactLcrInflow: row.impactLcrInflow ?? 0,
        impactLcrOutflow: row.impactLcrOutflow ?? 0,
        impactLcrAsset: row.impactLcrAsset ?? 0,
        impactLcrAssetCash: row.impactLcrAssetCash ?? 0
      }))
    );
  }

  private emptyRow(id: number): AdjustmentGridRow {
    return {
      id,
      ldpImpactLcrReglementaire: null,
      ldpImpactLcrGestion: null,
      impactLcrInflow: null,
      impactLcrOutflow: null,
      impactLcrAsset: null,
      impactLcrAssetCash: null
    };
  }

  private requiredColumn(
    field: keyof AdjustmentGridRow,
    headerName: string
  ): ColDef<AdjustmentGridRow> {
    return {
      field,
      headerName,
      headerClass: 'adjustment-required-header',
      cellClassRules: {
        'adjustment-invalid-cell': (params) => !Number.isFinite(params.value)
      }
    };
  }

  private optionalColumn(
    field: keyof AdjustmentGridRow,
    headerName: string
  ): ColDef<AdjustmentGridRow> {
    return { field, headerName, headerClass: 'adjustment-optional-header' };
  }

  private parseAmount(value: unknown): number | null {
    if (value === '' || value === null || value === undefined) {
      return null;
    }
    const parsed = Number(String(value).replace(',', '.'));
    return Number.isFinite(parsed) ? parsed : null;
  }
}
