import { JupyterFrontEnd } from '@jupyterlab/application';
import { ICommandPalette } from '@jupyterlab/apputils';
import { AppStateService } from './AppState';
import { DatabaseType } from './DatabaseStateService';
import {
  POSTGRESQL_ICON,
  MYSQL_ICON,
  SNOWFLAKE_ICON
} from './Components/databaseIcons';

// LocalStorage key for CTA collapsed state
const CTA_COLLAPSED_KEY = 'sage-ai-cta-collapsed';

/**
 * Register the add CTA div command for the Welcome to Your AI Data Assistant interface
 */
export function registerAddCtaDivCommand(
  app: JupyterFrontEnd,
  palette: ICommandPalette
): void {
  const addCtaDivCommand: string = 'sage-ai:add-cta-div';

  app.commands.addCommand(addCtaDivCommand, {
    label: 'Add CTA Div to Notebook',
    isVisible: () => false,
    execute: async () => {
      try {
        // Get the current notebook tracker
        const notebookTracker = AppStateService.getNotebookTracker();
        const currentNotebook = notebookTracker.currentWidget;

        if (!currentNotebook) {
          console.log('No active notebook found');
          return;
        }

        // Check if CTA already exists in the current notebook
        const existingCta = currentNotebook.node.querySelector(
          '.sage-ai-data-cta-container'
        );
        if (existingCta) {
          console.log(
            '[WelcomeCTA] CTA already exists in this notebook, skipping render'
          );
          return;
        }

        // Create the main CTA container
        const ctaContainer = document.createElement('div');
        ctaContainer.className = 'sage-ai-data-cta-container';

        // Check localStorage for collapsed state
        // In demo mode, default to collapsed
        const isDemoMode = AppStateService.isDemoMode();
        const isCollapsed =
          isDemoMode || localStorage.getItem(CTA_COLLAPSED_KEY) === 'true';

        // Create the HTML structure with modern, card-based design
        ctaContainer.innerHTML = `
          <div class="sage-ai-data-cta-content">
          <div class="sage-ai-data-cta-header">
            <h3 class="sage-ai-data-cta-title">
            Welcome to SignalPilot!</h3>
            <div class="sage-ai-data-cta-subtitle">Let's get started by asking a question or connecting your data</div>
          </div>
          
          <div class="sage-ai-data-cta-chat-section">
            <div class="sage-ai-data-cta-chat-label">
              <svg class="chat-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span>Ask a Question</span>
            </div>
            <div class="sage-ai-data-cta-chat-wrapper">
              <textarea 
                class="sage-ai-data-cta-input" 
                placeholder="What would you like to know? Ask me anything about your data, analytics, or insights..."
                rows="1"
              ></textarea>
              <button class="sage-ai-data-cta-send-btn" title="Send message (Enter)">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                  <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
            </div>
          </div>
          
          <div class="sage-ai-data-connect-section">
            <div class="sage-ai-data-section-title">
              <svg class="section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <polyline points="13 2 13 9 20 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span>Connect Your Data</span>
            </div>
            
            <div class="sage-ai-data-files-card" role="button" tabindex="0">
              <div class="card-icon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <div class="card-content">
                <div class="card-title">Add Files to /data</div>
                <div class="card-description">Upload CSV, JSON, Excel, Parquet and more</div>
              </div>
              <div class="card-arrow">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M9 18l6-6-6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
            </div>
            
            <div class="sage-ai-data-db-section">
              <div class="sage-ai-data-db-label">Connect to Database</div>
              <div class="sage-ai-data-db-grid">
                <div class="sage-ai-data-db-card postgresql" data-db-type="postgresql" role="button" tabindex="0">
                  <div class="db-card-header">
                    <span class="db-icon">${POSTGRESQL_ICON.element({ tag: 'span' }).outerHTML}</span>
                    <div class="db-name">PostgreSQL</div>
                  </div>
                  <div class="db-description">Powerful relational database</div>
                </div>
                
                <div class="sage-ai-data-db-card mysql" data-db-type="mysql" role="button" tabindex="0">
                  <div class="db-card-header">
                    <span class="db-icon">${MYSQL_ICON.element({ tag: 'span' }).outerHTML}</span>
                    <div class="db-name">MySQL</div>
                  </div>
                  <div class="db-description">Popular open-source DB</div>
                </div>
                
                <div class="sage-ai-data-db-card snowflake" data-db-type="snowflake" role="button" tabindex="0">
                  <div class="db-card-header">
                    <span class="db-icon">${SNOWFLAKE_ICON.element({ tag: 'span' }).outerHTML}</span>
                    <div class="db-name">Snowflake</div>
                  </div>
                  <div class="db-description">Cloud data warehouse</div>
                </div>
              </div>
            </div>
          </div>
          </div>
          <button class="sage-ai-data-cta-toggle" title="Collapse" aria-label="Toggle CTA visibility">
            <svg class="toggle-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M18 15l-6-6-6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        `;

        // Get references to interactive elements
        const inputField = ctaContainer.querySelector(
          '.sage-ai-data-cta-input'
        ) as HTMLTextAreaElement;
        const sendButton = ctaContainer.querySelector(
          '.sage-ai-data-cta-send-btn'
        ) as HTMLButtonElement;
        const filesCard = ctaContainer.querySelector(
          '.sage-ai-data-files-card'
        ) as HTMLElement;
        const dbCards = ctaContainer.querySelectorAll('.sage-ai-data-db-card');
        const toggleButton = ctaContainer.querySelector(
          '.sage-ai-data-cta-toggle'
        ) as HTMLButtonElement;

        // Apply initial collapsed state
        if (isCollapsed) {
          ctaContainer.classList.add('collapsed');
          toggleButton.setAttribute('title', 'Expand');
        }

        // Toggle button functionality
        toggleButton.addEventListener('click', () => {
          const isCurrentlyCollapsed =
            ctaContainer.classList.contains('collapsed');

          if (isCurrentlyCollapsed) {
            // Expand
            ctaContainer.classList.remove('collapsed');
            toggleButton.setAttribute('title', 'Collapse');
            localStorage.setItem(CTA_COLLAPSED_KEY, 'false');
          } else {
            // Collapse
            ctaContainer.classList.add('collapsed');
            toggleButton.setAttribute('title', 'Expand');
            localStorage.setItem(CTA_COLLAPSED_KEY, 'true');
          }
        });

        // Auto-expand textarea functionality with modern styling
        inputField.addEventListener('input', () => {
          inputField.style.height = 'auto';
          const newHeight = Math.min(inputField.scrollHeight, 120);
          inputField.style.height = newHeight + 'px';
        });

        // Send message functionality - directly to LLM chat
        const handleSendMessage = () => {
          const message = inputField.value.trim();
          if (message) {
            const chatContainer = AppStateService.getState().chatContainer;
            if (chatContainer?.chatWidget?.inputManager) {
              // Set the message in the chat input and send it
              chatContainer.chatWidget.inputManager.setInputValue(message);
              void chatContainer.chatWidget.inputManager.sendMessage();
              // Clear the CTA input and reset height
              inputField.value = '';
              inputField.style.height = 'auto';
              // Collapse the CTA after sending message
              ctaContainer.classList.add('collapsed');
              toggleButton.setAttribute('title', 'Expand');
              localStorage.setItem(CTA_COLLAPSED_KEY, 'true');
              console.log('[WelcomeCTA] Message sent to chat:', message);
            } else {
              console.warn('[WelcomeCTA] Chat input manager not available');
            }
          }
        };

        sendButton.addEventListener('click', handleSendMessage);

        // Handle keyboard events: Enter to send, prevent ALL other keys from propagating
        inputField.addEventListener('keydown', e => {
          // Always stop propagation to prevent JupyterLab shortcuts from firing
          e.stopPropagation();
          e.stopImmediatePropagation();

          // Handle Enter key for sending
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
          }
          // Shift+Enter allows new line (default textarea behavior)
        });

        // Also prevent propagation for other keyboard events
        inputField.addEventListener('keyup', e => {
          e.stopPropagation();
          e.stopImmediatePropagation();
        });

        inputField.addEventListener('keypress', e => {
          e.stopPropagation();
          e.stopImmediatePropagation();
        });

        // Files card click handler - trigger file explorer upload
        const handleFileUpload = () => {
          const fileExplorerWidget =
            AppStateService.getState().fileExplorerWidget;

          if (fileExplorerWidget) {
            // Create a hidden file input element
            const fileInput = document.createElement('input');
            fileInput.type = 'file';
            fileInput.multiple = true;
            fileInput.accept = '.csv,.json,.xlsx,.xls,.parquet,.txt,.tsv';
            fileInput.style.display = 'none';

            fileInput.onchange = async (e: Event) => {
              const target = e.target as HTMLInputElement;
              if (target.files && target.files.length > 0) {
                // Call the file explorer's upload handler
                try {
                  await fileExplorerWidget.handleFileUpload(target.files);
                  console.log('[WelcomeCTA] Files uploaded successfully');
                } catch (error) {
                  console.error('[WelcomeCTA] File upload failed:', error);
                }
              }
              // Clean up
              document.body.removeChild(fileInput);
            };

            // Add to DOM and trigger click
            document.body.appendChild(fileInput);
            fileInput.click();
          } else {
            console.warn('[WelcomeCTA] File explorer widget not available');
            alert('File explorer is not available. Please try again later.');
          }
        };

        filesCard.addEventListener('click', handleFileUpload);
        filesCard.addEventListener('keydown', e => {
          const kbEvent = e as KeyboardEvent;
          if (kbEvent.key === 'Enter' || kbEvent.key === ' ') {
            kbEvent.preventDefault();
            handleFileUpload();
          }
        });

        // Database connection handlers - open database creation modal
        const handleDatabaseConnect = (dbType: string) => {
          const databaseManagerWidget =
            AppStateService.getState().databaseManagerWidget;

          if (databaseManagerWidget) {
            // Get the database type enum value
            let databaseType: DatabaseType;
            switch (dbType) {
              case 'postgresql':
                databaseType = DatabaseType.PostgreSQL;
                break;
              case 'mysql':
                databaseType = DatabaseType.MySQL;
                break;
              case 'snowflake':
                databaseType = DatabaseType.Snowflake;
                break;
              default:
                databaseType = DatabaseType.PostgreSQL;
            }

            // Open the database manager widget
            if (!databaseManagerWidget.isVisible) {
              databaseManagerWidget.show();
            }

            // Activate the widget (bring to front)
            app.shell.activateById(databaseManagerWidget.id);

            // Trigger the add database action with the specific type
            // We need to access the internal state and methods
            const widget = databaseManagerWidget as any;
            if (widget.handleAddDatabase) {
              widget.handleAddDatabase(databaseType);
            }

            console.log(
              `[WelcomeCTA] Opening database connection modal for ${dbType}`
            );
          } else {
            console.warn('[WelcomeCTA] Database manager widget not available');
            alert('Database manager is not available. Please try again later.');
          }
        };

        dbCards.forEach(card => {
          const dbType = card.getAttribute('data-db-type');
          if (dbType) {
            card.addEventListener('click', () => handleDatabaseConnect(dbType));
            card.addEventListener('keydown', e => {
              const kbEvent = e as KeyboardEvent;
              if (kbEvent.key === 'Enter' || kbEvent.key === ' ') {
                kbEvent.preventDefault();
                handleDatabaseConnect(dbType);
              }
            });
          }
        });

        // Find the jp-WindowedPanel-outer div inside the notebook panel
        const notebookPanelElement = currentNotebook.node.querySelector(
          '.jp-WindowedPanel.lm-Widget.jp-Notebook.jp-mod-scrollPastEnd.jp-mod-showHiddenCellsButton.jp-NotebookPanel-notebook'
        );

        const outerPanelElement = notebookPanelElement?.querySelector(
          '.jp-WindowedPanel-outer'
        ) as HTMLElement;

        if (outerPanelElement) {
          // Add the CTA container at the top of the outer panel
          outerPanelElement.insertBefore(
            ctaContainer,
            outerPanelElement.firstChild
          );
          console.log(
            '[WelcomeCTA] Data CTA interface added to jp-WindowedPanel-outer'
          );
        } else {
          console.warn(
            '[WelcomeCTA] Could not find jp-WindowedPanel-outer, trying fallback'
          );
          // Fallback: try to find just the notebook element
          const notebookElement =
            currentNotebook.node.querySelector('.jp-Notebook');
          if (notebookElement) {
            const fallbackOuter = notebookElement.querySelector(
              '.jp-WindowedPanel-outer'
            ) as HTMLElement;
            if (fallbackOuter) {
              fallbackOuter.insertBefore(
                ctaContainer,
                fallbackOuter.firstChild
              );
              console.log('[WelcomeCTA] Data CTA interface added via fallback');
            } else {
              currentNotebook.node.appendChild(ctaContainer);
              console.log(
                '[WelcomeCTA] Data CTA interface added to notebook panel (final fallback)'
              );
            }
          } else {
            currentNotebook.node.appendChild(ctaContainer);
            console.log(
              '[WelcomeCTA] Data CTA interface added to notebook panel (final fallback)'
            );
          }
        }
      } catch (error) {
        console.error('[WelcomeCTA] Failed to add CTA div:', error);
      }
    }
  });

  // Add this command to the command palette
  palette.addItem({ command: addCtaDivCommand, category: 'AI Tools' });
}
