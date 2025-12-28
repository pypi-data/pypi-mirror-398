import * as React from 'react';
import { ReactWidget } from '@jupyterlab/ui-components';
import { HTMLPreviewContent } from './HTMLPreviewWidget/HTMLPreviewContent';

/**
 * HTML Preview Widget - Displays a preview of a notebook as HTML
 */
export class HTMLPreviewWidget extends ReactWidget {
  private notebookPath: string;
  private onClose: () => void;

  constructor(notebookPath: string, onClose: () => void) {
    super();
    this.notebookPath = notebookPath;
    this.onClose = onClose;
    this.id = `html-preview-${Date.now()}`;

    // Set tab title to filename
    const filename = notebookPath.split('/').pop() || 'notebook';
    this.title.label = filename;
    this.title.caption = `Preview: ${notebookPath}`;
    this.title.iconClass = 'jp-icon-cloud';
    this.title.closable = true;

    this.addClass('html-preview-widget');
  }

  /**
   * Render the React component
   */
  render(): React.ReactElement {
    return (
      <HTMLPreviewContent
        notebookPath={this.notebookPath}
        onClose={this.onClose}
      />
    );
  }

  /**
   * Handle close request when the widget is closed
   */
  protected onCloseRequest(): void {
    this.dispose();
  }

  /**
   * Dispose of the widget and clean up resources
   */
  dispose(): void {
    super.dispose();
  }
}
