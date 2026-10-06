import { Component, EventEmitter, inject, Output, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { AdjustmentAmounts } from '../../../../core/models/adjustment.model';

@Component({
  selector: 'app-adjustment-form',
  standalone: true,
  imports: [ReactiveFormsModule],
  templateUrl: './adjustment-form.html'
})
export class AdjustmentForm {
  private readonly formBuilder = inject(FormBuilder);

  @Output() preview = new EventEmitter<AdjustmentAmounts>();

  readonly advancedFieldsVisible = signal(false);

  // nonNullable garantit que getRawValue() retourne des nombres et non null.
  readonly form = this.formBuilder.nonNullable.group({
    ldpImpactLcrReglementaire: [0, [Validators.required]],
    ldpImpactLcrGestion: [0, [Validators.required]],
    impactLcrInflow: [0],
    impactLcrOutflow: [0],
    impactLcrAsset: [0],
    impactLcrAssetCash: [0]
  });

  toggleAdvancedFields(): void {
    this.advancedFieldsVisible.update((visible) => !visible);
  }

  submit(): void {
    if (this.form.invalid) {
      // Rend les messages de validation visibles si l'utilisateur soumet un
      // formulaire incomplet.
      this.form.markAllAsTouched();
      return;
    }

    // Aucun appel HTTP ici : le formulaire transmet seulement un brouillon à
    // la page par l'événement preview.
    this.preview.emit(this.form.getRawValue());
  }
}
