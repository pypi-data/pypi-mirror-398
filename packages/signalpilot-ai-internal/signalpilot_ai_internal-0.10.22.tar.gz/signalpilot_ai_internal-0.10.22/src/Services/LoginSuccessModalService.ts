import * as React from 'react';
import { Widget } from '@lumino/widgets';
import { ReactWidget } from '@jupyterlab/ui-components';
import {
  LoginSuccessToast,
  ILoginSuccessToastProps
} from '../Components/LoginSuccessToast';

/**
 * React Widget wrapper for the LoginSuccessToast
 */
class LoginSuccessToastWidget extends ReactWidget {
  private toastService: LoginSuccessModalService;

  constructor(toastService: LoginSuccessModalService) {
    super();
    this.toastService = toastService;
    this.addClass('sage-login-success-toast-widget');
    this.id = 'sage-login-success-toast';
  }

  render(): React.ReactElement {
    console.log(
      '[LoginSuccessToastWidget] Rendering with props:',
      this.toastService.getToastProps()
    );
    return React.createElement(
      LoginSuccessToast,
      this.toastService.getToastProps()
    );
  }
}

/**
 * Service for managing the login success toast
 */
export class LoginSuccessModalService {
  private static instance: LoginSuccessModalService | null = null;
  private widget: LoginSuccessToastWidget | null = null;
  private isShowing = false;

  private constructor() {}

  /**
   * Get the singleton instance
   */
  public static getInstance(): LoginSuccessModalService {
    if (!LoginSuccessModalService.instance) {
      LoginSuccessModalService.instance = new LoginSuccessModalService();
    }
    return LoginSuccessModalService.instance;
  }

  /**
   * Show the login success toast
   */
  public show(): void {
    console.log('[LoginSuccessModalService] show() called, current state:', {
      isShowing: this.isShowing,
      widgetExists: !!this.widget
    });

    if (this.isShowing) {
      console.log(
        '[LoginSuccessModalService] Already showing, returning early'
      );
      return;
    }

    this.isShowing = true;

    if (!this.widget) {
      console.log('[LoginSuccessModalService] Creating new ReactWidget');
      this.widget = new LoginSuccessToastWidget(this);
    }

    // Add to document body
    console.log(
      '[LoginSuccessModalService] Adding ReactWidget to document body'
    );
    Widget.attach(this.widget, document.body);

    console.log(
      '[LoginSuccessModalService] Login success toast ReactWidget attached successfully'
    );
  }

  /**
   * Hide the login success toast
   */
  public hide(): void {
    console.log('[LoginSuccessModalService] hide() called');

    if (!this.isShowing) {
      console.log('[LoginSuccessModalService] Not showing, returning early');
      return;
    }

    this.isShowing = false;

    if (this.widget) {
      console.log('[LoginSuccessModalService] Detaching and disposing widget');
      Widget.detach(this.widget);
      this.widget.dispose();
      this.widget = null;
    }

    console.log('[LoginSuccessModalService] Login success toast hidden');
  }

  /**
   * Handle user clicking close or auto-close
   */
  private handleClose(): void {
    console.log(
      '[LoginSuccessModalService] User closed toast or auto-close triggered'
    );
    this.hide();
  }

  /**
   * Get the toast props
   */
  public getToastProps(): ILoginSuccessToastProps {
    return {
      isVisible: this.isShowing,
      onClose: () => this.handleClose()
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
   * Get debug information
   */
  public getDebugInfo() {
    return {
      isShowing: this.isShowing,
      hasWidget: !!this.widget,
      widgetAttached: this.widget ? this.widget.isAttached : false,
      widgetDisposed: this.widget ? this.widget.isDisposed : false
    };
  }

  /**
   * Show login success toast after successful authentication
   * This is the main public method to trigger the success toast
   * Will skip showing if on launcher and tour not completed
   */
  public static async showLoginSuccess(): Promise<void> {
    console.log('[LoginSuccessModalService] showLoginSuccess() called');

    try {
      const { AppStateService } = await import('../AppState');

      const isLauncherActive = AppStateService.isLauncherActive();
      const tourCompleted = await AppStateService.hasCompletedWelcomeTour();

      console.log('[LoginSuccessModalService] State check:', {
        isLauncherActive,
        tourCompleted
      });

      // Only show the login success toast if:
      // 1. Not on launcher, OR
      // 2. Tour is already completed
      const shouldShowToast = tourCompleted;

      if (!shouldShowToast) {
        console.log(
          '[LoginSuccessModalService] ❌ Skipping toast - on launcher and tour not completed'
        );
        return;
      }

      console.log('[LoginSuccessModalService] ✅ Showing toast');
      const instance = LoginSuccessModalService.getInstance();
      instance.show();

      // Update demo control panel visibility after successful authentication
      try {
        const { updateDemoControlPanelVisibility } = await import('../Demo/demo');
        await updateDemoControlPanelVisibility();
      } catch (error) {
        console.error(
          '[LoginSuccessModalService] Error updating demo control panel visibility:',
          error
        );
      }
    } catch (error) {
      console.error(
        '[LoginSuccessModalService] Error checking if should show toast:',
        error
      );
      // Show anyway if check fails
      const instance = LoginSuccessModalService.getInstance();
      instance.show();
    }
  }

  /**
   * Debug method to test the toast - can be called from console
   */
  public static debugShow(): void {
    console.log(
      '[LoginSuccessModalService] Debug: Showing login success toast'
    );
    void LoginSuccessModalService.showLoginSuccess();
  }
}
