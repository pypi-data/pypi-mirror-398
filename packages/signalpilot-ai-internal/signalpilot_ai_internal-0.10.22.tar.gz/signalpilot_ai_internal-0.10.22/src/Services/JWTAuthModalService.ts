import * as React from 'react';
import { Widget } from '@lumino/widgets';
import { ReactWidget } from '@jupyterlab/ui-components';
import { JWTAuthModal, IJWTAuthModalProps } from '../Components/JWTAuthModal';
import { JupyterAuthService } from './JupyterAuthService';
import { AppStateService } from '../AppState';

/**
 * React Widget wrapper for the JWTAuthModal
 */
class JWTAuthModalWidget extends ReactWidget {
  private modalService: JWTAuthModalService;

  constructor(modalService: JWTAuthModalService) {
    super();
    this.modalService = modalService;
    this.addClass('sage-ai-jwt-auth-modal-widget');
    this.id = 'sage-ai-jwt-auth-modal';
  }

  render(): React.ReactElement {
    console.log(
      '[JWTAuthModalWidget] Rendering with props:',
      this.modalService.getModalProps()
    );
    return React.createElement(JWTAuthModal, this.modalService.getModalProps());
  }
}

/**
 * Service for managing the JWT authentication modal
 */
export class JWTAuthModalService {
  private static instance: JWTAuthModalService | null = null;
  private widget: JWTAuthModalWidget | null = null;
  private isShowing = false;

  private constructor() {}

  /**
   * Get the singleton instance
   */
  public static getInstance(): JWTAuthModalService {
    if (!JWTAuthModalService.instance) {
      JWTAuthModalService.instance = new JWTAuthModalService();
    }
    return JWTAuthModalService.instance;
  }

  /**
   * Check if JWT is set and valid
   */
  private async isJWTValid(): Promise<boolean> {
    try {
      const isAuthenticated = await JupyterAuthService.isAuthenticated();
      const jwtToken = await JupyterAuthService.getJwtToken();

      console.log('[JWTAuthModalService] Checking JWT validity:', {
        jwtToken: jwtToken ? `[${jwtToken.length} chars]` : 'null/undefined',
        isAuthenticated,
        isValid: Boolean(
          isAuthenticated && jwtToken && jwtToken.trim().length > 0
        )
      });

      return Boolean(isAuthenticated && jwtToken && jwtToken.trim().length > 0);
    } catch (error) {
      console.error(
        '[JWTAuthModalService] Error checking JWT validity:',
        error
      );
      return false;
    }
  }

  /**
   * Show the JWT auth modal if JWT is not valid
   */
  public async showIfNeeded(): Promise<void> {
    console.log('[JWTAuthModalService] showIfNeeded called');

    // Check if we're in demo mode - if so, never auto-show the login modal
    const isDemoMode = AppStateService.isDemoMode();
    if (isDemoMode) {
      console.log(
        '[JWTAuthModalService] Demo mode enabled - skipping auto-show of login modal'
      );
      return;
    }

    const isValid = await this.isJWTValid();
    const tourCompleted = await AppStateService.hasCompletedWelcomeTour();
    if (isValid && !tourCompleted) {
      return;
    }
    if (!isValid && !this.isShowing) {
      console.log('[JWTAuthModalService] Conditions met, showing modal');
      this.show();
    } else {
      console.log('[JWTAuthModalService] Not showing modal because:', {
        jwtValid: isValid,
        alreadyShowing: this.isShowing,
        isDemoMode
      });
    }
  }

  /**
   * Show the JWT auth modal
   */
  public show(): void {
    console.log('[JWTAuthModalService] show() called, current state:', {
      isShowing: this.isShowing,
      widgetExists: !!this.widget
    });

    if (this.isShowing) {
      console.log('[JWTAuthModalService] Already showing, returning early');
      return;
    }

    this.isShowing = true;

    if (!this.widget) {
      console.log('[JWTAuthModalService] Creating new ReactWidget');
      this.widget = new JWTAuthModalWidget(this);
    }

    // Add to document body
    console.log('[JWTAuthModalService] Adding ReactWidget to document body');
    Widget.attach(this.widget, document.body);

    console.log(
      '[JWTAuthModalService] JWT auth modal ReactWidget attached successfully'
    );
  }

