import { ReactWidget } from '@jupyterlab/ui-components';
import * as React from 'react';
import { SessionTimerBanner, SessionExpiredModal } from './SessionTimerBanner';

/**
 * Widget wrapper for the SessionTimerBanner component
 * This positions the banner at the top of the JupyterLab interface
 */
export class SessionTimerBannerWidget extends ReactWidget {
  private showExpiredModal: boolean = false;
  private updateCallback: (() => void) | null = null;
  private forceDisplay: boolean = false;

  constructor(forceDisplay: boolean = false) {
    super();
    this.forceDisplay = forceDisplay;
    this.addClass('sage-timer-banner-widget');
    this.id = 'sage-timer-banner-widget';
    // Trigger initial render
    this.update();
  }

  /**
   * Handle session expiration
   */
  private handleSessionExpired = (): void => {
    this.showExpiredModal = true;
    this.update();
  };

  /**
   * Handle modal exit
   */
  private handleModalExit = (): void => {
    window.location.href = 'https://signalpilot.ai/';
  };

  /**
   * Render the React component
   */
  render(): JSX.Element {
    return (
      <>
        <SessionTimerBanner 
          onSessionExpired={this.handleSessionExpired}
          forceDisplay={this.forceDisplay}
        />
        <SessionExpiredModal 
          show={this.showExpiredModal} 
          onExit={this.handleModalExit}
        />
      </>
    );
  }
}
