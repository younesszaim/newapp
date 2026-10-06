import { Component, EventEmitter, Input, Output } from '@angular/core';

@Component({
  selector: 'app-context-selector',
  standalone: true,
  templateUrl: './context-selector.html'
})
export class ContextSelector {
  @Input() asofdates: string[] = [];
  @Input() versions: string[] = [];
  @Input() selectedAsofdate: string | null = null;
  @Input() selectedVersion: string | null = null;
  @Input() loadingDates = false;
  @Input() loadingVersions = false;

  @Output() asofdateChange = new EventEmitter<string>();
  @Output() versionChange = new EventEmitter<string>();

  onAsofdateChange(event: Event): void {
    this.asofdateChange.emit((event.target as HTMLSelectElement).value);
  }

  onVersionChange(event: Event): void {
    this.versionChange.emit((event.target as HTMLSelectElement).value);
  }
}
