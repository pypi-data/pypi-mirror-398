import * as React from 'react';

interface IReplayLoadingOverlayProps {
  isVisible: boolean;
  isFadingOut?: boolean;
  message?: string;
}

/**
 * Full-page loading overlay for replay mode
 * Shows "Loading SignalPilot demo..." with an animated spinner
 * Optionally displays a user message below the loading text
 */
export function ReplayLoadingOverlay({
  isVisible,
  isFadingOut = false,
  message
}: IReplayLoadingOverlayProps): JSX.Element | null {
  const [shouldRender, setShouldRender] = React.useState(isVisible);

  React.useEffect(() => {
    if (isVisible) {
      setShouldRender(true);
    } else if (isFadingOut) {
      // Keep rendering during fade-out, remove after animation completes
      const timer = setTimeout(() => {
        setShouldRender(false);
      }, 600); // Match fade-out duration
      return () => clearTimeout(timer);
    } else {
      setShouldRender(false);
    }
  }, [isVisible, isFadingOut]);

  if (!shouldRender) {
    return null;
  }

  const overlayClassName = `sage-replay-loading-overlay ${
    isFadingOut ? 'fade-out' : ''
  } ${isVisible && !isFadingOut ? 'fade-in' : ''}`;

  return (
    <div className={overlayClassName}>
      <div className="sage-replay-loading-content">
        <div className="sage-replay-loading-spinner-container">
          <div className="sage-replay-loading-spinner">
            <svg
              className="sage-replay-spinner-svg"
              viewBox="0 0 50 50"
              xmlns="http://www.w3.org/2000/svg"
            >
              <circle
                className="sage-replay-spinner-path"
                cx="25"
                cy="25"
                r="20"
                fill="none"
                strokeWidth="3"
              />
            </svg>
          </div>
          <div className="sage-replay-loading-pulse-ring"></div>
        </div>
        <div className="sage-replay-loading-text">
          <span className="sage-replay-loading-text-main">Loading SignalPilot demo</span>
          <span className="sage-replay-loading-dots">
            <span>.</span>
            <span>.</span>
            <span>.</span>
          </span>
        </div>
        {message && (
          <div className="sage-replay-loading-message">
            <div className="sage-replay-loading-message-label">Your prompt:</div>
            <div className="sage-replay-loading-message-text">{message}</div>
          </div>
        )}
      </div>
    </div>
  );
}
