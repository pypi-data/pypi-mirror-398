/**
 * Session utilities for managing Jupyter Lab session timeouts with the cloud demo pool manager
 *
 * This module provides functions to interact with the pool manager API to extend session durations
 * after user authentication and during active usage.
 */

import { AppStateService } from './AppState';

// Pool manager API endpoint - use relative path to work with nginx proxy
const POOL_MANAGER_API_URL = '/api';

/**
 * Extract the slot ID from the current Jupyter Lab URL
 *
 * Examples:
 * - http://localhost/user0/lab/tree/Untitled.ipynb -> 0
 * - http://localhost/user42/lab -> 42
 * - http://example.com/user15/lab/workspaces/auto-v -> 15
 *
 * @returns The slot ID number, or null if not found
 */
export function getCurrentSlotId(): number | null {
  try {
    const url = window.location.href;

    // Match pattern: /userN/ where N is one or more digits
    const match = url.match(/\/user(\d+)\//);

    if (match && match[1]) {
      const slotId = parseInt(match[1], 10);
      console.log(
        `[SessionUtils] Extracted slot ID: ${slotId} from URL: ${url}`
      );
      return slotId;
    }

    console.warn('[SessionUtils] Could not extract slot ID from URL:', url);
    return null;
  } catch (error) {
    console.error('[SessionUtils] Error extracting slot ID:', error);
    return null;
  }
}

/**
 * Get session information from the pool manager
 *
 * @param slotId The slot ID (container number)
 * @returns Session information including expiry time
 */
export async function getSessionInfo(slotId: number): Promise<any> {
  try {
    const response = await fetch(`${POOL_MANAGER_API_URL}/session/${slotId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(
        `Failed to get session info: ${response.status} ${errorText}`
      );
    }

    const data = await response.json();
    console.log('[SessionUtils] Session info retrieved:', data);
    return data;
  } catch (error) {
    console.error('[SessionUtils] Error getting session info:', error);
    throw error;
  }
}

/**
 * Extend the session expiry time
 *
 * @param slotId The slot ID (container number)
 * @param extendByMinutes Number of minutes to extend the session by
 * @returns Updated session information
 */
export async function extendSessionExpiry(
  slotId: number,
  extendByMinutes: number
): Promise<any> {
  try {
    console.log(
      `[SessionUtils] Extending session ${slotId} by ${extendByMinutes} minutes`
    );

    const response = await fetch(
      `${POOL_MANAGER_API_URL}/session/${slotId}/expiry`,
      {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          extend_by_minutes: extendByMinutes
        })
      }
    );

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(
        `Failed to extend session: ${response.status} ${errorText}`
      );
    }

    const data = await response.json();
    console.log('[SessionUtils] Session extended successfully:', data);
    return data;
  } catch (error) {
    console.error('[SessionUtils] Error extending session:', error);
    throw error;
  }
}

/**
 * Set session timeout to 60 minutes after authentication
 *
 * This should be called after successful user authentication.
 * Default sessions start at 15 minutes, so we extend by 45 minutes to reach 60 total.
 *
 * @returns Session information after extension, or null if failed
 */
export async function setSessionTimeoutAfterAuth(): Promise<any | null> {
  try {
    const slotId = getCurrentSlotId();

    if (slotId === null) {
      console.warn(
        '[SessionUtils] Cannot set session timeout - no slot ID found'
      );
      return null;
    }

    console.log(
      `[SessionUtils] Setting session timeout to 60 minutes for slot ${slotId} after authentication`
    );

    // Default session is 15 minutes, extend by 45 to reach 60 total
    const result = await extendSessionExpiry(slotId, 45);

    console.log(
      '[SessionUtils] Session timeout set to 60 minutes successfully:',
      result
    );

    return result;
  } catch (error) {
    console.error(
      '[SessionUtils] Failed to set session timeout after authentication:',
      error
    );
    return null;
  }
}

/**
 * Extend current session by specified minutes
 *
 * This can be called on user activity to keep the session alive.
 *
 * @param extendByMinutes Number of minutes to extend (default: 15)
 * @returns Session information after extension, or null if failed
 */
export async function extendCurrentSession(
  extendByMinutes: number = 15
): Promise<any | null> {
  try {
    const slotId = getCurrentSlotId();

    if (slotId === null) {
      console.warn('[SessionUtils] Cannot extend session - no slot ID found');
      return null;
    }

    console.log(
      `[SessionUtils] Extending current session ${slotId} by ${extendByMinutes} minutes`
    );

    const result = await extendSessionExpiry(slotId, extendByMinutes);

    console.log('[SessionUtils] Session extended successfully:', result);

    return result;
  } catch (error) {
    console.error('[SessionUtils] Failed to extend current session:', error);
    return null;
  }
}

/**
 * Get information about the current session
 *
 * @returns Session information, or null if failed
 */
export async function getCurrentSessionInfo(): Promise<any | null> {
  const slotId = getCurrentSlotId();

  if (slotId === null) {
    console.warn('[SessionUtils] Cannot get session info - no slot ID found');
    return null;
  }

  try {
    const info = await getSessionInfo(slotId);
    return info;
  } catch (error) {
    console.error('[SessionUtils] Failed to get current session info:', error);
    
    // Check if this is a slot_not_in_use error (session expired)
    const errorMessage = error instanceof Error ? error.message : String(error);
    if (errorMessage.includes('slot_not_in_use')) {
      console.log('[SessionUtils] Slot not in use - session has expired');
      // Return a special object indicating the session is expired
      // This will trigger the session expired modal in the banner
      return {
        is_expired: true,
        slot: slotId,
        session_id: '',
        container: '',
        expires_at: new Date().toISOString(),
        time_remaining_minutes: 0,
        duration_minutes: 0
      };
    }
    
    return null;
  }
}

/**
 * Check if the current environment is a cloud demo session
 *
 * @returns true if running in a cloud demo container (URL contains /userN/)
 */
export function isCloudDemoSession(): boolean {
  const slotId = getCurrentSlotId();
  return slotId !== null;
}

/**
 * Check if the session timer banner should be displayed
 * 
 * The banner should be shown when:
 * - We are in demo mode (replay parameter is present), OR
 * - We are on the demo version (user0 is present in the URL)
 * - Or when manually triggered via a command (handled separately in commands.ts)
 * 
 * @returns true if the banner should be displayed automatically
 */
export function shouldShowSessionTimerBanner(): boolean {
  // Check if we're in demo mode (replay)
  const isDemoMode = AppStateService.isDemoMode();
  console.log('[SessionUtils] Checking if timer banner should show - isDemoMode:', isDemoMode);
  
  if (isDemoMode) {
    console.log('[SessionUtils] Timer banner should show - demo mode is active');
    return true;
  }
  
  // Check if we're on user0 (demo/live deployed version)
  const slotId = getCurrentSlotId();
  console.log('[SessionUtils] Checking slot ID:', slotId);
  const shouldShow = slotId === 0;
  console.log('[SessionUtils] Timer banner should show based on slot ID:', shouldShow);
  return shouldShow;
}
