import { ReactWidget } from '@jupyterlab/ui-components';
import * as React from 'react';
import { TrialBanner } from './TrialBanner';

/**
 * Widget wrapper for the TrialBanner component
 * This positions the banner at the top of the JupyterLab interface
 */
export class TrialBannerWidget extends ReactWidget {
  constructor() {
    super();
    this.addClass('sage-trial-banner-widget');
    this.id = 'sage-trial-banner-widget';
    // Trigger initial render
    this.update();
  }

  /**
   * Render the React component
   */
  render(): JSX.Element {
    return <TrialBanner />;
  }
}
