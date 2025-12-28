import * as React from 'react';
import { Modal, Button } from 'react-bootstrap';
import { getCurrentSessionInfo, getCurrentSlotId } from '../../sessionUtils';
import { JWTAuthModalService } from '../../Services/JWTAuthModalService';
import { JupyterAuthService } from '../../Services/JupyterAuthService';

interface ISessionData {
  slot: number;
  session_id: string;
  container: string;
  expires_at: string;
  time_remaining_minutes: number;
  duration_minutes: number;
  is_expired: boolean;
}

interface ISessionTimerBannerProps {
  onSessionExpired?: () => void;
  forceDisplay?: boolean;
}

/**
 * Beautiful animated session timer banner component
 * Displays at the top of the page as an announcement banner
 */
export function SessionTimerBanner({
  onSessionExpired,
  forceDisplay = false
}: ISessionTimerBannerProps): JSX.Element | null {
  // Initialize with placeholder data for local testing (15 minutes)
  const getPlaceholderData = (): ISessionData => {
    const mockExpiry = new Date();
    mockExpiry.setMinutes(mockExpiry.getMinutes() + 15);
    return {
      slot: 0,
      session_id: 'local-test-session',
      container: 'local-container',
      expires_at: mockExpiry.toISOString(),
      time_remaining_minutes: 15,
      duration_minutes: 60,
      is_expired: false
    };
  };

  const [sessionData, setSessionData] =
    React.useState<ISessionData>(getPlaceholderData());
  const [timeRemaining, setTimeRemaining] = React.useState<number>(15);
  const [isLoading, setIsLoading] = React.useState<boolean>(true);
  const [isExpired, setIsExpired] = React.useState<boolean>(false);
  const [error, setError] = React.useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = React.useState<boolean>(false);
  const [hasSlotId, setHasSlotId] = React.useState<boolean>(false);

  // Check if we have a slot ID (cloud session)
  React.useEffect(() => {
    const slotId = getCurrentSlotId();
    setHasSlotId(slotId !== null);
    console.log(
      '[SessionTimerBanner] Slot ID check:',
      slotId,
      'hasSlotId:',
      slotId !== null,
      'forceDisplay:',
      forceDisplay
    );
  }, [forceDisplay]);

  // Check authentication status on mount
  React.useEffect(() => {
    const checkAuth = async () => {
      const authenticated = await JupyterAuthService.isAuthenticated();
      setIsAuthenticated(authenticated);
    };
    void checkAuth();
  }, []);

  // Format time remaining as MM:SS
  const formatTime = (
    minutes: number
  ): { minutes: number; seconds: number } => {
    const totalSeconds = Math.max(0, Math.floor(minutes * 60));
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return { minutes: mins, seconds: secs };
  };

  // Fetch session data
  const fetchSessionData = React.useCallback(async () => {
    try {
      const data = await getCurrentSessionInfo();

      if (!data) {
        // Use placeholder data for testing when not in cloud session
        console.log(
          '[SessionTimerBanner] No session data from endpoint, using placeholder (15 minutes)'
        );
        const placeholderData = getPlaceholderData();
        setSessionData(placeholderData);
        setTimeRemaining(15);
        setIsLoading(false);
        setError(null);
        return;
      }

      setSessionData(data);
      setTimeRemaining(data.time_remaining_minutes);

      if (data.is_expired) {
        setIsExpired(true);
        if (onSessionExpired) {
          onSessionExpired();
        }
      }

      setIsLoading(false);
      setError(null);
    } catch (err) {
      console.error('[SessionTimerBanner] Error fetching session data:', err);
      // Use placeholder data on error as well
      const placeholderData = getPlaceholderData();
      setSessionData(placeholderData);
      setTimeRemaining(15);
      setIsLoading(false);
      setError(null);
    }
  }, [onSessionExpired]);

  // Initial fetch on mount
  React.useEffect(() => {
    void fetchSessionData();
  }, [fetchSessionData]);

  // Countdown timer - update every second
  React.useEffect(() => {
    if (!sessionData) {
      return;
    }

    const interval = setInterval(() => {
      setTimeRemaining(prev => {
        const newTime = prev - 1 / 60; // Decrease by 1 second

        if (newTime <= 0) {
          setIsExpired(true);
          if (onSessionExpired) {
            onSessionExpired();
          }
          return 0;
        }

        return newTime;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [sessionData, onSessionExpired]);

  // Periodic refresh from server (every 30 seconds)
  React.useEffect(() => {
    const interval = setInterval(() => {
      void fetchSessionData();
    }, 30000); // 30 seconds

    return () => clearInterval(interval);
  }, [fetchSessionData]);

  console.log(
    '[SessionTimerBanner] Rendering timer banner - hasSlotId:',
    hasSlotId,
    'forceDisplay:',
    forceDisplay
  );

  // Show loading state only if we're still initially loading
  // After initial load, we'll always have sessionData (either from backend or placeholder)
  if (isLoading) {
    // Show loading state while fetching
    return (
      <div className="sage-timer-banner sage-timer-banner-normal">
        <div className="sage-timer-banner-content">
          <div className="sage-timer-banner-info">
            <span className="sage-timer-banner-label">
              Loading session information...
            </span>
          </div>
        </div>
      </div>
    );
  }

  // At this point, we should always have sessionData (either from backend or placeholder)
  if (!sessionData) {
    console.warn(
      '[SessionTimerBanner] No session data available after loading'
    );
    return null;
  }

  const { minutes, seconds } = formatTime(timeRemaining);
  const percentRemaining = (timeRemaining / sessionData.duration_minutes) * 100;

  // Color based on time remaining
  let colorClass = 'sage-timer-banner-normal';
  if (isExpired || percentRemaining <= 0) {
    colorClass = 'sage-timer-banner-critical';
  } else if (percentRemaining < 20) {
    colorClass = 'sage-timer-banner-critical';
  } else if (percentRemaining < 50) {
    colorClass = 'sage-timer-banner-warning';
  }

  // Handler for signup/takeover
  const handleSignupClick = () => {
    console.log(
      '[SessionTimerBanner] Signup for Free clicked - showing auth modal'
    );
    const jwtModalService = JWTAuthModalService.getInstance();
    jwtModalService.show();
  };

  return (
    <div className={`sage-timer-banner ${colorClass}`}>
      <div className="sage-timer-banner-content">
        <div className="sage-timer-banner-icon">
          <svg
            className="sage-timer-banner-icon-svg"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <circle
              cx="12"
              cy="13"
              r="9"
              stroke="currentColor"
              strokeWidth="2"
            />
            <path
              d="M12 8v5l3 3"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            />
            <path
              d="M9 2h6"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
        </div>

        <div className="sage-timer-banner-info">
          <span className="sage-timer-banner-label">
            {isExpired ? 'Session Expired' : 'Session Time Remaining'}
          </span>
          <div className="sage-timer-banner-time">
            <span className="sage-timer-banner-digit">
              {String(minutes).padStart(2, '0')}
            </span>
            <span className="sage-timer-banner-separator">:</span>
            <span className="sage-timer-banner-digit">
              {String(seconds).padStart(2, '0')}
            </span>
          </div>
        </div>

        <div className="sage-timer-banner-progress-wrapper">
          <div className="sage-timer-banner-progress-bar">
            <div
              className="sage-timer-banner-progress-fill"
              style={{ width: `${percentRemaining}%` }}
            />
          </div>
          <span className="sage-timer-banner-expiry">
            {isExpired
              ? 'Session has ended'
              : `Expires at ${(() => {
                  // Calculate expiry time by adding time remaining to current browser time
                  const expiryTime = new Date();
                  expiryTime.setSeconds(
                    expiryTime.getSeconds() + Math.floor(timeRemaining * 60)
                  );
                  return expiryTime.toLocaleTimeString(undefined, {
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                    hour12: true
                  });
                })()}`}
          </span>
        </div>

        <div className="sage-timer-banner-demo-mode">
          {isAuthenticated ? (
            <>
              <span className="sage-timer-banner-demo-mode-text">
                SignalPilot Demo Mode
              </span>
              <span className="sage-timer-banner-demo-mode-icon">❓</span>
              <div className="sage-timer-banner-tooltip">
                You are currently using SignalPilot in demo mode. To access
                extended session times, please log in. For an unlimited one-week
                trial, download and run the local version.
              </div>
            </>
          ) : (
            <>
              <span className="sage-timer-banner-demo-mode-text">
                <b
                  onClick={handleSignupClick}
                  style={{ cursor: 'pointer', textDecoration: 'underline' }}
                >
                  Signup for Free
                </b>{' '}
                to Take Over and Try All Features
              </span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Session expired modal using react-bootstrap
 */
export function SessionExpiredModal({
  show,
  onExit
}: {
  show: boolean;
  onExit: () => void;
}): JSX.Element {
  const handleExit = () => {
    window.location.href = 'https://signalpilot.ai/';
  };

  return (
    <Modal
      show={show}
      onHide={handleExit}
      centered
      backdrop="static"
      keyboard={false}
      className="sage-session-expired-modal"
    >
      <Modal.Body className="sage-session-expired-body">
        <div className="sage-session-expired-icon-wrapper">
          <svg
            className="sage-session-expired-icon"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <circle
              cx="12"
              cy="13"
              r="9"
              stroke="currentColor"
              strokeWidth="2.5"
            />
            <path
              d="M12 8v5l3 3"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M9 2h6"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
            />
            <path
              d="M16 4l2 2M6 6l2-2"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
        </div>

        <Modal.Title className="sage-session-expired-title">
          Session Expired
        </Modal.Title>

        <p className="sage-session-expired-message">
          Your session has expired. Please return to the main site to start a
          new session.
        </p>

        <div className="sage-session-expired-actions">
          <Button
            variant="primary"
            size="lg"
            onClick={handleExit}
            className="sage-session-expired-button"
          >
            Return to SignalPilot.ai
          </Button>
        </div>
      </Modal.Body>
    </Modal>
  );
}
