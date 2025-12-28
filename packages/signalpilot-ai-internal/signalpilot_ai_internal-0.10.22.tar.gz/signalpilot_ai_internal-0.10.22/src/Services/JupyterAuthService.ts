import { StateDBCachingService } from '../utils/backendCaching';
import { TokenEncoder } from '../utils/tokenEncoder';
import { jwtDecode } from 'jwt-decode';
import { AppStateService } from '../AppState';

export class JupyterAuthService {
  private static readonly AUTH_JWT_KEY = 'jupyter_auth_jwt';
  private static readonly WEB_APP_BASE_URL = 'https://app.signalpilot.ai'; // Local portal URL

  /**
   * Store JWT token in StateDB with encoding
   */
  public static async storeJwtToken(jwtToken: string): Promise<void> {
    console.log(
      '[JupyterAuthService] ========== STORING JWT TOKEN IN STATEDB =========='
    );

    if (!jwtToken) {
      console.warn('[JupyterAuthService] ❌ Cannot store empty JWT token');
      console.log(
        '[JupyterAuthService] ========== JWT STORAGE ABORTED (EMPTY TOKEN) =========='
      );
      return;
    }

    try {
      console.log('[JupyterAuthService] Received JWT token for storage');
      console.log('[JupyterAuthService] JWT token length:', jwtToken.length);
      console.log(
        '[JupyterAuthService] Token preview:',
        jwtToken.substring(0, 20) + '...'
      );
      console.log(
        '[JupyterAuthService] Encoding JWT token for secure storage...'
      );

      // Encode the token before storing
      const encodedToken = TokenEncoder.encode(jwtToken);
      console.log('[JupyterAuthService] JWT token encoded successfully');
      console.log(
        '[JupyterAuthService] Encoded token length:',
        encodedToken.length
      );

      await StateDBCachingService.setValue(this.AUTH_JWT_KEY, encodedToken);
      console.log(
        '[JupyterAuthService] ✅ JWT token stored successfully in StateDB'
      );
      console.log(
        '[JupyterAuthService] ⚠️  JWT token is ONLY stored in StateDB (not in caching service)'
      );
      console.log(
        '[JupyterAuthService] ========== JWT STORAGE COMPLETED (SUCCESS) =========='
      );
    } catch (error) {
      console.error(
        '[JupyterAuthService] ❌ Failed to store JWT token:',
        error
      );
      console.log(
        '[JupyterAuthService] ========== JWT STORAGE FAILED =========='
      );
    }
  }

  /**
   * Retrieve JWT token from StateDB with decoding
   */
  public static async getJwtToken(): Promise<string | null> {
    try {
      const encodedToken = await StateDBCachingService.getValue(
        this.AUTH_JWT_KEY,
        null
      );

      if (!encodedToken || typeof encodedToken !== 'string') {
        console.log(
          '[JupyterAuthService] ❌ No JWT token found in StateDB cache'
        );
        console.log(
          '[JupyterAuthService] ========== JWT RETRIEVAL COMPLETED (NO TOKEN) =========='
        );
        return null;
      }

      // Decode the token before returning
      const decodedToken = TokenEncoder.decode(encodedToken);

      if (!decodedToken) {
        console.warn(
          '[JupyterAuthService] ❌ Failed to decode JWT token - token may be corrupted'
        );
        console.log(
          '[JupyterAuthService] ========== JWT RETRIEVAL COMPLETED (DECODE FAILED) =========='
        );
      }

      return decodedToken || null;
    } catch (error) {
      console.error(
        '[JupyterAuthService] ❌ Failed to retrieve JWT token:',
        error
      );
      console.log(
        '[JupyterAuthService] ========== JWT RETRIEVAL FAILED =========='
      );
      return null;
    }
  }

  /**
   * Clear JWT token from StateDB
   */
  public static async clearJwtToken(): Promise<void> {
    try {
      await StateDBCachingService.removeValue(this.AUTH_JWT_KEY);
      console.log('[JupyterAuthService] JWT token cleared successfully');
    } catch (error) {
      console.error('[JupyterAuthService] Failed to clear JWT token:', error);
    }
  }

