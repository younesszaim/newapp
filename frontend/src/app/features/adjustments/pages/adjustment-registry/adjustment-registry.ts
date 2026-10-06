import { Component, computed, inject, OnInit, signal } from '@angular/core';

import { AdjustmentRegistryItem } from '../../../../core/models/adjustment.model';
import { CompactEuroPipe } from '../../../../core/pipes/compact-euro.pipe';
import { AdjustmentService } from '../../../../core/services/adjustment.service';

@Component({
  selector: 'app-adjustment-registry',
  standalone: true,
  imports: [CompactEuroPipe],
  templateUrl: './adjustment-registry.html'
})
export class AdjustmentRegistry implements OnInit {
  private readonly adjustmentService = inject(AdjustmentService);

  readonly adjustments = signal<AdjustmentRegistryItem[]>([]);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly selectedAsofdate = signal('');
  readonly selectedVersion = signal('');
  readonly viewedAdjustment = signal<AdjustmentRegistryItem | null>(null);
  readonly adjustmentToDelete = signal<AdjustmentRegistryItem | null>(null);
  readonly deleting = signal(false);
  readonly deleteError = signal<string | null>(null);

  readonly asofdates = computed(() =>
    [...new Set(this.adjustments().map((item) => item.asofdate))].sort().reverse()
  );

  readonly versions = computed(() =>
    [
      ...new Set(
        this.adjustments()
          .filter((item) => !this.selectedAsofdate() || item.asofdate === this.selectedAsofdate())
          .map((item) => item.asofdateflowVersion)
      )
    ].sort().reverse()
  );

  readonly filteredAdjustments = computed(() =>
    this.adjustments().filter(
      (item) =>
        (!this.selectedAsofdate() || item.asofdate === this.selectedAsofdate()) &&
        (!this.selectedVersion() || item.asofdateflowVersion === this.selectedVersion())
    )
  );

  ngOnInit(): void {
    this.loadAdjustments();
  }

  loadAdjustments(): void {
    this.loading.set(true);
    this.error.set(null);

    this.adjustmentService.getAdjustments().subscribe({
      next: (adjustments) => {
        this.adjustments.set(adjustments);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Impossible de charger le registre des ajustements.');
        this.loading.set(false);
      }
    });
  }

  selectAsofdate(event: Event): void {
    this.selectedAsofdate.set((event.target as HTMLSelectElement).value);
    this.selectedVersion.set('');
  }

  selectVersion(event: Event): void {
    this.selectedVersion.set((event.target as HTMLSelectElement).value);
  }

  formatDateTime(value: string): string {
    return new Intl.DateTimeFormat('fr-FR', {
      dateStyle: 'medium',
      timeStyle: 'short'
    }).format(new Date(value));
  }

  askForDeletion(item: AdjustmentRegistryItem): void {
    this.deleteError.set(null);
    this.adjustmentToDelete.set(item);
  }

  cancelDeletion(): void {
    if (!this.deleting()) {
      this.adjustmentToDelete.set(null);
      this.deleteError.set(null);
    }
  }

  confirmDeletion(): void {
    const item = this.adjustmentToDelete();
    if (!item || this.deleting()) {
      return;
    }

    this.deleting.set(true);
    this.deleteError.set(null);
    this.adjustmentService.deleteAdjustment(item.adjustmentId).subscribe({
      next: () => {
        if (this.viewedAdjustment()?.adjustmentId === item.adjustmentId) {
          this.viewedAdjustment.set(null);
        }
        this.adjustmentToDelete.set(null);
        this.deleting.set(false);
        this.loadAdjustments();
      },
      error: () => {
        this.deleteError.set("Impossible de supprimer l'ajustement.");
        this.deleting.set(false);
      }
    });
  }
}
