import * as React from 'react';
import { Widget } from '@lumino/widgets';
import { ReactWidget } from '@jupyterlab/ui-components';
import { AppStateService } from '../AppState';
import {
  FirstRunModal,
  IFirstRunModalProps
} from '../Components/FirstRunModal';

/**
 * React Widget wrapper for the FirstRunModal
 */
class FirstRunModalWidget extends ReactWidget {
  private modalService: FirstRunModalService;

  constructor(modalService: FirstRunModalService) {
    super();
    this.modalService = modalService;
    this.addClass('sage-ai-first-run-modal-widget');
    this.id = 'sage-ai-first-run-modal';
  }

  render(): React.ReactElement {
    console.log(
      '[FirstRunModalWidget] Rendering with props:',
      this.modalService.getModalProps()
    );
    return React.createElement(
      FirstRunModal,
      this.modalService.getModalProps()
    );
  }
}

/**
 * Service for managing the first-run modal
 */
export class FirstRunModalService {
  private static instance: FirstRunModalService | null = null;
  private widget: FirstRunModalWidget | null = null;
  private isShowing = false;

  private constructor() {}

  /**
   * Get the singleton instance
   */
  public static getInstance(): FirstRunModalService {
    if (!FirstRunModalService.instance) {
      FirstRunModalService.instance = new FirstRunModalService();
    }
    return FirstRunModalService.instance;
  }

  /**
   * Check if API key is set
   */
  private isApiKeySet(): boolean {
    const apiKey = AppStateService.getClaudeApiKey();
    console.log('[FirstRunModalService] Checking API key:', {
      apiKey: apiKey ? `[${apiKey.length} chars]` : 'null/undefined',
      trimmedLength: apiKey ? apiKey.trim().length : 0,
      isSet: Boolean(apiKey && apiKey.trim().length > 0)
    });
    return Boolean(apiKey && apiKey.trim().length > 0);
  }

  /**
   * Show the first-run modal if API key is not set
   */
  public showIfNeeded(): void {
    console.log('[FirstRunModalService] showIfNeeded called');
    const apiKeySet = this.isApiKeySet();
    console.log('[FirstRunModalService] API key set:', apiKeySet);
    console.log('[FirstRunModalService] Already showing:', this.isShowing);

    if (!apiKeySet && !this.isShowing) {
      console.log('[FirstRunModalService] Conditions met, showing modal');
      this.show();
    } else {
      console.log('[FirstRunModalService] Not showing modal because:', {
        apiKeySet,
        alreadyShowing: this.isShowing
      });
    }
  }

  /**
   * Show the first-run modal
   */
  public show(): void {
    console.log('[FirstRunModalService] show() called, current state:', {
      isShowing: this.isShowing,
      widgetExists: !!this.widget
    });

    if (this.isShowing) {
      console.log('[FirstRunModalService] Already showing, returning early');
      return;
    }

    this.isShowing = true;

    if (!this.widget) {
      console.log('[FirstRunModalService] Creating new ReactWidget');
      this.widget = new FirstRunModalWidget(this);
    }

    // Add to document body
    console.log('[FirstRunModalService] Adding ReactWidget to document body');
    Widget.attach(this.widget, document.body);

    console.log(
      '[FirstRunModalService] First-run modal ReactWidget attached successfully'
    );
  }

  /**
   * Hide the first-run modal
   */
  public hide(): void {
    if (!this.isShowing) {
      return;
    }

    this.isShowing = false;

    if (this.widget) {
      console.log('[FirstRunModalService] Detaching and disposing widget');
      Widget.detach(this.widget);
      this.widget.dispose();
      this.widget = null;
    }

    console.log('[FirstRunModalService] First-run modal hidden');
  }

  /**
   * Handle user clicking "Get started"
   */
  private handleGetStarted(): void {
    console.log('[FirstRunModalService] User clicked Get started');
    // TODO: Open signup URL
    // For now, just hide the modal
    this.hide();
  }

  /**
   * Handle user clicking "I already have an account"
   */
  private handleAlreadyHaveAccount(): void {
    console.log(
      '[FirstRunModalService] User clicked I already have an account'
    );
    // TODO: Open signin URL
    // For now, just hide the modal
    this.hide();
  }

  /**
   * Handle user clicking "Not now"
   */
  private handleNotNow(): void {
    console.log('[FirstRunModalService] User clicked Not now');
    this.hide();
  }

  /**
   * Get the modal props
   */
  public getModalProps(): IFirstRunModalProps {
    return {
      isVisible: this.isShowing,
      onGetStarted: () => this.handleGetStarted(),
      onAlreadyHaveAccount: () => this.handleAlreadyHaveAccount(),
      onNotNow: () => this.handleNotNow()
    };
  }

  /**
   * Update the widget to reflect current state
   */
  public update(): void {
    if (this.widget) {
      this.widget.update();
    }
  }

  /**
   * Force show the modal for testing purposes
   */
  public forceShow(): void {
    console.log('[FirstRunModalService] Force showing modal for testing');
    this.isShowing = false; // Reset state
    this.show();
  }

  /**
   * Get debug information
   */
  public getDebugInfo() {
    const apiKey = AppStateService.getClaudeApiKey();
    return {
      isShowing: this.isShowing,
      hasWidget: !!this.widget,
      apiKey: apiKey ? `[${apiKey.length} chars]` : 'null/undefined',
      apiKeySet: this.isApiKeySet(),
      widgetAttached: this.widget ? this.widget.isAttached : false,
      widgetDisposed: this.widget ? this.widget.isDisposed : false
    };
  }
}
