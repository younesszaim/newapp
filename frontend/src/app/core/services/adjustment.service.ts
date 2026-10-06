import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { LcrSummary } from '../models/lcr-summary.model';
import { Adjustment, AdjustmentRequest } from '../models/adjustment.model';

@Injectable({ providedIn: 'root' })
export class AdjustmentService {
  // inject() demande à Angular l'instance HttpClient configurée dans app.config.ts.
  private readonly http = inject(HttpClient);
  private readonly apiUrl = environment.apiUrl;

  /** Exemple de réponse : ['2026-10-05', '2026-10-04']. */
  getAsofdates(): Observable<string[]> {
    return this.http.get<string[]>(`${this.apiUrl}/asofdates`);
  }

  /** Exemple de réponse : ['2026-10-06T15:30:00']. */
  getVersions(asofdate: string): Observable<string[]> {
    return this.http.get<string[]>(
      `${this.apiUrl}/asofdates/${encodeURIComponent(asofdate)}/versions`
    );
  }

  getLcrSummary(asofdate: string, version: string): Observable<LcrSummary> {
    return this.http.get<LcrSummary>(`${this.apiUrl}/lcr-summary`, {
      params: { asofdate, version }
    });
  }

  createAdjustment(request: AdjustmentRequest): Observable<Adjustment> {
    return this.http.post<Adjustment>(`${this.apiUrl}/adjustments`, request);
  }
}
