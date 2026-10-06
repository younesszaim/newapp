import { Component, EventEmitter, Input, Output } from '@angular/core';

import { AdjustmentRequest } from '../../../../core/models/adjustment.model';

@Component({
  selector: 'app-confirmation-dialog',
  standalone: true,
  templateUrl: './confirmation-dialog.html'
})
export class ConfirmationDialog {
  @Input({ required: true }) request!: AdjustmentRequest;
  @Input() saving = false;
  @Input() error: string | null = null;

  @Output() cancelled = new EventEmitter<void>();
  @Output() confirmed = new EventEmitter<void>();

  formatAmount(value: number): string {
    const formatted = new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
    return value > 0 ? `+${formatted}` : formatted;
  }
}
