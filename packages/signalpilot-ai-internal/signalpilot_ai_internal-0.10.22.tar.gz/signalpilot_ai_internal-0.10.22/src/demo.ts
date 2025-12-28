import { driver } from 'driver.js';
import 'driver.js/dist/driver.css';
import '../style/welcome-tour.css';
import { AppStateService } from './AppState';
import { JupyterFrontEnd } from '@jupyterlab/application';
import { BackendCacheService, STATE_DB_KEYS } from './utils/backendCaching';

/**
 * Run the SignalPilot welcome demo using driver.js
 * This demo guides users through the main features of the extension
 */
export function runWelcomeDemo(app: JupyterFrontEnd): void {
  // Make sure the chat panel is visible
  try {
    if (!AppStateService.getState().isLauncherActive) {
      app.shell.activateById('sage-ai-chat-container');
    }
  } catch (error) {
    console.warn('[WelcomeDemo] Could not activate chat panel:', error);
  }

  // Start pre-loading the welcome message immediately
  const chatContainer = AppStateService.getChatContainerSafe();
  if (chatContainer && chatContainer.chatWidget) {
    console.log('[WelcomeDemo] Starting welcome message pre-load...');
    void chatContainer.chatWidget.startWelcomeMessagePreload();
  }

  // Wait for UI to settle and layout to complete
  setTimeout(() => {
    // Force a layout reflow to ensure all dimensions are calculated
    document.body.offsetHeight;

    // Use requestAnimationFrame to wait for paint to complete
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        startTourWithElements(app);
      });
    });
  }, 800);
}

/**
 * Internal function to start the tour after ensuring elements are ready
 */
