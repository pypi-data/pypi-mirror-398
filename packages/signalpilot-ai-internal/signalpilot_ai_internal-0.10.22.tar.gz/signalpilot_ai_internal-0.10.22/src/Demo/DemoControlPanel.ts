import { Widget } from '@lumino/widgets';
import { AppStateService } from '../AppState';

/**
 * Demo Control Panel - A floating control panel for demo mode
 * Provides options to either try the demo interactively or skip to results
 */
export class DemoControlPanel extends Widget {
  private containerDiv: HTMLDivElement;
  private tryItButton: HTMLButtonElement;
  private skipButton: HTMLButtonElement;
  private onTryItCallback: () => void;
  private onSkipCallback: () => void;
  private isDemoFinished: boolean = false;

  constructor(onTryIt: () => void, onSkip: () => void) {
    super();

    this.onTryItCallback = onTryIt;
    this.onSkipCallback = onSkip;

    this.addClass('sage-ai-demo-control-panel');
    this.addClass('hidden');
    this.node.style.display = 'none';

    // Create container
    this.containerDiv = document.createElement('div');
    this.containerDiv.className = 'sage-ai-demo-control-container';

    // Create title
    const title = document.createElement('div');
    title.className = 'sage-ai-demo-control-title';
    title.innerHTML = `
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
        <path d="M2 17l10 5 10-5"></path>
        <path d="M2 12l10 5 10-5"></path>
      </svg>
      Demo Mode
    `;

    // Create button container
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'sage-ai-demo-control-buttons';

    // Create "Takeover" button
    this.tryItButton = document.createElement('button');
    this.tryItButton.className =
      'sage-ai-demo-control-button sage-ai-demo-control-try';
    this.tryItButton.innerHTML = `
      <span>Try it Yourself</span>
    `;
    this.tryItButton.onclick = () => this.handleTryIt();

    // Create "Results" button
    this.skipButton = document.createElement('button');
    this.skipButton.className =
      'sage-ai-demo-control-button sage-ai-demo-control-skip';
    this.skipButton.innerHTML = `
      <span>Results</span>
    `;
    this.skipButton.onclick = () => this.handleSkip();

    buttonContainer.appendChild(this.tryItButton);
    buttonContainer.appendChild(this.skipButton);

    this.containerDiv.appendChild(title);
    this.containerDiv.appendChild(buttonContainer);

    this.node.appendChild(this.containerDiv);
  }

  private handleTryIt(): void {
    this.hideSkipButton();
    this.onTryItCallback();
  }

  private handleSkip(): void {
    this.hideSkipButton();
    this.onSkipCallback();
  }

  /**
   * Show the control panel
   */
  public show(): void {
    this.removeClass('hidden');
    this.node.style.display = '';
    this.node.style.opacity = '0';

    // Animate in
    requestAnimationFrame(() => {
      this.node.style.transition = 'opacity 0.3s ease';
      this.node.style.opacity = '1';
    });
  }

  /**
   * Hide the control panel
   */
  public hide(): void {
    this.addClass('hidden');
    // Ensure display is set to none when hidden
    this.node.style.display = 'none';
    // Trigger update of sibling positions in the container
    this.updateSiblingPositions();
  }

  /**
   * Hide the "Results" button
   */
  public hideSkipButton(): void {
    this.skipButton.style.display = 'none';
  }

  /**
   * Show the "Results" button
   */
  public showSkipButton(): void {
    this.skipButton.style.display = '';
  }

  /**
   * Mark the demo as finished and update button text to "Login to Chat"
   */
  public markDemoFinished(): void {
    this.isDemoFinished = true;
    this.updateButtonText();
    this.hideSkipButton();
  }

  /**
   * Update button text based on demo finished state
   */
  private updateButtonText(): void {
    if (this.isDemoFinished) {
      this.tryItButton.innerHTML = `
        <span>Login to Chat</span>
      `;
    } else {
      this.tryItButton.innerHTML = `
        <span>Try it Yourself</span>
      `;
    }
  }

  /**
   * Check if demo is finished
   */
  public getDemoFinished(): boolean {
    return this.isDemoFinished;
  }

  /**
   * Update sibling positions when this panel's visibility changes
   */
  private updateSiblingPositions(): void {
    if (this.node.parentElement) {
      const container = this.node.parentElement;
      // Check if this is the state display container
      if (container.classList.contains('sage-ai-state-display-container')) {
        // Get the chat container and update positions
        const chatContainer = AppStateService.getChatContainerSafe();
        if (chatContainer?.chatWidget?.updateDynamicBottomPositions) {
          // Use setTimeout to ensure the hidden class is applied first
          setTimeout(() => {
            chatContainer.chatWidget.updateDynamicBottomPositions();
          }, 0);
        }
      }
    }
  }

  /**
   * Attach the control panel to a container or the document
   * @param container Optional container element to attach to. If not provided, attaches to document.body for backwards compatibility.
   */
  public attach(container?: HTMLElement): void {
    if (container) {
      container.appendChild(this.node);
    } else {
      document.body.appendChild(this.node);
    }
    this.show();
  }

  /**
   * Detach the control panel from the document
   */
  public detach(): void {
    if (this.node.parentNode) {
      this.node.parentNode.removeChild(this.node);
    }
  }
}
