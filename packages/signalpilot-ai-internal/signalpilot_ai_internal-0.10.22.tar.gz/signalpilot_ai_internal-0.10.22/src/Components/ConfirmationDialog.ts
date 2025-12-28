/**
 * Reusable confirmation dialog component
 */
export class ConfirmationDialog {
  public static async showConfirmation(
    title: string,
    message: string,
    confirmButtonText: string = 'Confirm',
    cancelButtonText: string = 'Cancel'
  ): Promise<boolean> {
    const modal = document.createElement('div');
    modal.className = 'sage-ai-modal';

    const dialog = document.createElement('div');
    dialog.className = 'sage-ai-dialog';

    const titleElement = document.createElement('h3');
    titleElement.textContent = title;
    titleElement.className = 'sage-ai-dialog-title';

    const messageElement = document.createElement('div');
    messageElement.textContent = message;
    messageElement.className = 'sage-ai-dialog-label';
    messageElement.style.marginBottom = '20px';

    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'sage-ai-dialog-button-container';

    const cancelButton = document.createElement('button');
    cancelButton.textContent = cancelButtonText;
    cancelButton.className = 'sage-ai-dialog-cancel-button';
    cancelButton.style.marginRight = '10px';
    cancelButton.style.border = '0';

    const confirmButton = document.createElement('button');
    confirmButton.textContent = confirmButtonText;
    confirmButton.className = 'sage-ai-dialog-submit-button';

    buttonContainer.appendChild(cancelButton);
    buttonContainer.appendChild(confirmButton);
    dialog.appendChild(titleElement);
    dialog.appendChild(messageElement);
    dialog.appendChild(buttonContainer);
    modal.appendChild(dialog);

    document.body.appendChild(modal);

    return new Promise<boolean>(resolve => {
      const cleanup = () => {
        if (document.body.contains(modal)) {
          document.body.removeChild(modal);
        }
      };

      const handleConfirm = () => {
        cleanup();
        resolve(true);
      };

      const handleCancel = () => {
        cleanup();
        resolve(false);
      };

      confirmButton.addEventListener('click', handleConfirm);
      cancelButton.addEventListener('click', handleCancel);

      // Handle keyboard shortcuts
      const handleKeydown = (event: KeyboardEvent) => {
        if (event.key === 'Enter') {
          event.preventDefault();
          document.removeEventListener('keydown', handleKeydown);
          handleConfirm();
        } else if (event.key === 'Escape') {
          event.preventDefault();
          document.removeEventListener('keydown', handleKeydown);
          handleCancel();
        }
      };

      document.addEventListener('keydown', handleKeydown);

      // Close on outside click
      modal.addEventListener('click', event => {
        if (event.target === modal) {
          handleCancel();
        }
      });

      // Focus the confirm button for better UX
      setTimeout(() => {
        confirmButton.focus();
      }, 100);
    });
  }
}