  /**
   * Get the base Jupyter URL including user path if present
   * Handles URLs like http://localhost/user0/lab -> http://localhost/user0
   */
  private static getJupyterBaseUrl(): string {
    const url = window.location.href;

    // Match pattern: /userN/ where N is one or more digits
    const match = url.match(/^(.*?\/user\d+)/);

    if (match && match[1]) {
      console.log(
        '[JupyterAuthService] Using base URL with user path:',
        match[1]
      );
      return match[1];
    }

    // Fallback to origin if no user path found
    console.log(
      '[JupyterAuthService] No user path found, using origin:',
      window.location.origin
    );
    return window.location.origin;
  }

  /**
   * Open the web app login page with callback URL
   */
  public static openLoginPage(): void {
    const jupyterUrl = this.getJupyterBaseUrl();
    const callbackUrl = `${jupyterUrl}/lab?auth_callback=true`;
    const loginUrl = `${this.WEB_APP_BASE_URL}/login?redirect_url=${encodeURIComponent(callbackUrl)}`;

    window.location.href = loginUrl;
  }

  /**
   * Exchange temporary token for JWT
   */
  public static async exchangeTempToken(tempToken: string): Promise<string> {
    const response = await fetch(
      `${this.WEB_APP_BASE_URL}/api/auth/exchange-temp-token`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ tempToken })
      }
    );

    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ error: 'Unknown error' }));
      throw new Error(errorData.error || 'Failed to exchange token');
    }

    const { jwtToken } = await response.json();
    return jwtToken;
  }

  /**
   * Check if user is authenticated
   */
  public static async isAuthenticated(): Promise<boolean> {
    const token = await this.getJwtToken();
    return token !== null && token !== '';
  }

  /**
   * Get user profile from API using JWT token
   */
  public static async getUserProfile(): Promise<any> {
    console.log('[JupyterAuthService] Getting user profile...');

    const token = await this.getJwtToken();
    if (!token) {
      throw new Error('No JWT token available');
    }

    try {
      const response = await fetch(
        'https://sage.alpinex.ai:8761/account/profile',
        {
          method: 'GET',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (!response.ok) {
        const errorData = await response
          .json()
          .catch(() => ({ error: 'Unknown error' }));
        throw new Error(
          errorData.error ||
            `Failed to get user profile: ${response.statusText}`
        );
      }

      const profileData = await response.json();
      console.log('[JupyterAuthService] User profile retrieved successfully');
      return profileData.data; // Return the data portion of the response
    } catch (error) {
      console.error('[JupyterAuthService] Failed to get user profile:', error);
      throw error;
    }
  }

  /**
   * Handle callback from web app authentication
   */
  public static async handleAuthCallback(): Promise<boolean> {
    const urlParams = new URLSearchParams(window.location.search);
    const tempToken = urlParams.get('temp_token');
    const isCallback = urlParams.get('auth_callback') === 'true';

    if (!isCallback || !tempToken) {
      return false;
    }

    try {
      // Exchange temporary token for actual JWT
      const jwtToken = await this.exchangeTempToken(tempToken);

      // Store the JWT
      await this.storeJwtToken(jwtToken);

      // Clean up URL parameters
      const newUrl = new URL(window.location.href);
      newUrl.searchParams.delete('temp_token');
      newUrl.searchParams.delete('auth_callback');
      window.history.replaceState({}, '', newUrl.toString());

      // Extend session timeout to 60 minutes after successful authentication
      try {
        const { setSessionTimeoutAfterAuth } = await import('../sessionUtils');
        const result = await setSessionTimeoutAfterAuth();
        if (result) {
          console.log(
            '[JupyterAuthService] ✅ Session timeout extended to 60 minutes after authentication'
          );
        }
      } catch (sessionError) {
        console.warn(
          '[JupyterAuthService] Failed to extend session timeout (may not be in cloud demo):',
          sessionError
        );
        // Don't fail authentication if session extension fails
      }

      // Show login success modal only if not on launcher or tour is completed
      // Skip if in takeover mode (check AppState)
      try {
        const isInTakeoverMode = AppStateService.isTakeoverMode();

        if (!isInTakeoverMode) {
          const { LoginSuccessModalService } = await import(
            './LoginSuccessModalService'
          );

          // Small delay to ensure UI is ready
          setTimeout(async () => {
            await LoginSuccessModalService.showLoginSuccess();
          }, 500);

          console.log('[JupyterAuthService] Login success modal triggered');
        } else {
          console.log(
            '[JupyterAuthService] Skipping login success modal - takeover mode active'
          );
        }
      } catch (modalError) {
        console.error(
          '[JupyterAuthService] Failed to show login success modal:',
          modalError
        );
      }

      return true;
    } catch (error) {
      console.error('Failed to handle auth callback:', error);
      return false;
    }
  }

  /**
   * Initialize JWT token on app startup - loads JWT and sets it in settings registry immediately
   */
  public static async initializeJWTOnStartup(): Promise<boolean> {
    console.log(
      '[JupyterAuthService] ========== STARTING JWT INITIALIZATION ON APP STARTUP =========='
    );

    try {
      // First check for auth callback
      console.log('[JupyterAuthService] Checking for auth callback...');
      const callbackHandled = await this.handleAuthCallback();
      if (callbackHandled) {
        console.log(
          '[JupyterAuthService] ✅ Auth callback handled during startup'
        );
      } else {
        console.log('[JupyterAuthService] ℹ️  No auth callback to handle');
      }

      // Get JWT token from StateDB
      console.log(
        '[JupyterAuthService] Attempting to retrieve JWT token from StateDB...'
      );
      const jwtToken = await this.getJwtToken();

      if (jwtToken) {
        console.log(
          '[JupyterAuthService] ✅ JWT token found during startup initialization'
        );
        console.log('[JupyterAuthService] JWT token length:', jwtToken.length);
        console.log(
          '[JupyterAuthService] JWT token preview:',
          jwtToken.substring(0, 20) + '...'
        );

        // IMPORTANT: DO NOT store JWT in settings registry or caching service!
        // JWT should only be stored in StateDB and used directly from there
        console.log(
          '[JupyterAuthService] ⚠️  NOT storing JWT in settings registry (per requirements)'
        );

        // Update AppState with JWT token for Claude API key
        try {
          const { AppStateService } = await import('../AppState');
          AppStateService.updateClaudeSettings({ claudeApiKey: jwtToken });
          console.log(
            '[JupyterAuthService] ✅ JWT token set as Claude API key in AppState during startup'
          );
        } catch (appStateError) {
          console.error(
            '[JupyterAuthService] ❌ Failed to update AppState with JWT during startup:',
            appStateError
          );
        }

        console.log(
          '[JupyterAuthService] ✅ JWT initialization completed successfully'
        );
        return true;
      } else {
        console.log(
          '[JupyterAuthService] ℹ️  No JWT token found during startup initialization'
        );
      }

      console.log(
        '[JupyterAuthService] ========== JWT INITIALIZATION COMPLETED (NO TOKEN) =========='
      );
      return false;
    } catch (error) {
      console.error(
        '[JupyterAuthService] ❌ Failed to initialize JWT on startup:',
        error
      );
      console.log(
        '[JupyterAuthService] ========== JWT INITIALIZATION FAILED =========='
      );
      return false;
    }
  }

  /**
   * Decode JWT token to extract jti (JWT ID) claim
   */
  public static decodeJwtForJti(token: string): string | null {
    try {
      if (!token) {
        console.warn('[JupyterAuthService] Cannot decode empty token');
        return null;
      }

      // Use jwt.decode to decode without verification (just extract payload)
      const payload = jwtDecode(token) as any;

      if (payload && payload.jti) {
        console.log('[JupyterAuthService] Successfully extracted jti from JWT');
        return payload.jti;
      } else {
        console.warn('[JupyterAuthService] No jti found in JWT payload');
        return null;
      }
    } catch (error) {
      console.error(
        '[JupyterAuthService] Failed to decode JWT for jti:',
        error
      );
      return null;
    }
  }

  /**
   * Revoke JWT token on the server
   */
  public static async revokeJwtToken(token: string): Promise<boolean> {
    try {
      const jti = this.decodeJwtForJti(token);

      if (!jti) {
        console.warn('[JupyterAuthService] Cannot revoke token: no jti found');
        return false;
      }

      console.log('[JupyterAuthService] Revoking JWT token with jti:', jti);

      const response = await fetch(
        'https://sage.alpinex.ai:8761/device/revoke',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({ jti })
        }
      );

      if (response.ok) {
        console.log('[JupyterAuthService] ✅ JWT token revoked successfully');
        return true;
      } else {
        console.warn(
          '[JupyterAuthService] ❌ Failed to revoke JWT token:',
          response.status,
          response.statusText
        );
        return false;
      }
    } catch (error) {
      console.error('[JupyterAuthService] ❌ Error revoking JWT token:', error);
      return false;
    }
  }
}
