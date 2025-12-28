import * as React from 'react';

/**
 * Props for the LoginSuccessToast component
 */
export interface ILoginSuccessToastProps {
  isVisible: boolean;
  onClose: () => void;
}

/**
 * Simple success toast that shows "Login Successful" for 5 seconds
 */
export function LoginSuccessToast({
  isVisible,
  onClose
}: ILoginSuccessToastProps): JSX.Element | null {
  React.useEffect(() => {
    if (isVisible) {
      // Auto-hide after 5 seconds
      const timer = setTimeout(() => {
        onClose();
      }, 5000);

      return () => clearTimeout(timer);
    }
  }, [isVisible, onClose]);

  if (!isVisible) {
    return null;
  }

  return (
    <div className="sage-login-success-toast">
      <svg
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="sage-login-success-toast-icon"
      >
        <path
          d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z"
          fill="currentColor"
        />
      </svg>
      <span className="sage-login-success-toast-text">Login Successful</span>
    </div>
  );
}
