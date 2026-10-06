import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'compactEuro',
  standalone: true
})
export class CompactEuroPipe implements PipeTransform {
  /**
   * Formate uniquement l'affichage. La valeur numérique originale reste intacte.
   * Exemples : 1 500 000 -> 1,5 M€ ; 530 000 -> 530 K€.
   */
  transform(value: number): string {
    const absoluteValue = Math.abs(value);

    if (absoluteValue >= 1_000_000_000) {
      return `${this.format(value / 1_000_000_000)} Bn€`;
    }
    if (absoluteValue >= 1_000_000) {
      return `${this.format(value / 1_000_000)} M€`;
    }
    if (absoluteValue >= 1_000) {
      return `${this.format(value / 1_000)} K€`;
    }

    return `${this.format(value, 0)} €`;
  }

  private format(value: number, maximumFractionDigits = 1): string {
    return new Intl.NumberFormat('fr-FR', {
      minimumFractionDigits: 0,
      maximumFractionDigits
    }).format(value);
  }
}
