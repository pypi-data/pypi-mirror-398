/**
 * Utility for managing replayId persistence in localStorage
 * and URL reconstruction
 */

const REPLAY_ID_STORAGE_KEY = 'sage-replay-id';
const TAKEOVER_MODE_STORAGE_KEY = 'sage-takeover-mode';
const TAKEOVER_REPLAY_DATA_KEY = 'sage-takeover-replay-data';
const LAST_NOTEBOOK_PATH_KEY = 'sage-last-notebook-path';

/**
 * Get the stored replayId from localStorage
 */
export function getStoredReplayId(): string | null {
  try {
    return localStorage.getItem(REPLAY_ID_STORAGE_KEY);
  } catch (error) {
    console.warn('[ReplayIdManager] Failed to get stored replayId:', error);
    return null;
  }
}

/**
 * Store replayId in localStorage
 */
export function storeReplayId(replayId: string): void {
  try {
    localStorage.setItem(REPLAY_ID_STORAGE_KEY, replayId);
    console.log('[ReplayIdManager] Stored replayId:', replayId);
  } catch (error) {
    console.warn('[ReplayIdManager] Failed to store replayId:', error);
  }
}

/**
 * Remove replayId from localStorage
 */
export function removeStoredReplayId(): void {
  try {
    localStorage.removeItem(REPLAY_ID_STORAGE_KEY);
    console.log('[ReplayIdManager] Removed stored replayId');
  } catch (error) {
    console.warn('[ReplayIdManager] Failed to remove stored replayId:', error);
  }
}



/**
 * Get replayId from URL parameters
 */
export function getReplayIdFromUrl(): string | null {
  try {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('replay');
  } catch (error) {
    console.warn('[ReplayIdManager] Failed to get replayId from URL:', error);
    return null;
  }
}

/**
 * Initialize replayId management:
 * - If replayId is in URL, store it in localStorage
 * - Returns the replayId from URL or localStorage
 */
export async function initializeReplayIdManagement(): Promise<string | null> {
  const urlReplayId = getReplayIdFromUrl();
  const storedReplayId = getStoredReplayId();

  if (urlReplayId) {
    // New replayId in URL - update localStorage
    if (urlReplayId !== storedReplayId) {
      storeReplayId(urlReplayId);
      console.log(
        '[ReplayIdManager] Updated stored replayId from URL:',
        urlReplayId
      );
    }
    return urlReplayId;
  } else if (storedReplayId) {
    // ReplayId exists in localStorage
    console.log(
      '[ReplayIdManager] ReplayId exists in localStorage:',
      storedReplayId
    );
    return storedReplayId;
  }

  return null;
}

/**
 * Takeover mode utilities
 */

/**
 * Check if takeover mode is enabled
 */
export function isTakeoverModeEnabled(): boolean {
  try {
    return localStorage.getItem(TAKEOVER_MODE_STORAGE_KEY) === 'true';
  } catch (error) {
    console.warn('[ReplayIdManager] Failed to check takeover mode:', error);
    return false;
  }
}

/**
 * Enable takeover mode and store the demo data for later use
 */
export function enableTakeoverMode(replayData: { messages: any; replayId: string }): void {
  try {
    localStorage.setItem(TAKEOVER_MODE_STORAGE_KEY, 'true');
    localStorage.setItem(TAKEOVER_REPLAY_DATA_KEY, JSON.stringify(replayData));
    console.log('[ReplayIdManager] Takeover mode enabled with replay data');
  } catch (error) {
    console.warn('[ReplayIdManager] Failed to enable takeover mode:', error);
  }
}

/**
 * Get the stored takeover replay data
 */
export function getTakeoverReplayData(): { messages: any; replayId: string } | null {
  try {
    const dataStr = localStorage.getItem(TAKEOVER_REPLAY_DATA_KEY);
    if (!dataStr) return null;
    return JSON.parse(dataStr);
  } catch (error) {
    console.warn('[ReplayIdManager] Failed to get takeover replay data:', error);
    return null;
  }
}

/**
 * Disable takeover mode and clear all related data
 */
export function disableTakeoverMode(): void {
  try {
    localStorage.removeItem(TAKEOVER_MODE_STORAGE_KEY);
    localStorage.removeItem(TAKEOVER_REPLAY_DATA_KEY);
    console.log('[ReplayIdManager] Takeover mode disabled and data cleared');
  } catch (error) {
    console.warn('[ReplayIdManager] Failed to disable takeover mode:', error);
  }
}

/**
 * Last notebook path utilities
 */

/**
 * Store the last notebook path in localStorage
 */
export function storeLastNotebookPath(notebookPath: string): void {
  try {
    localStorage.setItem(LAST_NOTEBOOK_PATH_KEY, notebookPath);
    console.log('[ReplayIdManager] Stored last notebook path:', notebookPath);
  } catch (error) {
    console.warn('[ReplayIdManager] Failed to store last notebook path:', error);
  }
}

/**
 * Get the stored last notebook path from localStorage
 */
export function getStoredLastNotebookPath(): string | null {
  try {
    return localStorage.getItem(LAST_NOTEBOOK_PATH_KEY);
  } catch (error) {
    console.warn('[ReplayIdManager] Failed to get stored last notebook path:', error);
    return null;
  }
}

/**
 * Remove the stored last notebook path from localStorage
 */
export function removeStoredLastNotebookPath(): void {
  try {
    localStorage.removeItem(LAST_NOTEBOOK_PATH_KEY);
    console.log('[ReplayIdManager] Removed stored last notebook path');
  } catch (error) {
    console.warn('[ReplayIdManager] Failed to remove stored last notebook path:', error);
  }
}
