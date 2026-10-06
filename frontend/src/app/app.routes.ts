import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'creer-ajustement' },
  {
    path: 'creer-ajustement',
    loadComponent: () =>
      import('./features/adjustments/pages/create-adjustment/create-adjustment').then(
        (component) => component.CreateAdjustment
      )
  },
  {
    path: 'ajustements',
    loadComponent: () =>
      import('./features/adjustments/pages/adjustment-registry/adjustment-registry').then(
        (component) => component.AdjustmentRegistry
      )
  },
  { path: '**', redirectTo: 'creer-ajustement' }
];
