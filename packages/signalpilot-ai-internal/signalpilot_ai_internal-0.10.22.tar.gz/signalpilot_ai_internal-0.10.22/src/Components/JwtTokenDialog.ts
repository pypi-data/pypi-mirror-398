/**
 * Simple input dialog for JWT token entry
 */
export class JwtTokenDialog {
  /**
   * Show a dialog to collect JWT token
   */
  public async showDialog(): Promise<{ accepted: boolean; value: string }> {
    // Create a modal dialog for JWT token input
    const modal = document.createElement('div');
    modal.className = 'sage-ai-modal';

    const dialog = document.createElement('div');
    dialog.className = 'sage-ai-dialog';

    const title = document.createElement('h3');
    title.textContent = 'Test Mode: Set JWT Token';
    title.className = 'sage-ai-dialog-title';

    const label = document.createElement('label');
    label.textContent = 'Enter your JWT token for testing:';
    label.className = 'sage-ai-dialog-label';

    const input = document.createElement('input');
    input.type = 'password';
    input.className = 'sage-ai-dialog-input';
    input.placeholder = 'Enter JWT token...';
    input.style.width = '100%';
    input.style.padding = '8px';
    input.style.marginBottom = '15px';
    input.style.boxSizing = 'border-box';
    input.style.border = '1px solid var(--jp-border-color2)';
    input.style.borderRadius = '4px';
    input.style.backgroundColor = 'var(--jp-layout-color1)';
    input.style.color = 'var(--jp-ui-font-color1)';

    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'sage-ai-dialog-button-container';

    const cancelButton = document.createElement('button');
    cancelButton.textContent = 'Cancel';
    cancelButton.style.padding = '8px 16px';
    cancelButton.style.marginRight = '8px';
    cancelButton.style.backgroundColor = 'var(--jp-layout-color3)';
    cancelButton.style.color = 'var(--jp-ui-font-color1)';
    cancelButton.style.border = '1px solid var(--jp-border-color2)';
    cancelButton.style.borderRadius = '4px';
    cancelButton.style.cursor = 'pointer';

    const submitButton = document.createElement('button');
    submitButton.textContent = 'Set Token';
    submitButton.className = 'sage-ai-dialog-submit-button';

    buttonContainer.appendChild(cancelButton);
    buttonContainer.appendChild(submitButton);
    dialog.appendChild(title);
    dialog.appendChild(label);
    dialog.appendChild(input);
    dialog.appendChild(buttonContainer);
    modal.appendChild(dialog);

    document.body.appendChild(modal);

    // Focus on the input field
    setTimeout(() => input.focus(), 100);

    return new Promise<{ accepted: boolean; value: string }>(resolve => {
      const cleanup = () => {
        if (document.body.contains(modal)) {
          document.body.removeChild(modal);
        }
      };

      submitButton.addEventListener('click', () => {
        const token = input.value.trim();
        cleanup();
        resolve({ accepted: true, value: token });
      });

      cancelButton.addEventListener('click', () => {
        cleanup();
        resolve({ accepted: false, value: '' });
      });

      // Handle Enter key
      input.addEventListener('keydown', event => {
        if (event.key === 'Enter') {
          event.preventDefault();
          const token = input.value.trim();
          cleanup();
          resolve({ accepted: true, value: token });
        } else if (event.key === 'Escape') {
          event.preventDefault();
          cleanup();
          resolve({ accepted: false, value: '' });
        }
      });

      // Close on outside click
      modal.addEventListener('click', event => {
        if (event.target === modal) {
          cleanup();
          resolve({ accepted: false, value: '' });
        }
      });
    });
  }
}

/**
 * Simple success/error message dialog
 */
export class MessageDialog {
  public static async showMessage(
    title: string,
    message: string,
    isError: boolean = false
  ): Promise<void> {
    const modal = document.createElement('div');
    modal.className = 'sage-ai-modal';

    const dialog = document.createElement('div');
    dialog.className = 'sage-ai-dialog';

    const titleElement = document.createElement('h3');
    titleElement.textContent = title;
    titleElement.className = 'sage-ai-dialog-title';
    if (isError) {
      titleElement.style.color = 'var(--jp-error-color1)';
    }

    const messageElement = document.createElement('div');
    messageElement.textContent = message;
    messageElement.className = 'sage-ai-dialog-label';
    messageElement.style.marginBottom = '20px';

    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'sage-ai-dialog-button-container';

    const okButton = document.createElement('button');
    okButton.textContent = 'OK';
    okButton.className = isError
      ? 'sage-ai-dialog-error-button'
      : 'sage-ai-dialog-submit-button';
    if (isError) {
      okButton.style.backgroundColor = 'var(--jp-error-color1)';
    }

    buttonContainer.appendChild(okButton);
    dialog.appendChild(titleElement);
    dialog.appendChild(messageElement);
    dialog.appendChild(buttonContainer);
    modal.appendChild(dialog);

    document.body.appendChild(modal);

    return new Promise<void>(resolve => {
      const cleanup = () => {
        if (document.body.contains(modal)) {
          document.body.removeChild(modal);
        }
      };

      okButton.addEventListener('click', () => {
        cleanup();
        resolve();
      });

      // Handle Enter key or Escape key
      document.addEventListener('keydown', function handleKeydown(event) {
        if (event.key === 'Enter' || event.key === 'Escape') {
          event.preventDefault();
          document.removeEventListener('keydown', handleKeydown);
          cleanup();
          resolve();
        }
      });

      // Close on outside click
      modal.addEventListener('click', event => {
        if (event.target === modal) {
          cleanup();
          resolve();
        }
      });
    });
  }
}
