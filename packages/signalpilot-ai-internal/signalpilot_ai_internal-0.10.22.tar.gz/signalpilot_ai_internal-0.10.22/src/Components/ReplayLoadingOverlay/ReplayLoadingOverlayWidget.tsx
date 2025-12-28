import { ReactWidget } from '@jupyterlab/ui-components';
import * as React from 'react';
import { ReplayLoadingOverlay } from './ReplayLoadingOverlay';

/**
 * Widget wrapper for the ReplayLoadingOverlay component
 * This creates a full-page loading overlay for replay mode
 */
export class ReplayLoadingOverlayWidget extends ReactWidget {
  private overlayVisible: boolean = false;
  private isFadingOut: boolean = false;
  private message: string = '';

  constructor() {
    super();
    this.addClass('sage-replay-loading-overlay-widget');
    this.id = 'sage-replay-loading-overlay-widget';
  }

  /**
   * Show the loading overlay with fade-in animation
   * @param message Optional message to display below the loading text
   */
  public show(message?: string): void {
    this.overlayVisible = true;
    this.isFadingOut = false;
    if (message !== undefined) {
      this.message = message;
    }
    this.update();
  }

  /**
   * Hide the loading overlay with fade-out animation
   */
  public hide(): void {
    this.isFadingOut = true;
    this.update();
    
    // Actually hide after fade-out animation completes
    setTimeout(() => {
      this.overlayVisible = false;
      this.isFadingOut = false;
      this.update();
    }, 600); // Match fade-out duration
  }

  /**
   * Check if the overlay is currently visible
   */
  public getIsVisible(): boolean {
    return this.overlayVisible;
  }

  /**
   * Update the message displayed in the overlay
   * @param message The new message to display
   */
  public updateMessage(message: string): void {
    this.message = message;
    this.update();
  }

  /**
   * Render the React component
   */
  render(): JSX.Element {
    return (
      <ReplayLoadingOverlay
        isVisible={this.overlayVisible}
        isFadingOut={this.isFadingOut}
        message={this.message}
      />
    );
  }
}

