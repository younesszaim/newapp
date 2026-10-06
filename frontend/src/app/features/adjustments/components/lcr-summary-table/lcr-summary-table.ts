import { Component, Input } from '@angular/core';

import { LcrSummary } from '../../../../core/models/lcr-summary.model';
import { CompactEuroPipe } from '../../../../core/pipes/compact-euro.pipe';

@Component({
  selector: 'app-lcr-summary-table',
  imports: [CompactEuroPipe],
  templateUrl: './lcr-summary-table.html'
})
export class LcrSummaryTable {
  @Input({ required: true }) summary!: LcrSummary;

  preciseAmount(value: number): string {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  }
}