function startTourWithElements(app: JupyterFrontEnd): void {
  // Get the chat container and settings elements
  const chatContainer = AppStateService.getChatContainerSafe();

  if (!chatContainer) {
    console.warn('[WelcomeDemo] Chat container not available - aborting tour');
    return;
  }

  // Find the chat input element (using the chatbox wrapper which contains the input)
  const chatInput = document.querySelector('.sage-ai-chatbox-wrapper');

  // Find the context row (which includes the Add Context button)
  const contextRow = document.querySelector('.sage-ai-context-row');

  // Find the File Explorer widget in the left sidebar
  const fileExplorerPanel = document.querySelector(
    '.lm-Widget.sage-ai-file-explorer-widget.lm-StackedPanel-child'
  );

  // Find the File Explorer tab in the left sidebar
  const fileExplorerTab = document.querySelector(
    'li.lm-TabBar-tab[role="tab"][data-id="sage-ai-file-explorer"]'
  );

  // Find the Database Manager widget in the left sidebar
  const databaseManagerPanel = document.querySelector(
    '.lm-Widget.sage-ai-database-manager-widget.lm-StackedPanel-child'
  );

  // Find the Database Manager tab in the left sidebar
  const databaseManagerTab = document.querySelector(
    'li.lm-TabBar-tab[role="tab"][data-id="sage-ai-database-manager"]'
  );

  // Find the Snippet Creation widget in the left sidebar
  const snippetCreationPanel = document.querySelector(
    '.lm-Widget.sage-ai-snippet-creation-widget.lm-StackedPanel-child'
  );

  // Find the Snippet Creation tab in the left sidebar
  const snippetCreationTab = document.querySelector(
    'li.lm-TabBar-tab[role="tab"][data-id="sage-ai-snippet-creation"]'
  );

  if (!chatInput) {
    console.warn('[WelcomeDemo] Chat input not found - aborting tour');
    return;
  }

  if (!contextRow) {
    console.warn('[WelcomeDemo] Context row not found - aborting tour');
    return;
  }

  // Initialize the driver
  try {
    const driverObj = driver({
      showProgress: true,
      animate: false, // Disable driver.js animations to prevent jump
      allowClose: false,
      onDestroyed: () => {
        console.log('[WelcomeDemo] Tour closed');
        BackendCacheService.setValue(STATE_DB_KEYS.WELCOME_TOUR_COMPLETED, true)
          .then(() => {
            console.log('[WelcomeDemo] Tour completion saved to cache');
            if (AppStateService.getState().isLauncherActive) {
              void AppStateService.getState().chatContainer?.chatWidget.showWelcomeMessage();
            }
          })
          .catch(error => {
            console.error(
              '[WelcomeDemo] Failed to save tour completion:',
              error
            );
          });
      },
      onPopoverRender: popover => {
        // Small delay to let positioning settle, then ensure visibility
        requestAnimationFrame(() => {
          const popoverElement = popover.wrapper;
          if (popoverElement) {
            // Force a reflow to ensure positioning is calculated
            popoverElement.offsetHeight;
          }
        });
      },
      steps: [
        {
          popover: {
            title: 'Welcome to SignalPilot! 🚀',
            description:
              'Let me show you around! This quick tour will help you get started with your AI-powered Jupyter assistant.',
            onNextClick: () => {
              driverObj.moveNext();
            }
          }
        },
        {
          element: chatInput as HTMLElement,
          popover: {
            title: 'Chat with AI 💬',
            description:
              'This is your chat interface. Ask questions, request code changes, or get help with your data analysis.',
            side: 'left',
            align: 'start',
            onNextClick: () => {
              driverObj.moveNext();
            },
            onPrevClick: () => {
              driverObj.movePrevious();
            }
          }
        },
        {
          element: fileExplorerPanel as HTMLElement,
          popover: {
            title: 'File Picker 📁',
            description:
              'On the left sidebar, you can manage your data files here. Browse, upload, and organize files for your analysis.',
            side: 'right',
            align: 'start',
            onNextClick: () => {
              driverObj.moveNext();
            },
            onPrevClick: () => {
              driverObj.movePrevious();
            }
          },
          onHighlightStarted: element => {
            // Open the file explorer panel and wait for layout to complete
            return new Promise<void>(resolve => {
              try {
                if (fileExplorerTab) {
                  app.shell.activateById('sage-ai-file-explorer');

                  // Wait for layout to settle with multiple animation frames
                  requestAnimationFrame(() => {
                    // Force a reflow to ensure dimensions are calculated
                    if (element) {
                      (element as HTMLElement).offsetHeight;
                    }

                    requestAnimationFrame(() => {
                      // Additional delay to ensure the left sidebar is fully expanded
                      setTimeout(() => {
                        // Final reflow
                        if (element) {
                          (element as HTMLElement).offsetHeight;
                        }
                        resolve();
                      }, 1000);
                    });
                  });
                } else {
                  resolve();
                }
              } catch (error) {
                console.warn(
                  '[WelcomeDemo] Could not activate file explorer:',
                  error
                );
                resolve();
              }
            });
          }
        },
        {
          element: databaseManagerPanel as HTMLElement,
          popover: {
            title: 'Database Connections 🗄️',
            description:
              'Also on the left sidebar, connect and manage your databases here. Add MySQL, PostgreSQL, or Snowflake connections for easy data access.',
            side: 'right',
            align: 'start',
            onNextClick: () => {
              driverObj.moveNext();
            },
            onPrevClick: () => {
              driverObj.movePrevious();
            }
          },
          onHighlightStarted: element => {
            // Open the database manager panel and wait for layout to complete
            return new Promise<void>(resolve => {
              try {
                if (databaseManagerTab) {
                  app.shell.activateById('sage-ai-database-manager');

                  // Wait for layout to settle with multiple animation frames
                  requestAnimationFrame(() => {
                    // Force a reflow to ensure dimensions are calculated
                    if (element) {
                      (element as HTMLElement).offsetHeight;
                    }

                    requestAnimationFrame(() => {
                      // Additional delay to ensure the left sidebar is fully expanded
                      setTimeout(() => {
                        // Final reflow
                        if (element) {
                          (element as HTMLElement).offsetHeight;
                        }
                        resolve();
                      }, 300);
                    });
                  });
                } else {
                  resolve();
                }
              } catch (error) {
                console.warn(
                  '[WelcomeDemo] Could not activate database manager:',
                  error
                );
                resolve();
              }
            });
          }
        },
        {
          element: snippetCreationPanel as HTMLElement,
          popover: {
            title: 'Rules & Snippets 📝',
            description:
              'On the left sidebar, create reusable rules and code snippets. Define custom instructions that the AI will follow in your conversations.',
            side: 'right',
            align: 'start',
            onNextClick: () => {
              driverObj.moveNext();
            },
            onPrevClick: () => {
              driverObj.movePrevious();
            }
          },
          onHighlightStarted: element => {
            // Open the snippet creation panel and wait for layout to complete
            return new Promise<void>(resolve => {
              try {
                if (snippetCreationTab) {
                  app.shell.activateById('sage-ai-snippet-creation');

                  // Wait for layout to settle with multiple animation frames
                  requestAnimationFrame(() => {
                    // Force a reflow to ensure dimensions are calculated
                    if (element) {
                      (element as HTMLElement).offsetHeight;
                    }

                    requestAnimationFrame(() => {
                      // Additional delay to ensure the left sidebar is fully expanded
                      setTimeout(() => {
                        // Final reflow
                        if (element) {
                          (element as HTMLElement).offsetHeight;
                        }
                        resolve();
                      }, 300);
                    });
                  });
                } else {
                  resolve();
                }
              } catch (error) {
                console.warn(
                  '[WelcomeDemo] Could not activate snippet creation:',
                  error
                );
                resolve();
              }
            });
          }
        },
        {
          element: contextRow as HTMLElement,
          popover: {
            title: 'Context Picker 🎯',
            description:
              'Use this to add context to your conversations. Click the button or type @ to attach files, databases, code snippets, cells, and more to your messages.',
            side: 'top',
            align: 'start',
            onNextClick: () => {
              driverObj.moveNext();
            },
            onPrevClick: () => {
              driverObj.movePrevious();
            }
          },
          onHighlightStarted: () => {
            // Switch back to chat for context picker
            try {
              if (!AppStateService.getState().isLauncherActive) {
                app.shell.activateById('sage-ai-chat-container');
              }
            } catch (error) {
              console.warn('[WelcomeDemo] Could not activate chat:', error);
            }
          }
        },
        {
          popover: {
            title: "You're All Set! 🎉",
            description:
              'You now know the basics! Start by asking a question in the chat, or explore the sidebar tools to configure your workspace. Happy coding!',
            onNextClick: () => {
              driverObj.destroy();
            }
          },
          onHighlightStarted: () => {
            // Close the snippet creation (rules) tab on the final step
            try {
              const snippetWidget = Array.from(app.shell.widgets('left')).find(
                widget => widget.id === 'sage-ai-snippet-creation'
              );
              if (snippetWidget) {
                snippetWidget.close();
              }
            } catch (error) {
              console.warn(
                '[WelcomeDemo] Could not close snippet creation widget:',
                error
              );
            }
          }
        }
      ]
    });

    // Start the tour
    driverObj.drive();
  } catch (error) {
    console.error('[WelcomeDemo] Error starting tour:', error);
  }
}
