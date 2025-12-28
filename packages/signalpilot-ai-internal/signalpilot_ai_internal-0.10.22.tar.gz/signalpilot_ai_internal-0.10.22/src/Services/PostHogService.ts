import posthog from 'posthog-js';

import { JupyterAuthService } from './JupyterAuthService';

// Build-time configuration for tracking
// This file is generated during build based on DISABLE_TRACKING environment variable
// eslint-disable-next-line @typescript-eslint/no-var-requires
const trackingConfig = require('../Config/tracking_config.json');

export class PostHogService {
  private static instance: PostHogService;
  private initialized = false;
  private readonly POSTHOG_PROJECT_API_KEY =
    'phc_E3oZ3UN1nOoWsMMKtPBAGKSqQCtuKutiwmfUZAu3ybr';
  private readonly POSTHOG_API_HOST = 'https://user.signalpilot.ai'; // Production PostHog instance

  private constructor() {}

  /**
   * Check if tracking is disabled via DISABLE_TRACKING environment variable
   */
  public isTrackingDisabled(): boolean {
    // Check build-time config file (generated during build)
    if (trackingConfig.disableTracking === true) {
      return true;
    }
    // Fallback: check window global (for runtime configuration)
    if (
      typeof window !== 'undefined' &&
      (window as any).__DISABLE_TRACKING__ === true
    ) {
      return true;
    }
    return false;
  }

  public getSessionId(): string | null {
    return posthog.get_session_id();
  }

  public static getInstance(): PostHogService {
    if (!PostHogService.instance) {
      PostHogService.instance = new PostHogService();
    }
    return PostHogService.instance;
  }

  /**
   * Initialize PostHog with proper configuration
   * Always tracks unless DISABLE_TRACKING is true
   */
  public async initialize(): Promise<void> {
    if (this.initialized) {
      return;
    }

    try {
      // Check if tracking is disabled via environment variable
      if (this.isTrackingDisabled()) {
        console.log('PostHog tracking disabled via DISABLE_TRACKING flag');
        this.initialized = true;
        return;
      }

      // Always initialize tracking unless disabled
      posthog.init(this.POSTHOG_PROJECT_API_KEY, {
        api_host: this.POSTHOG_API_HOST,
        persistence: 'localStorage',
        cross_subdomain_cookie: false,
        secure_cookie: window.location.protocol === 'https:'
      });

      // Identify user after initialization
      await this.identifyUser();

      this.initialized = true;
    } catch (error) {
      console.error('Failed to initialize PostHog:', error);
    }
  }

  /**
   * Identify user with their profile information
   */
  public async identifyUser(): Promise<void> {
    try {
      if (this.isTrackingDisabled()) {
        return;
      }

      const userProfile = await JupyterAuthService.getUserProfile();
      if (userProfile) {
        posthog.identify(userProfile.id, userProfile);
      }
    } catch (error) {
      console.error('Failed to identify user:', error);
    }
  }

  public captureTimeToBeginDemo(): void {
    try {
      if (this.isTrackingDisabled()) {
        return;
      }

      // Try sessionStorage first, then localStorage as fallback
      let loadStartTime = sessionStorage.getItem(
        'demo-loading-initialized-timestamp'
      );
      if (!loadStartTime) {
        loadStartTime = localStorage.getItem(
          'demo-loading-initialized-timestamp'
        );
        if (loadStartTime) {
          localStorage.removeItem('demo-loading-initialized-timestamp');
        }
      } else {
        sessionStorage.removeItem('demo-loading-initialized-timestamp');
      }

      if (!loadStartTime) {
        console.warn(
          '[PostHogService] demo-loading-initialized-timestamp not found in sessionStorage or localStorage'
        );
        return;
      }

      const loadStartTimeDate = new Date(loadStartTime);
      const loadTime = Date.now() - loadStartTimeDate.getTime();

      posthog.capture('time_to_begin_demo', { time_to_begin_demo: loadTime });
    } catch (error) {
      console.error('Failed to capture load time:', error);
    }
  }
}

// Export a singleton instance
export const posthogService = PostHogService.getInstance();
