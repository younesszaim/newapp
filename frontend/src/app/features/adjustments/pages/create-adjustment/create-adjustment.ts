import { Component, inject, OnInit, signal } from '@angular/core';

import { AdjustmentService } from '../../../../core/services/adjustment.service';
import { LcrSummary } from '../../../../core/models/lcr-summary.model';
import { ContextSelector } from '../../components/context-selector/context-selector';
import { LcrSummaryTable } from '../../components/lcr-summary-table/lcr-summary-table';

@Component({
  selector: 'app-create-adjustment',
  standalone: true,
  imports: [ContextSelector, LcrSummaryTable],
  templateUrl: './create-adjustment.html'
})
export class CreateAdjustment implements OnInit {
  private readonly adjustmentService = inject(AdjustmentService);

  readonly asofdates = signal<string[]>([]);
  readonly versions = signal<string[]>([]);
  readonly selectedAsofdate = signal<string | null>(null);
  readonly selectedVersion = signal<string | null>(null);
  readonly loadingDates = signal(false);
  readonly loadingVersions = signal(false);
  readonly loadingSummary = signal(false);
  readonly summary = signal<LcrSummary | null>(null);
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
}
