import * as React from 'react';
import { IDeploymentData } from '../../Services/DeploymentStateService';

type DeploymentStatus =
  | 'deployed'
  | 'uploading'
  | 'error'
  | 'idle'
  | 'not-deployed';

interface IStatusBallProps {
  status: DeploymentStatus;
  id?: string;
  title?: string;
  className?: string;
  style?: React.CSSProperties;
  onMouseEnter?: () => void;
  onMouseLeave?: () => void;
  deployment?: IDeploymentData | null;
  onDelete?: () => void | Promise<void>;
  popoverPosition?: 'left' | 'center';
}

/**
 * Small reusable status indicator ball with optional popover for deployment info.
 * - If className is provided, it will be used as-is (for CSS-driven styling).
 * - Otherwise, a sensible inline style is applied based on status.
 * - If deployment data is provided, shows a popover on hover.
 */
export const StatusBall = React.forwardRef<HTMLDivElement, IStatusBallProps>(
  (
    {
      id,
      title,
      className,
      popoverPosition,
      onMouseEnter,
      onMouseLeave,
      deployment,
      onDelete
    },
    ref
  ) => {
    const [isPopoverVisible, setIsPopoverVisible] = React.useState(false);
    const popoverRef = React.useRef<HTMLDivElement>(null);
    const ballRef = React.useRef<HTMLDivElement>(null);
    const hideTimeoutRef = React.useRef<NodeJS.Timeout | null>(null);

    // Set both refs when the ball element mounts
    const internalRef = React.useCallback(
      (node: HTMLDivElement | null) => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (ballRef as any).current = node;
        if (ref) {
          if (typeof ref === 'function') {
            ref(node);
          } else if (typeof ref === 'object' && ref !== null) {
            // For object refs, use any to bypass TypeScript's readonly check
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            (ref as any).current = node;
          }
        }
      },
      [ref]
    );

    // Cleanup timeouts
    React.useEffect(() => {
      return () => {
        if (hideTimeoutRef.current) {
          clearTimeout(hideTimeoutRef.current);
        }
      };
    }, []);

    const copyToClipboard = async (text: string): Promise<void> => {
      try {
        await navigator.clipboard.writeText(text);
      } catch (error) {
        console.error('Failed to copy:', error);
      }
    };

    const handleMouseEnter = () => {
      if (deployment) {
        if (hideTimeoutRef.current) {
          clearTimeout(hideTimeoutRef.current);
          hideTimeoutRef.current = null;
        }
        setIsPopoverVisible(true);
      }
      onMouseEnter?.();
    };

    const handleMouseLeave = () => {
      hideTimeoutRef.current = setTimeout(() => {
        if (
          !ballRef.current?.matches(':hover') &&
          !popoverRef.current?.matches(':hover')
        ) {
          setIsPopoverVisible(false);
        }
        hideTimeoutRef.current = null;
      }, 200);
      onMouseLeave?.();
    };

    return (
      <>
        {/* Popover */}
        {isPopoverVisible && deployment && (
          <div
            ref={popoverRef}
            className={`html-preview-deployment-popover ${popoverPosition}`}
            onMouseEnter={() => {
              if (hideTimeoutRef.current) {
                clearTimeout(hideTimeoutRef.current);
                hideTimeoutRef.current = null;
              }
            }}
            onMouseLeave={() => {
              hideTimeoutRef.current = setTimeout(() => {
                setIsPopoverVisible(false);
                hideTimeoutRef.current = null;
              }, 200);
            }}
          >
            <div className="html-preview-popover-label">Deploy Status:</div>
            <div className="html-preview-popover-value">✓ Deployed</div>

            <div className="html-preview-popover-label">Deployed:</div>
            <div className="html-preview-popover-value">
              {new Date(deployment.deployedAt).toLocaleString()}
            </div>

            <div
              style={{
                marginTop: '8px',
                display: 'flex',
                gap: '4px',
                flexDirection: 'column'
              }}
            >
              <button
                className="html-preview-popover-button"
                onClick={() => {
                  void copyToClipboard(deployment.deployedUrl);
                }}
              >
                Copy Link
              </button>

              <button
                className="html-preview-popover-button"
                onClick={() => {
                  window.open(deployment.deployedUrl, '_blank');
                }}
              >
                Open in New Tab
              </button>

              {onDelete && (
                <button
                  className="html-preview-popover-button html-preview-button-danger"
                  onClick={() => {
                    void onDelete();
                  }}
                >
                  Delete Deployment
                </button>
              )}
            </div>
          </div>
        )}

        {/* Status Ball */}
        <div
          ref={internalRef}
          id={id}
          title={title}
          className={className}
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
        />
      </>
    );
  }
);

StatusBall.displayName = 'StatusBall';
