import * as React from 'react';
import { Modal, Button } from 'react-bootstrap';

/**
 * Props for the FirstRunModal component
 */
export interface IFirstRunModalProps {
  isVisible: boolean;
  onGetStarted: () => void;
  onAlreadyHaveAccount: () => void;
  onNotNow?: () => void;
}

/**
 * First-run modal component that appears when API key is not set
 */
export function FirstRunModal({
  isVisible,
  onGetStarted,
  onAlreadyHaveAccount,
  onNotNow
}: IFirstRunModalProps): JSX.Element | null {
  console.log('[FirstRunModal] Render called with isVisible:', isVisible);

  if (!isVisible) {
    console.log('[FirstRunModal] Not visible, returning null');
    return null;
  }

  console.log('[FirstRunModal] Rendering modal');

  const handleGetStarted = () => {
    console.log('[FirstRunModal] Get started clicked');
    onGetStarted();
  };

  const handleAlreadyHaveAccount = () => {
    console.log('[FirstRunModal] Already have account clicked');
    onAlreadyHaveAccount();
  };

  const handleNotNow = () => {
    console.log('[FirstRunModal] Not now clicked');
    if (onNotNow) {
      onNotNow();
    }
  };

  return (
    <Modal
      show={isVisible}
      backdrop="static"
      keyboard={false}
      centered
      dialogClassName="sage-ai-first-run-modal"
    >
      <Modal.Header className="sage-ai-first-run-header">
        <Modal.Title className="sage-ai-first-run-title">
          Let's get you set up
        </Modal.Title>
      </Modal.Header>

      <Modal.Body className="sage-ai-first-run-body">
        <p className="sage-ai-first-run-message">
          SignalPilot needs an account to activate.
        </p>

        <div className="sage-ai-first-run-actions">
          <Button
            variant="primary"
            size="lg"
            className="sage-ai-first-run-primary-btn"
            onClick={handleGetStarted}
          >
            Get started
          </Button>

          <Button
            variant="link"
            className="sage-ai-first-run-secondary-btn"
            onClick={handleAlreadyHaveAccount}
          >
            I already have an account
          </Button>
        </div>

        {onNotNow && (
          <div className="sage-ai-first-run-not-now">
            <Button
              variant="outline-secondary"
              size="sm"
              className="sage-ai-first-run-not-now-btn"
              onClick={handleNotNow}
            >
              Not now
            </Button>
          </div>
        )}
      </Modal.Body>
    </Modal>
  );
}
