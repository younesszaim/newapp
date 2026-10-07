import { Component, inject, OnInit, signal, ViewChild } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';

import { AdjustmentService } from '../../../../core/services/adjustment.service';
import { LcrSummary } from '../../../../core/models/lcr-summary.model';
import { AdjustmentAmounts, AdjustmentBatchRequest } from '../../../../core/models/adjustment.model';
import { ContextSelector } from '../../components/context-selector/context-selector';
import { LcrSummaryTable } from '../../components/lcr-summary-table/lcr-summary-table';
import { AdjustmentForm } from '../../components/adjustment-form/adjustment-form';
import { ConfirmationDialog } from '../../components/confirmation-dialog/confirmation-dialog';

@Component({
  selector: 'app-create-adjustment',
  standalone: true,
  imports: [ContextSelector, LcrSummaryTable, AdjustmentForm, ConfirmationDialog],
  templateUrl: './create-adjustment.html'
})
export class CreateAdjustment implements OnInit {
  private readonly adjustmentService = inject(AdjustmentService);
  @ViewChild(AdjustmentForm) private adjustmentForm?: AdjustmentForm;

  readonly asofdates = signal<string[]>([]);
  readonly versions = signal<string[]>([]);
  readonly selectedAsofdate = signal<string | null>(null);
  readonly selectedVersion = signal<string | null>(null);
  readonly loadingDates = signal(false);
  readonly loadingVersions = signal(false);
  readonly loadingSummary = signal(false);
  readonly summary = signal<LcrSummary | null>(null);
  readonly adjustmentDraft = signal<AdjustmentAmounts[]>([]);
  readonly confirmationRequested = signal(false);
  readonly savingAdjustment = signal(false);
  readonly creationError = signal<string | null>(null);
  readonly creationSuccess = signal(false);
  readonly error = signal<string | null>(null);

  ngOnInit(): void {
    this.loadAsofdates();
  }

  loadAsofdates(): void {
    this.loadingDates.set(true);
    this.error.set(null);

    // HttpClient renvoie un Observable. subscribe déclenche la requête HTTP,
    // puis appelle next en cas de succès ou error en cas d'échec.
    this.adjustmentService.getAsofdates().subscribe({
      next: (asofdates) => {
        this.asofdates.set(asofdates);
        this.loadingDates.set(false);
      },
      error: () => {
        this.error.set('Impossible de charger les dates de reporting.');
        this.loadingDates.set(false);
      }
    });
  }

  selectAsofdate(asofdate: string): void {
    this.selectedAsofdate.set(asofdate || null);
    this.selectedVersion.set(null);
    this.versions.set([]);
    this.summary.set(null);
    this.adjustmentDraft.set([]);
    this.confirmationRequested.set(false);
    this.creationError.set(null);
    this.creationSuccess.set(false);
    this.error.set(null);

    if (asofdate) {
      this.loadVersions(asofdate);
    }
  }

  loadVersions(asofdate: string): void {
    this.loadingVersions.set(true);

    this.adjustmentService.getVersions(asofdate).subscribe({
      next: (versions) => {
        this.versions.set(versions);
        this.loadingVersions.set(false);
      },
      error: () => {
        this.error.set('Impossible de charger les versions disponibles.');
        this.loadingVersions.set(false);
      }
    });
  }

  selectVersion(version: string): void {
    this.selectedVersion.set(version || null);
    this.summary.set(null);
    this.adjustmentDraft.set([]);
    this.confirmationRequested.set(false);
    this.creationError.set(null);
    this.creationSuccess.set(false);
    this.error.set(null);

    const asofdate = this.selectedAsofdate();
    if (asofdate && version) {
      this.loadSummary(asofdate, version);
    }
  }

  loadSummary(asofdate: string, version: string): void {
    this.loadingSummary.set(true);

    this.adjustmentService.getLcrSummary(asofdate, version).subscribe({
      next: (summary) => {
        this.summary.set(summary);
        this.loadingSummary.set(false);
      },
      error: () => {
        this.error.set('Impossible de charger la situation LCR.');
        this.loadingSummary.set(false);
      }
    });
  }

  preparePreview(amounts: AdjustmentAmounts[]): void {
    this.adjustmentDraft.set(amounts);
    this.confirmationRequested.set(true);
    this.creationError.set(null);
  }

  closeConfirmation(): void {
    this.confirmationRequested.set(false);
    this.creationError.set(null);
  }

  adjustmentRequest(): AdjustmentBatchRequest | null {
    const asofdate = this.selectedAsofdate();
    const version = this.selectedVersion();
    const adjustments = this.adjustmentDraft();

    if (!asofdate || !version || adjustments.length === 0) {
      return null;
    }

    return { asofdate, asofdateflowVersion: version, adjustments };
  }

  confirmAdjustment(): void {
    const request = this.adjustmentRequest();
    if (!request) {
      return;
    }

    this.savingAdjustment.set(true);
    this.creationError.set(null);

    this.adjustmentService.createAdjustments(request).subscribe({
      next: () => {
        this.savingAdjustment.set(false);
        this.confirmationRequested.set(false);
        this.adjustmentDraft.set([]);
        this.adjustmentForm?.reset();
        this.creationSuccess.set(true);
        this.loadSummary(request.asofdate, request.asofdateflowVersion);
      },
      error: (error: HttpErrorResponse) => {
        this.savingAdjustment.set(false);
        this.creationError.set(
          error.status === 422
            ? 'Vérifiez les montants obligatoires de chaque ligne.'
            : "Impossible d'enregistrer les ajustements."
        );
      }
    });
  }
}
