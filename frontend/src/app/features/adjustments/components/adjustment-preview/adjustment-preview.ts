import { Component, EventEmitter, Input, Output } from '@angular/core';

import { AdjustmentAmounts } from '../../../../core/models/adjustment.model';
import { LcrSummary } from '../../../../core/models/lcr-summary.model';
import { CompactEuroPipe } from '../../../../core/pipes/compact-euro.pipe';

@Component({
  selector: 'app-adjustment-preview',
  standalone: true,
  imports: [CompactEuroPipe],
  templateUrl: './adjustment-preview.html'
})
export class AdjustmentPreview {
  @Input({ required: true }) asofdate!: string;
  @Input({ required: true }) version!: string;
  @Input({ required: true }) summary!: LcrSummary;
  @Input({ required: true }) amounts!: AdjustmentAmounts;

  @Output() cancelled = new EventEmitter<void>();
  @Output() confirmed = new EventEmitter<void>();

  get projectedReglementaire(): number {
    return this.summary.total.lcrReglementaire + this.amounts.ldpImpactLcrReglementaire;
  }

  get projectedGestion(): number {
    return this.summary.total.lcrGestion + this.amounts.ldpImpactLcrGestion;
  }

  preciseAmount(value: number, showSign = false): string {
    const formatted = new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);

    return showSign && value > 0 ? `+${formatted}` : formatted;
  }
}
