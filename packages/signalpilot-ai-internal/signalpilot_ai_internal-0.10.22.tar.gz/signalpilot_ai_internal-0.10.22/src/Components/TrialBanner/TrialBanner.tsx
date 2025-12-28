import * as React from 'react';
import { JupyterAuthService } from '../../Services/JupyterAuthService';
import { IUserProfile } from '../Settings/SettingsWidget';
import { AppStateService } from '../../AppState';

interface ITrialBannerProps {
  // Optional props for future extensibility
}

// Free trial duration in days
const FREE_TRIAL_DAYS = 7;

/**
 * Calculate remaining trial days
 */
function calculateTrialDaysRemaining(createdAt: string): number {
  const createdDate = new Date(createdAt);
  const expiryDate = new Date(createdDate);
  expiryDate.setDate(expiryDate.getDate() + FREE_TRIAL_DAYS);

  const now = new Date();
  const diffMs = expiryDate.getTime() - now.getTime();
  const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

  return Math.max(0, diffDays);
}

/**
 * Beautiful trial period banner component
 * Displays at the top of the page when user is in free trial
 */
export function TrialBanner({}: ITrialBannerProps): JSX.Element | null {
  const [userProfile, setUserProfile] = React.useState<IUserProfile | null>(
    null
  );
  const [isLoading, setIsLoading] = React.useState<boolean>(true);
  const [daysRemaining, setDaysRemaining] = React.useState<number>(0);

  // Fetch user profile on mount
  React.useEffect(() => {
    const fetchUserProfile = async () => {
      try {
        const isAuth = await JupyterAuthService.isAuthenticated();
        if (!isAuth) {
          setIsLoading(false);
          return;
        }

        const profile = await JupyterAuthService.getUserProfile();
        setUserProfile(profile);

        if (profile && profile.is_free_trial && profile.created_at) {
          const days = calculateTrialDaysRemaining(profile.created_at);
          setDaysRemaining(days);
        }

        setIsLoading(false);
      } catch (error) {
        console.error('[TrialBanner] Failed to fetch user profile:', error);
        setIsLoading(false);
      }
    };

    void fetchUserProfile();
  }, []);

  // Update days remaining every minute
  React.useEffect(() => {
    if (!userProfile?.is_free_trial || !userProfile?.created_at) {
      return;
    }

    const interval = setInterval(() => {
      const days = calculateTrialDaysRemaining(userProfile.created_at);
      setDaysRemaining(days);
    }, 60000); // Update every minute

    return () => clearInterval(interval);
  }, [userProfile]);

  // Don't show if loading
  if (isLoading) {
    return null;
  }

  // Don't show if in demo mode
  if (AppStateService.isDemoMode()) {
    return null;
  }

  // Don't show if not authenticated
  if (!userProfile) {
    return null;
  }

  // Don't show if user has a subscription
  const hasSubscription = !!(
    userProfile.subscription_expiry ||
    userProfile.subscription_price_id ||
    userProfile.subscribed_at
  );

  if (hasSubscription) {
    return null;
  }

  // Don't show if not in free trial
  if (!userProfile.is_free_trial) {
    return null;
  }

  // Handle view plans click
  const handleViewPlansClick = () => {
    window.open('https://app.signalpilot.ai/subscription', '_blank');
  };

  // Color class based on days remaining
  let colorClass = 'sage-trial-banner-normal';
  if (daysRemaining <= 0) {
    colorClass = 'sage-trial-banner-expired';
  } else if (daysRemaining <= 2) {
    colorClass = 'sage-trial-banner-critical';
  } else if (daysRemaining <= 4) {
    colorClass = 'sage-trial-banner-warning';
  }

  return (
    <div className={`sage-trial-banner ${colorClass}`}>
      <div className="sage-trial-banner-content">
        <div className="sage-trial-banner-info">
          <span className="sage-trial-banner-label">
            {daysRemaining <= 0 ? 'Free Trial Ended' : 'Free Trial'}
          </span>
          <div className="sage-trial-banner-days">
            <span className="sage-trial-banner-digit">{daysRemaining}</span>
            <span className="sage-trial-banner-days-text">
              {daysRemaining === 1 ? 'day' : 'days'} remaining
            </span>
          </div>
        </div>

        <a className="sage-trial-banner-link" onClick={handleViewPlansClick}>
          View Plans
          <svg
            width="12"
            height="12"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            style={{
              marginLeft: '4px',
              display: 'inline-block',
              verticalAlign: 'middle'
            }}
          >
            <path
              d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M15 3h6v6"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M10 14L21 3"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </a>
      </div>
    </div>
  );
}
