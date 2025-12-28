import * as React from 'react';
import { Modal, Button } from 'react-bootstrap';

/**
 * Props for the LoginSuccessModal component
 */
export interface ILoginSuccessModalProps {
  isVisible: boolean;
  onClose: () => void;
}

/**
 * Beautiful login success modal that shows after successful JWT exchange
 */
export function LoginSuccessModal({
  isVisible,
  onClose
}: ILoginSuccessModalProps): JSX.Element | null {
  console.log('[LoginSuccessModal] Render called with isVisible:', isVisible);

  if (!isVisible) {
    console.log('[LoginSuccessModal] Not visible, returning null');
    return null;
  }

  console.log('[LoginSuccessModal] Rendering success modal');

  const handleClose = () => {
    console.log('[LoginSuccessModal] Close clicked');
    onClose();
  };

  return (
    <Modal
      show={isVisible}
      backdrop="static"
      keyboard={false}
      centered
      dialogClassName="sage-ai-login-success-modal"
    >
      <div className="sage-ai-login-success-header">
        <div className="sage-ai-login-success-icon-container">
          <div className="sage-ai-login-success-icon">
            <svg
              width="32"
              height="32"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z"
                fill="currentColor"
              />
            </svg>
          </div>
        </div>

        <h2 className="sage-ai-login-success-title">Welcome to SignalPilot!</h2>

        <p className="sage-ai-login-success-subtitle">
          You've successfully logged in and are ready to explore the future of
          AI-powered development!
        </p>
      </div>

      <Modal.Body className="sage-ai-login-success-body">
        <div className="sage-ai-login-success-content">
          <div className="sage-ai-login-success-features">
            <div className="sage-ai-login-success-tip">
              <div className="sage-ai-login-success-tip-icon">
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M8 10C8 7.79086 9.79086 6 12 6C14.2091 6 16 7.79086 16 10C16 11.8934 14.7861 13.4968 13.1197 13.8802C12.8073 13.9585 12.6064 14.2223 12.6064 14.5226V16C12.6064 16.3314 12.3378 16.6 12.0064 16.6C11.675 16.6 11.4064 16.3314 11.4064 16V14.5226C11.4064 13.8309 11.8735 13.2271 12.5535 13.0608C13.7366 12.7814 14.6 11.72 14.6 10.4C14.6 8.51177 13.0882 7 11.2 7C9.31177 7 7.8 8.51177 7.8 10.4"
                    stroke="currentColor"
                    strokeWidth="1.4"
                    strokeLinecap="round"
                  />
                  <circle cx="12" cy="19" r="1" fill="currentColor" />
                </svg>
              </div>
              <div className="sage-ai-login-success-tip-content">
                <div className="sage-ai-login-success-tip-title">
                  Start Chatting
                </div>
                <div className="sage-ai-login-success-tip-description">
                  Type in the chat box and use <code>@</code> to add context
                  from your notebooks, files, or code
                </div>
              </div>
            </div>

            <div className="sage-ai-login-success-tip">
              <div className="sage-ai-login-success-tip-icon">
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M9 11H15M9 15H15M17 21H7C5.89543 21 5 20.1046 5 19V5C5 3.89543 5.89543 3 7 3H12.5858C12.851 3 13.1054 3.10536 13.2929 3.29289L19.7071 9.70711C19.8946 9.89464 20 10.149 20 10.4142V19C20 20.1046 19.1046 21 18 21H17Z"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
              <div className="sage-ai-login-success-tip-content">
                <div className="sage-ai-login-success-tip-title">
                  Select Code & Ask
                </div>
                <div className="sage-ai-login-success-tip-description">
                  Highlight any code in your notebooks and ask Sage to explain,
                  improve, or debug it
                </div>
              </div>
            </div>

            <div className="sage-ai-login-success-tip">
              <div className="sage-ai-login-success-tip-icon">
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M13 2L3 14H12L11 22L21 10H12L13 2Z"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
              <div className="sage-ai-login-success-tip-content">
                <div className="sage-ai-login-success-tip-title">
                  AI-Powered Features
                </div>
                <div className="sage-ai-login-success-tip-description">
                  Generate code, create visualizations, analyze data, and get
                  intelligent suggestions
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="sage-ai-login-success-actions">
          <Button
            variant="primary"
            size="lg"
            className="sage-ai-login-success-start-btn"
            onClick={handleClose}
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              style={{ marginRight: '8px' }}
            >
              <path
                d="M13 2L3 14H12L11 22L21 10H12L13 2Z"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            Start Using SignalPilot
          </Button>
        </div>
      </Modal.Body>
    </Modal>
  );
}