  /**
   * Hide the JWT auth modal
   */
  public hide(): void {
    if (!this.isShowing) {
      return;
    }

    this.isShowing = false;

    if (this.widget) {
      console.log('[JWTAuthModalService] Detaching and disposing widget');
      Widget.detach(this.widget);
      this.widget.dispose();
      this.widget = null;
    }

    console.log('[JWTAuthModalService] JWT auth modal hidden');
  }

  /**
   * Handle user clicking "Log In"
   */
  private handleLogin(): void {
    console.log('[JWTAuthModalService] User clicked Log In');
    try {
      // Use the same login logic as the settings page
      JupyterAuthService.openLoginPage();
      // Keep the modal open - it will automatically close when auth is successful
    } catch (error) {
      console.error('[JWTAuthModalService] Failed to open login page:', error);
    }
  }

  /**
   * Handle user clicking "Continue without login"
   */
  private handleDismiss(): void {
    console.log('[JWTAuthModalService] User clicked Continue without login');
    this.hide();
  }

  /**
   * Get the modal props
   */
  public getModalProps(): IJWTAuthModalProps {
    return {
      isVisible: this.isShowing,
      onLogin: () => this.handleLogin(),
      onDismiss: () => this.handleDismiss()
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
    console.log('[JWTAuthModalService] Force showing modal for testing');
    this.isShowing = false; // Reset state
    this.show();
  }

  /**
   * Check authentication status and hide modal if now authenticated
   */
  public async checkAndHideIfAuthenticated(): Promise<void> {
    try {
      const isValid = await this.isJWTValid();
      if (isValid && this.isShowing) {
        console.log(
          '[JWTAuthModalService] User is now authenticated, hiding modal'
        );
        this.hide();

        // Show login success modal only if not on launcher or tour is completed
        // Skip if in takeover mode
        try {
          // Check takeover mode from AppState
          const isInTakeoverMode = AppStateService.isTakeoverMode();

          if (!isInTakeoverMode) {
            const { LoginSuccessModalService } = await import(
              './LoginSuccessModalService'
            );

            // Small delay to ensure UI transition is smooth
            setTimeout(async () => {
              await LoginSuccessModalService.showLoginSuccess();
            }, 300);

            console.log(
              '[JWTAuthModalService] Login success modal triggered after authentication'
            );
          } else {
            console.log('[JWTAuthModalService] Skipping login success modal - takeover mode active');
          }
        } catch (modalError) {
          console.error(
            '[JWTAuthModalService] Failed to show login success modal:',
            modalError
          );
          // Don't fail if modal fails
        }
      }
    } catch (error) {
      console.error(
        '[JWTAuthModalService] Error checking authentication status:',
        error
      );
    }
  }

  /**
   * Get debug information
   */
  public async getDebugInfo() {
    const jwtToken = await JupyterAuthService.getJwtToken();
    const isAuthenticated = await JupyterAuthService.isAuthenticated();
    const isValid = await this.isJWTValid();

    return {
      isShowing: this.isShowing,
      hasWidget: !!this.widget,
      jwtToken: jwtToken ? `[${jwtToken.length} chars]` : 'null/undefined',
      isAuthenticated,
      isJWTValid: isValid,
      widgetAttached: this.widget ? this.widget.isAttached : false,
      widgetDisposed: this.widget ? this.widget.isDisposed : false
    };
  }

  /**
   * Initialize JWT token on app startup - loads JWT and sets it in settings registry immediately
   */
  public static async initializeJWTOnStartup(): Promise<boolean> {
    console.log('[JWTAuthModalService] Initializing JWT on app startup...');

    try {
      // Delegate to JupyterAuthService for actual JWT initialization
      const jwtInitialized = await JupyterAuthService.initializeJWTOnStartup();

      if (jwtInitialized) {
        console.log(
          '[JWTAuthModalService] JWT authentication initialized successfully on startup'
        );
      } else {
        console.log(
          '[JWTAuthModalService] No JWT token found during startup initialization'
        );
      }

      return jwtInitialized;
    } catch (error) {
      console.error(
        '[JWTAuthModalService] Failed to initialize JWT on startup:',
        error
      );
      return false;
    }
  }
}
