import { parse as parseBestEffortJson } from 'best-effort-json-parser';
import { INotebookTracker, NotebookPanel } from '@jupyterlab/notebook';
import { NotebookContextManager } from '../../Notebook/NotebookContextManager';
import { Cell } from '@jupyterlab/cells';
import { NotebookTools } from '../../Notebook/NotebookTools';
import { AppStateService } from '../../AppState';
import { inlineDiffService } from '../../Notebook/InlineDiffService';

/**
 * Service that highlights cells that are in context
 * and provides UI to add/remove cells from context and quick generation
 */
export class ContextCellHighlighter {
  private notebookTracker: INotebookTracker;
  private notebookContextManager: NotebookContextManager;
  private notebookTools: NotebookTools;
  private highlightedCells: Map<string, Set<string>> = new Map(); // Map of notebook path to set of highlighted cell IDs
  private chatContainerRef: any = null; // Reference to chat container for updates
  private cellHistory: Map<string, string[]> = new Map(); // Map of cell tracking ID to array of content versions for undo
  private abortController: AbortController | null = null;
  private cellsWithKeydownListener = new WeakSet<HTMLElement>(); // Track cells that already have Cmd+K listener

  constructor(
    notebookTracker: INotebookTracker,
    notebookContextManager: NotebookContextManager,
    notebookTools: NotebookTools
  ) {
    this.notebookTracker = notebookTracker;
    this.notebookContextManager = notebookContextManager;
    this.notebookTools = notebookTools;

    // Add CSS for context highlighting
    this.addContextHighlightCSS();

    this.setupListeners();
  }

  /**
   * Handle prompt submission for AI quick generation
   */
  private async onPromptSubmit(
    cell: Cell,
    promptText: string
  ): Promise<boolean | 'cancelled'> {
    // This is the callback executed when a prompt is submitted from the quick generation input
    console.log(
      'Prompt submitted for cell',
      (cell as any).model?.id || cell.id,
      ':',
      promptText
    );

    // Get the cell ID (use tracking ID if available, fallback to model.id or id)
    const cellId =
      (cell as any).model?.sharedModel.getMetadata()?.cell_tracker
        ?.trackingId ||
      (cell as any).model?.id ||
      (cell as any).id ||
      '[unknown]';

    if (cellId === '[unknown]') {
      console.error('Could not determine cell ID for prompt submission.', cell);
      return false;
    }

    const activeCell = this.notebookTracker.activeCell;
    if (!activeCell) {
      console.warn('No active cell');
      return false;
    }

    const editor = activeCell.editor;
    const selection = editor?.getSelection();
    const cellLines = editor?.model.sharedModel.source.split('\n') || [];
    const endSelection = this.calculateEndLine(selection?.end, cellLines);
    const selectedText = editor?.model.sharedModel.source.substring(
      editor.getOffsetAt(selection?.start || { line: 0, column: 0 }),
      editor.getOffsetAt(endSelection)
    );

    // Check if there's selected text to determine the mode
    const hasSelection = selectedText && selectedText.trim().length > 0;

    // For edit_selection, get the selected line range
    const startLine = selection?.start?.line || 0;
    const endLine = endSelection.line;
    const selectedLines = cellLines.slice(startLine, endLine + 1);

    const config = AppStateService.getConfig();

    // Determine which config section to use based on whether text is selected
    let modeConfig;
    let modeLabel;
    if (hasSelection) {
      modeConfig = config.edit_selection;
      modeLabel = 'edit_selection';
    } else {
      modeConfig = config.edit_full_cell;
      modeLabel = 'edit_full_cell';
    }

    const systemPrompt = modeConfig.system_prompt;

    // Use ephemeral API call instead of chatbox for faster response
    try {
      const targetCell = this.notebookTools.findCellByTrackingId(cellId);
      const cellContent = targetCell?.cell.model.sharedModel.getSource();
      const previousCellContent = this.notebookTools
        .findCellByIndex((targetCell?.index || 0) - 1)
        ?.cell?.model?.sharedModel.getSource();

      // Compose enhanced context messages based on whether text is selected
      let contextMessage = '';

      if (hasSelection) {
        // Create line-numbered cell content for the selection range
        const selectionRangeLines = selectedLines
          .map((line, index) => {
            const lineNum = startLine + index + 1; // Use actual line numbers from the cell
            return `${lineNum.toString().padStart(3, ' ')}: ${line}`;
          })
          .join('\n');

        // Create line-numbered full cell content for context
        const fullCellLines = cellLines
          .map((line, index) => {
            const lineNum = index + 1;
            return `${lineNum.toString().padStart(3, ' ')}:${line}`;
          })
          .join('\n');

        contextMessage = `EDIT SELECTION MODE: Edit the selected lines (${startLine + 1}-${endLine + 1}) using structured operations.

FULL CELL CONTEXT:
\`\`\`
${fullCellLines}
\`\`\`

SELECTED LINES TO EDIT (${startLine + 1}-${endLine + 1}):
\`\`\`
${selectionRangeLines}
\`\`\`

Return a JSON object with operations for each line in the selection range. Use KEEP, MODIFY, REMOVE, or INSERT actions. Consider the full cell context when making edits.

User request: ${promptText}`;
      } else {
        contextMessage = `
              EDIT FULL CELL MODE: Edit and improve the complete cell.

              CELL TO EDIT:
              \`\`\`
              ${cellContent}
              \`\`\`

              PREVIOUS CELL CONTENT:
              \`\`\`
              ${previousCellContent}
              \`\`\`

              Return only the fully edited cell. Apply your quantitative expertise to improve the code.

              User request: ${promptText}`;
      }

      const chatService = AppStateService.getChatService();

      this.abortController = new AbortController();
      chatService.initializeRequest(this.abortController);

      // Handle streaming based on whether text is selected
      if (hasSelection) {
        // For edit_selection, use structured JSON operations with streaming
        const targetCell = this.notebookTools.findCellByTrackingId(cellId);
        if (!targetCell) {
          throw new Error(`Could not find cell with ID ${cellId}`);
        }

        let accumulatedResponse = '';
        let lastAppliedOperations: IEditOperation[] = [];

        // Helper function to try parsing JSON and extract complete operations
        const tryParseAndApplyOperations = (text: string): IEditOperation[] => {
          try {
            // Use best-effort JSON parser to handle incomplete JSON
            const parsedResponse = parseBestEffortJson(
              text.trim()
            ) as IEditSelectionResponse;

            if (
              parsedResponse?.operations &&
              Array.isArray(parsedResponse.operations)
            ) {
              return parsedResponse.operations.filter(
                (op: IEditOperation) =>
                  op.line !== undefined &&
                  op.action &&
                  ['KEEP', 'MODIFY', 'REMOVE', 'INSERT'].includes(op.action)
              );
            }
          } catch (error) {
            // JSON parsing failed, return empty array
          }
          return [];
        };

        // Helper function to apply operations progressively
        const applyOperationsToCell = (operations: IEditOperation[]) => {
          if (operations.length === 0) {
            return;
          }

          const updatedCellLines = [...cellLines];
          let lineOffset = 0;

          // Sort operations by line number to process in order
          const sortedOperations = operations.sort(
            (a: IEditOperation, b: IEditOperation) => a.line - b.line
          );

          for (const operation of sortedOperations) {
            const actualLineIndex = operation.line - 1 + lineOffset;

            switch (operation.action) {
              case 'KEEP':
                // Do nothing - line stays as is
                break;
              case 'MODIFY':
                if (
                  actualLineIndex < updatedCellLines.length &&
                  operation.content !== undefined
                ) {
                  updatedCellLines[actualLineIndex] = operation.content;
                }
                break;
              case 'REMOVE':
                if (actualLineIndex < updatedCellLines.length) {
                  updatedCellLines.splice(actualLineIndex, 1);
                  lineOffset--;
                }
                break;
              case 'INSERT':
                if (
                  actualLineIndex <= updatedCellLines.length &&
                  operation.content !== undefined
                ) {
                  updatedCellLines.splice(
                    actualLineIndex,
                    0,
                    operation.content
                  );
                  lineOffset++;
                }
                break;
            }
          }

          // Apply the changes to the cell
          targetCell.cell.model.sharedModel.setSource(
            updatedCellLines.join('\n')
          );
        };

        const response = await chatService.sendEphemeralMessage(
          contextMessage,
          systemPrompt,
          'claude-3-5-haiku-latest',
          (textChunk: string) => {
            accumulatedResponse += textChunk;

            // Try to parse and apply operations from the accumulated response
            const currentOperations =
              tryParseAndApplyOperations(accumulatedResponse);

            // Only apply if we have new or changed operations
            if (currentOperations.length > 0) {
              const operationsChanged =
                currentOperations.length !== lastAppliedOperations.length ||
                currentOperations.some((op, idx) => {
                  const lastOp = lastAppliedOperations[idx];
                  return (
                    !lastOp ||
                    op.line !== lastOp.line ||
                    op.action !== lastOp.action ||
                    op.content !== lastOp.content
                  );
                });

              if (operationsChanged) {
                applyOperationsToCell(currentOperations);
                lastAppliedOperations = [...currentOperations];
              }
            }
          },
          undefined,
          undefined,
          'cmd-k'
        );

        this.abortController = null;

        if (typeof response === 'object') {
          // Handle cancellation - restore original cell content
          const metadata: any =
            targetCell.cell.model.sharedModel.getMetadata() || {};
          const trackingId = metadata.cell_tracker?.trackingId;

          if (trackingId && this.cellHistory.has(trackingId)) {
            const history = this.cellHistory.get(trackingId);
            if (history && history.length > 0) {
              // Get the most recent version (the original content before editing)
              const originalContent = history[history.length - 1];
              targetCell.cell.model.sharedModel.setSource(originalContent);

              // Clean up the history entry since we're cancelling
              history.pop();
              if (history.length === 0) {
                this.cellHistory.delete(trackingId);
              }
            }
          }

          return 'cancelled';
        }

        // Final parsing and application
        try {
          const finalOperations = tryParseAndApplyOperations(response);
          if (finalOperations.length > 0) {
            applyOperationsToCell(finalOperations);
            console.log(
              `Applied ${finalOperations.length} edit_selection operations to lines ${startLine + 1}-${endLine + 1} in cell ${cellId}`
            );
          } else {
            throw new Error('No valid operations found in response');
          }
        } catch (error) {
          console.error(
            'Failed to parse final edit_selection response:',
            error
          );
          console.error('Raw response:', response);
          alert(
            'Error processing edit_selection: Invalid response format. Please try again.'
          );
          return false;
        }
      } else {
        // For edit_full_cell, keep the original behavior
        const targetCell = this.notebookTools.findCellByTrackingId(cellId);
        if (!targetCell) {
          throw new Error(`Could not find cell with ID ${cellId}`);
        }

        let accumulatedResponse = '';
        let codeContent = '';
        let isInCodeBlock = false;
        const codeBlockStartPattern = /```(?:python|py)?\s*/i;
        const codeBlockEndPattern = /```/;

        const response = await chatService.sendEphemeralMessage(
          contextMessage,
          systemPrompt,
          'claude-3-5-haiku-latest',
          (textChunk: string) => {
            accumulatedResponse += textChunk;

            // Handle code extraction for streaming
            if (!isInCodeBlock) {
              const startMatch = accumulatedResponse.match(
                codeBlockStartPattern
              );
              if (startMatch) {
                isInCodeBlock = true;
                // Remove everything up to and including the code block start (and any language specifier)
                codeContent = accumulatedResponse.substring(
                  accumulatedResponse.indexOf(startMatch[0]) +
                    startMatch[0].length
                );
                // Remove any leading 'python' or 'py' line if present
                codeContent = codeContent.replace(/^\s*(python|py)\s*\n?/i, '');
              } else {
                // Not in code block, just accumulate
                codeContent = accumulatedResponse;
              }
            } else {
              // Already in code block
              if (codeBlockEndPattern.test(textChunk)) {
                isInCodeBlock = false;
                // Remove trailing ```
                const endIndex = codeContent.lastIndexOf('```');
                if (endIndex !== -1) {
                  codeContent = codeContent.substring(0, endIndex);
                }
                // Remove any trailing 'python' or 'py' line if present
                codeContent = codeContent.replace(/^\s*(python|py)\s*\n?/i, '');
              } else {
                codeContent += textChunk;
              }
            }

            // Create progressive transformation effect
            if (codeContent.includes('\n')) {
              const newCodeLines = codeContent.split('\n');

              // Progressive replacement: mix old and new code
              const displayLines = [...cellLines];

              // Replace lines progressively based on how much new content we have
              const linesToReplace = Math.min(
                newCodeLines.length,
                cellLines.length
              );

              for (let i = 0; i < linesToReplace; i++) {
                if (newCodeLines[i] !== undefined) {
                  displayLines[i] = newCodeLines[i];
                }
              }

              // If new code has more lines than original, add them
              if (newCodeLines.length > cellLines.length) {
                for (let i = cellLines.length; i < newCodeLines.length; i++) {
                  if (newCodeLines[i] !== undefined) {
                    displayLines.push(newCodeLines[i]);
                  }
                }
              }

              // Update cell with the progressive transformation
              targetCell.cell.model.sharedModel.setSource(
                displayLines.join('\n')
              );
            } else if (codeContent.trim() && !codeContent.includes('\n')) {
              // Handle single line updates by replacing first line progressively
              const displayLines = [...cellLines];
              if (displayLines.length > 0) {
                displayLines[0] = codeContent.trim();
              } else {
                displayLines.push(codeContent.trim());
              }
              targetCell.cell.model.sharedModel.setSource(
                displayLines.join('\n')
              );
            }
          },
          undefined,
          undefined,
          'cmd-k'
        );

        this.abortController = null;

        if (typeof response === 'object') {
          // Handle cancellation - restore original cell content
          const metadata: any =
            targetCell.cell.model.sharedModel.getMetadata() || {};
          const trackingId = metadata.cell_tracker?.trackingId;

          if (trackingId && this.cellHistory.has(trackingId)) {
            const history = this.cellHistory.get(trackingId);
            if (history && history.length > 0) {
              // Get the most recent version (the original content before editing)
              const originalContent = history[history.length - 1];
              targetCell.cell.model.sharedModel.setSource(originalContent);

              // Clean up the history entry since we're cancelling
              history.pop();
              if (history.length === 0) {
                this.cellHistory.delete(trackingId);
              }
            }
          }

          return 'cancelled';
        }

        // Final cleanup and application for full cell mode
        let finalCode = codeContent.trim();
        if (!finalCode && response.trim()) {
          if (response.includes('```')) {
            const codeMatch = response.match(
              /```(?:python|py)?\s*([\s\S]*?)```/i
            );
            if (codeMatch) {
              finalCode = codeMatch[1]
                .replace(/^\s*(python|py)\s*\n?/i, '')
                .trim();
            }
          } else {
            finalCode = response.trim();
          }
        } else if (finalCode) {
          // Remove any leading/trailing code block markers and 'python' lines
          finalCode = finalCode
            .replace(/^```(?:python|py)?\s*/i, '')
            .replace(/```$/, '')
            .replace(/^\s*(python|py)\s*\n?/i, '')
            .trim();
        }

        // Always commit the last codeContent to the cell, even if not updated in the last chunk
        if (finalCode) {
          targetCell.cell.model.sharedModel.setSource(finalCode);
          console.log(
            `Applied edit_full_cell response to cell ${cellId} with progressive transformation`
          );
        }
      }

      console.log(
        `Ephemeral ${modeLabel} request completed using Haiku model.`
      );

      return true;
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : String(error);
      console.error(`Failed to process: ${errorMessage}`, error);
      return false;
    }
  }

  private async handlePromptSubmit(cell: Cell, prompt: string) {
    if (prompt.trim()) {
      const inputContainer = <HTMLInputElement>(
        cell.node.querySelector('.sage-ai-prompt-input')
      );
      const errorMessage = <HTMLElement>(
        cell.node.querySelector('.sage-ai-quick-gen-prompt-error-message')
      );
      const submitButton = <HTMLButtonElement>(
        cell.node.querySelector('.sage-ai-quick-gen-submit')
      );
      const undoButton = <HTMLButtonElement>(
        cell.node.querySelector('.sage-ai-quick-gen-undo')
      );
      const loader = <HTMLElement>(
        cell.node.querySelector('.sage-ai-blob-loader')
      );

      // Get cell tracking ID for history
      const metadata: any = cell.model.sharedModel.getMetadata() || {};
      const trackingId = metadata.cell_tracker?.trackingId;

      // Save current content before making changes
      const originalContent = cell.model.sharedModel.getSource();
      if (trackingId) {
        if (!this.cellHistory.has(trackingId)) {
          this.cellHistory.set(trackingId, []);
        }
        this.cellHistory.get(trackingId)!.push(originalContent);
      }

      loader.style.display = 'block';
      submitButton.disabled = true;
      inputContainer.disabled = true;
      if (undoButton) {
        undoButton.disabled = true;
      }

      const successResult = await this.onPromptSubmit(cell, prompt);

      loader.style.display = 'none';
      submitButton.disabled = false;
      inputContainer.disabled = false;

      if (successResult === true) {
        inputContainer.value = '';
        errorMessage.classList.add(
          'sage-ai-quick-gen-prompt-error-message-hidden'
        );

        // Get the new content after AI modification
        const newContent = cell.model.sharedModel.getSource();

        // Show diff view if content has changed
        if (originalContent !== newContent) {
          this.showDiffView(cell, originalContent, newContent);
        }

        // Update undo button state
        this.updateUndoButtonState(cell);
      } else if (successResult === false) {
        errorMessage.classList.remove(
          'sage-ai-quick-gen-prompt-error-message-hidden'
        );
        // Keep undo button disabled on failure
        if (undoButton) {
          undoButton.disabled = true;
        }
      }
    }
  }

  /**
   * Helper function to calculate end line for selection
   */
  private calculateEndLine(end: any, cellLines: string[]) {
    if (!end) {
      return null;
    }
    if (end.line >= cellLines.length) {
      return {
        line: cellLines.length - 1,
        column: cellLines[cellLines.length - 1]?.length || 0
      };
    }
    return end;
  }

  /**
   * Show diff view for a cell after AI modification using InlineDiffService
   */
  private showDiffView(
    cell: Cell,
    originalContent: string,
    newContent: string
  ): void {
    try {
      // Use InlineDiffService instead of HTML overlay
      inlineDiffService.showInlineDiff(cell, originalContent, newContent);

      console.log(
        '[ContextCellHighlighter] Inline diff displayed using InlineDiffService'
      );
    } catch (error) {
      console.error('Error showing diff view:', error);
    }
  }

  /**
   * Set the chat container reference for updates
   */
  public setChatContainer(container: any): void {
    this.chatContainerRef = container;
  }

  /**
   * Handle undo functionality for a cell
   */
  private handleUndo(cell: Cell): void {
    const metadata: any = cell.model.sharedModel.getMetadata() || {};
    const trackingId = metadata.cell_tracker?.trackingId;

    if (trackingId && this.cellHistory.has(trackingId)) {
      const history = this.cellHistory.get(trackingId);
      if (history && history.length > 0) {
        // Get the most recent previous version
        const previousContent = history.pop()!;
        cell.model.sharedModel.setSource(previousContent);

        // Update undo button state
        this.updateUndoButtonState(cell);

        // Remove from history if empty
        if (history.length === 0) {
          this.cellHistory.delete(trackingId);
        }
      }
    }
  }

  /**
   * Clear history for a specific cell
   */
  private clearCellHistory(trackingId: string): void {
    this.cellHistory.delete(trackingId);
  }

  /**
   * Get the number of undo steps available for a cell
   */
  private getUndoStepsAvailable(trackingId: string): number {
    const history = this.cellHistory.get(trackingId);
    return history ? history.length : 0;
  }

  /**
   * Update undo button tooltip and state
   */
  private updateUndoButtonState(cell: Cell): void {
    const metadata: any = cell.model.sharedModel.getMetadata() || {};
    const trackingId = metadata.cell_tracker?.trackingId;
    const undoButton = <HTMLButtonElement>(
      cell.node.querySelector('.sage-ai-quick-gen-undo')
    );

    if (undoButton && trackingId) {
      const stepsAvailable = this.getUndoStepsAvailable(trackingId);
      undoButton.disabled = stepsAvailable === 0;
      undoButton.title =
        stepsAvailable > 0
          ? `Undo AI changes (${stepsAvailable} step${stepsAvailable > 1 ? 's' : ''} available)`
          : 'No AI changes to undo';
    }
  }

  /**
   * Set up event listeners for notebook changes
   */
  private setupListeners(): void {
    // Listen for active notebook changes
    this.notebookTracker.currentChanged.connect((_, notebook) => {
      if (notebook) {
        // Apply highlighting to the newly active notebook
        this.highlightContextCells(notebook);

        // Listen for changes in cells
        notebook.model?.cells.changed.connect(() => {
          this.refreshHighlighting(notebook);
        });
      }
    });

    // Initial highlight for the current notebook
    if (this.notebookTracker.currentWidget) {
      this.highlightContextCells(this.notebookTracker.currentWidget);
    }
  }

  /**
   * Refresh highlighting for a notebook
   */
  public refreshHighlighting(notebook: NotebookPanel): void {
    // Clear existing highlights for this notebook
    const notebookPath = this.getNotebookId(notebook);
    this.highlightedCells.delete(notebookPath);

    // Apply highlighting again
    this.highlightContextCells(notebook);
  }

  /**
   * Add the CSS for context highlighting
   */
  private addContextHighlightCSS(): void {
    const style = document.createElement('style');
    style.id = 'sage-ai-context-highlight-style';
    style.textContent = `
      .sage-ai-in-context-cell {
        position: relative;
      }
      .sage-ai-cell-id-label {
        position: absolute;
        right: 8px;
        top: -8px;
        transform: translateY(-50%);
        background: var(--jp-layout-color2);
        color: #1976d2;
        border: 1px solid var(--jp-border-color0);
        border-radius: 4px;
        font-size: 10px;
        padding: 2px 6px;
        z-index: 101;
        pointer-events: none;
        color: var(--jp-ui-font-color1);
      }
      
      .sage-ai-context-indicator {
        position: absolute;
        left: -24px;
        top: 0;
        bottom: 0;
        width: 4px;
        background-color: #4CAF50;
        border-radius: 2px;
      }
      
      .sage-ai-context-badge {
        position: absolute;
        left: -80px;
        top: 50%;
        transform: translateY(-50%);
        background-color: #4CAF50;
        color: white;
        padding: 2px 5px;
        border-radius: 4px;
        font-size: 10px;
        white-space: nowrap;
        opacity: 0;
        transition: opacity 0.3s;
      }
      
      .sage-ai-in-context-cell:hover .sage-ai-context-badge {
        opacity: 1;
      }
      
      .sage-ai-context-buttons {
        position: absolute;
        top: 0px;
        left: 78px;
        transform: translateY(-100%);
        display: flex;
        gap: 8px;
        opacity: 1;
        z-index: 100;
      }
      
      .sage-ai-add-button, .sage-ai-remove-button {
        padding: 2px 8px;
        font-size: 10px;
        border-radius: 4px !important;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 4px;
        border: 1px solid var(--jp-border-color1);
      }
      
      .sage-ai-add-button {
        background-color: var(--jp-layout-color2);
        color: var(--jp-ui-font-color1);
      }
      
      .sage-ai-add-button:hover {
        background-color: var(--jp-layout-color3);
        border-color: #a9c6e9;
      }
      
      .sage-ai-remove-button {
        background-color: var(--jp-layout-color2);
        color: var(--jp-ui-font-color1);
        border: 1px solid #ffcdd2 !important;
      }
      
      .sage-ai-remove-button:hover {
        background-color: var(--jp-layout-color3);
        border-color: #ef9a9a !important;
      }

      .sage-ai-quick-generation {
        display: flex;
        align-items: center;
        border: 0;
        cursor: pointer;
        font-size: 10px;
        background-color: var(--jp-layout-color2);
        color: var(--jp-ui-font-color1);
        border: 1px solid var(--jp-border-color0);
        border-radius: 4px !important;
      }
      
      .sage-ai-quick-generation:hover {
        background-color: var(--jp-layout-color3);
        border-color: var(--jp-border-color1);
      }

      .sage-ai-quick-generation-hidden {
        display: none !important;
      }
      
      .sage-ai-quick-gen-prompt-container {
        display: inline-flex;
        justify-content: center;
        align-items: center;
        gap: 4px;
        flex: 1;
        padding: 6px;
      }

      .sage-ai-quick-gen-prompt-input-container {
        display: flex;
        flex-direction: column;
        gap: 4px;
        flex: 1;
      }

      .sage-ai-quick-gen-prompt-error-message {
        color: #f1625f;
        font-size: var(--jp-ui-font-size0);
        position: absolute;
        top: 28px;
        left: 93px;
      }

      .sage-ai-quick-gen-prompt-error-message-hidden {
        display: none;
      }

      .sage-ai-prompt-input {
        font-size: var(--jp-ui-font-size1);
        padding: 4px;
        margin: 0;
        min-height: 20px;
        width: 100%;
        border: 0;
        background-color: transparent;
        outline: 0;
      }

      .sage-ai-quick-gen-submit {
        display: flex;
        align-items: center;
        background: transparent;
        border: 0;
        padding: 0;
        margin: 0;
      }

      .sage-ai-quick-gen-undo {
        display: flex;
        align-items: center;
        background: transparent;
        border: 0;
        padding: 0;
        margin: 0;
        cursor: pointer;
        opacity: 0.5;
        transition: opacity 0.2s;
      }

      .sage-ai-quick-gen-undo:enabled {
        opacity: 1;
        cursor: pointer;
      }

      .sage-ai-quick-gen-undo:disabled {
        opacity: 0.3;
        cursor: not-allowed;
      }

      .sage-ai-quick-gen-cancel {
        color: var(--jp-ui-font-color1);
        font-size: 14px;
        cursor: pointer;
        line-height: 0;
      }

      .sage-ai-quick-gen-container {
        display: flex;
        flex-direction: column;
        flex: 1;
        border: var(--jp-border-width) solid var(--jp-cell-editor-border-color);
      }

      .sage-ai-quick-gen-active .jp-InputArea-editor {
        border-top: var(--jp-border-width) solid var(--jp-cell-editor-border-color) !important; /* Use !important to override */
        border-left: 0 !important;
        border-right: 0 !important;
        border-bottom: 0 !important;
      }

      .sage-ai-quick-gen-active .jp-Toolbar {
        top: 39px !important; /* Use !important to override */
      }

      /* Reset toolbar position when quick gen is not active */
      .jp-Cell:not(.sage-ai-quick-gen-active) .jp-Toolbar {
          top: 0 !important; /* Ensure it resets */
      }

      .sage-ai-placeholder-quick-gen {
        color: #828282;
        position: absolute;
        bottom: 12px;
        left: 84px;
      }

      .sage-ai-placeholder-quick-gen-hidden {
        display: none;
      }

      .sage-ai-placeholder-quick-gen-button {
        display: inline-flex;
        align-items: center;
        gap: 2px;
        color: #1976D2 !important;
      }

      .sage-ai-placeholder-quick-gen-button:hover {
        cursor: pointer;
        color: rgb(19, 93, 167) !important;
      }

      .sage-ai-placeholder-quick-gen-button:hover svg {
        cursor: pointer;
        fill: rgb(19, 93, 167) !important;
      }
      
      .sage-ai-plan-label {
        border-color: #12ff00 !important;
      }

      .sage-ai-quick-gen-diff-overlay {
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        transition: opacity 0.3s ease;
      }

      .sage-ai-quick-gen-diff-overlay:hover {
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
      }

      .sage-ai-diff-approve-button:hover {
        background: #45a049 !important;
        transform: scale(1.05);
        transition: all 0.2s ease;
      }

      .sage-ai-diff-reject-button:hover {
        background: #d32f2f !important;
        transform: scale(1.05);
        transition: all 0.2s ease;
      }
    `;
    document.head.appendChild(style);
  }

  private getNotebookId(notebook: NotebookPanel): string {
    const metadata = notebook.content.model?.sharedModel.getMetadata() as any;

    if (metadata.sage_ai?.unique_id) {
      return metadata.sage_ai.unique_id;
    }

    if (AppStateService.getCurrentNotebookId()) {
      return AppStateService.getCurrentNotebookId()!;
    }

    return notebook.context.path;
  }

  /**
   * Highlight cells that are in context for a specific notebook
   */
  private highlightContextCells(notebook: NotebookPanel): void {
    const notebookPath = this.getNotebookId(notebook);
    if (!notebookPath) {
      return;
    }

    // Get all context cells for this notebook
    const contextCells =
      this.notebookContextManager.getContextCells(notebookPath);

    // Create a set to track highlighted cells
    const highlightedSet = new Set<string>();
    this.highlightedCells.set(notebookPath, highlightedSet);

    // Apply highlighting to each cell in the context
    for (const contextCell of contextCells) {
      // Find the cell based on its ID
      const cellId = contextCell.trackingId || contextCell.cellId;
      const cellInfo = this.notebookTools.findCellByAnyId(cellId, notebookPath);

      if (cellInfo) {
        this.highlightCell(cellInfo.cell, true);
        highlightedSet.add(cellId);
      }
    }

    // Add context buttons to all cells
    this.addContextButtonsToAllCells(notebook);
  }

  /**
   * Add context buttons to all cells in a notebook
   */
  public addContextButtonsToAllCells(notebook: NotebookPanel): void {
    const cells = notebook.content.widgets;
    const notebookPath = this.getNotebookId(notebook);

    for (let i = 0; i < cells.length; i++) {
      const cell = cells[i];

      // Get tracking ID from metadata
      const metadata: any = cell.model.sharedModel.getMetadata() || {};
      const trackingId = metadata.cell_tracker?.trackingId;

      // Remove existing cell id label if any
      const existingIdLabel = cell.node.querySelector('.sage-ai-cell-id-label');
      if (existingIdLabel) {
        existingIdLabel.remove();
      }
      if (trackingId) {
        // Add cell id label to the right
        const idLabel = document.createElement('div');
        idLabel.setAttribute('sage-ai-cell-id', trackingId);
        idLabel.className = 'sage-ai-cell-id-label';
        if (trackingId === 'planning_cell') {
          idLabel.className += ' sage-ai-plan-label';
        }
        idLabel.textContent = trackingId;
        cell.node.appendChild(idLabel);

        // Check if this cell is in context
        const isInContext = this.notebookContextManager.isCellInContext(
          notebookPath,
          trackingId
        );

        // Add appropriate buttons based on context status
        this.addContextButtonsToCell(
          cell,
          trackingId,
          notebookPath,
          isInContext
        );
      }
    }
  }

  /**
   * Add context buttons to a single cell
   */
  private addContextButtonsToCell(
    cell: Cell,
    trackingId: string,
    notebookPath: string,
    isInContext: boolean
  ): void {
    // Remove existing buttons if any
    const existingButtons = cell.node.querySelector('.sage-ai-context-buttons');
    if (existingButtons) {
      existingButtons.remove();
    }

    // Create buttons container
    const buttonsContainer = document.createElement('div');
    buttonsContainer.className = 'sage-ai-context-buttons';

    if (isInContext) {
      // Create remove button if in context
      const removeButton = document.createElement('button');
      removeButton.className = 'sage-ai-remove-button';
      removeButton.textContent = 'Remove from Chat';
      removeButton.addEventListener('click', e => {
        e.stopPropagation();
        e.preventDefault();

        // Remove from context
        this.notebookContextManager.removeCellFromContext(
          notebookPath,
          trackingId
        );

        // Update the cell UI
        this.highlightCell(cell, false); // Immediately remove highlighting
        this.refreshHighlighting(this.notebookTracker.currentWidget!);

        // Update chat UI context counter
        if (this.chatContainerRef && !this.chatContainerRef.isDisposed) {
          this.chatContainerRef.onCellRemovedFromContext(
            notebookPath,
            trackingId
          );
        }
      });
      buttonsContainer.appendChild(removeButton);

      // Add the in-context class using classList
      cell.node.classList.add('sage-ai-in-context-cell');
    } else {
      // Create add button if not in context
      const addButton = document.createElement('button');
      addButton.className = 'sage-ai-add-button';
      addButton.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" height="12" width="12" viewBox="0 0 24 24">
          <path fill="#1976d2" d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6z"/>
        </svg>
        Add to Context
      `;
      addButton.addEventListener('click', e => {
        e.stopPropagation();
        e.preventDefault();

        // Get cell content and metadata
        const cellContent = cell.model.sharedModel.getSource();
        const cellType = cell.model.type;

        // Add to context
        this.notebookContextManager.addCellToContext(
          notebookPath,
          trackingId,
          trackingId,
          cellContent,
          cellType
        );

        // Update the cell UI
        this.refreshHighlighting(this.notebookTracker.currentWidget!);

        // Update chat UI context counter
        if (this.chatContainerRef && !this.chatContainerRef.isDisposed) {
          this.chatContainerRef.onCellAddedToContext(notebookPath, trackingId);
        }
      });

      buttonsContainer.appendChild(addButton);

      // Remove the in-context class using classList
      cell.node.classList.remove('sage-ai-in-context-cell');
    }

    const quickGen = cell.node.querySelector('.sage-ai-quick-gen-container');
    if (!quickGen) {
      const generateWithSageButton = document.createElement('button');
      generateWithSageButton.className = 'sage-ai-quick-generation';
      const isMac = /Mac|iPod|iPhone|iPad/.test(navigator.platform);
      // Unicode icons for Cmd, Ctrl, and Enter
      const cmdIcon = '\u2318'; // ⌘
      const ctrlIcon = '\u2303'; // ⌃
      const kIcon = 'K';

      // Compose label: [Cmd|Ctrl] + K
      const modifierIcon = isMac ? cmdIcon : ctrlIcon;

      generateWithSageButton.append(`Inline Edit (${modifierIcon} ${kIcon})`);
      buttonsContainer.appendChild(generateWithSageButton);

      if (!cell.model.sharedModel.source) {
        generateWithSageButton.classList.add('sage-ai-quick-generation-hidden');
      }

      // Add click event listener to the Inline Edit button
      generateWithSageButton.addEventListener('click', () => {
        const isBoxOpened = cell.node.querySelector(
          '.sage-ai-quick-gen-prompt-container'
        );
        if (isBoxOpened) {
          return;
        }

        // Hide the buttons container
        generateWithSageButton.classList.add('sage-ai-quick-generation-hidden');

        // Create and style the textarea
        const quickGenContainer = document.createElement('div');
        quickGenContainer.className = 'sage-ai-quick-gen-prompt-container';

        const loader = document.createElement('div');
        loader.className = 'sage-ai-blob-loader';
        loader.style.display = 'none';

        const inputContainer = document.createElement('div');
        inputContainer.className = 'sage-ai-quick-gen-prompt-input-container';

        const promptInput = document.createElement('input');
        promptInput.className = 'sage-ai-prompt-input';
        promptInput.placeholder = 'Edit selected lines or the whole cell';

        const errorMessage = document.createElement('span');
        errorMessage.className =
          'sage-ai-quick-gen-prompt-error-message sage-ai-quick-gen-prompt-error-message-hidden';
        errorMessage.textContent =
          'An unexpected error occurred, please try again.';

        inputContainer.append(promptInput, errorMessage);

        const cancelQuickGen = document.createElement('span');
        cancelQuickGen.className = 'sage-ai-quick-gen-cancel';
        cancelQuickGen.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" height="20px" width="20px" viewBox="0 0 24 24">
          <path fill="var(--jp-ui-font-color3)" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
        </svg>
      `;

        cancelQuickGen.addEventListener('click', () => {
          const chatService = AppStateService.getChatService();
          if (this.abortController && !this.abortController.signal.aborted) {
            chatService.cancelRequest();
            this.abortController = null;
            return;
          }

          container.remove();
          cellInputArea?.appendChild(cellInputAreaEditor);
          buttonsContainer.classList.remove('sage-ai-buttons-hidden');
          cell.node.classList.remove('sage-ai-quick-gen-active');

          if (cell.model.sharedModel.source) {
            generateWithSageButton.classList.remove(
              'sage-ai-quick-generation-hidden'
            );
          }
        });

        const undoButton = document.createElement('button');
        undoButton.className = 'sage-ai-quick-gen-undo';
        undoButton.disabled = true; // Initially disabled
        undoButton.innerHTML = UNDO_ICON;
        undoButton.title = 'Undo AI changes';
        undoButton.addEventListener('click', () => {
          this.handleUndo(cell);
        });

        const submitButton = document.createElement('button');
        submitButton.className = 'sage-ai-quick-gen-submit';
        submitButton.style.cursor = 'pointer';
        submitButton.innerHTML =
          '<svg width="20px" height="20px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" stroke="var(--jp-ui-font-color3)"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <g clip-path="url(#clip0_429_11126)"> <path d="M9 4.00018H19V18.0002C19 19.1048 18.1046 20.0002 17 20.0002H9" stroke="var(--jp-ui-font-color3)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"></path> <path d="M12 15.0002L15 12.0002M15 12.0002L12 9.00018M15 12.0002H5" stroke="var(--jp-ui-font-color3)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"></path> </g> <defs> <clipPath id="clip0_429_11126"> <rect width="24" height="24" fill="white"></rect> </clipPath> </defs> </g></svg>';

        submitButton.addEventListener('click', () => {
          void this.handlePromptSubmit(cell, promptInput.value);
        });

        quickGenContainer.append(
          inputContainer,
          loader,
          undoButton,
          submitButton,
          cancelQuickGen
        );

        const container = document.createElement('div');
        container.className = 'sage-ai-quick-gen-container';

        const cellInputAreaEditor = <HTMLElement>(
          cell.node.querySelector('.jp-InputArea-editor')
        );
        if (!cellInputAreaEditor) {
          throw "Unexpected error: Couldn't find the cell input area editor element";
        }

        container.append(quickGenContainer, cellInputAreaEditor);

        const cellInputArea = cell.node.querySelector('.jp-InputArea');
        if (!cellInputArea) {
          throw "Unexpected error: Couldn't find the cell input area element";
        }

        cellInputArea.appendChild(container);

        // Add class to cell node to activate toolbar and editor styles
        cell.node.classList.add('sage-ai-quick-gen-active');

        // Focus the textarea
        promptInput.focus();

        // Add keydown listener for submission
        promptInput.addEventListener('keydown', event => {
          // Submit on Enter (without Shift)
          if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault(); // Prevent newline
            void this.handlePromptSubmit(cell, promptInput.value);
          }
        });
      });
    }

    // Add keydown listener to trigger quick generation on Cmd+K (only once per cell)
    // This serves as a fallback; the primary keybinding is registered via JupyterLab commands
    if (!this.cellsWithKeydownListener.has(cell.node)) {
      cell.node.addEventListener(
        'keydown',
        event => {
          // Check if Cmd+K or Ctrl+K is pressed
          if (
            (event.metaKey || event.ctrlKey) &&
            (event.key === 'k' || event.key === 'K')
          ) {
            // Check if the cell is active
            if (!cell.node.classList.contains('jp-mod-active')) {
              return;
            }

            event.preventDefault(); // Prevent default browser shortcut
            event.stopPropagation(); // Stop event from bubbling

            // Check if quick gen is already open
            const isBoxOpened = cell.node.querySelector(
              '.sage-ai-quick-gen-prompt-container'
            );
            if (isBoxOpened) {
              return;
            }

            // Find the generate button and trigger its click event
            // This will work regardless of whether the button is visible or hidden
            const generateButton = cell.node.querySelector(
              '.sage-ai-quick-generation'
            ) as HTMLButtonElement;
            if (generateButton) {
              generateButton.click();
            }
          }
        }
      );
      this.cellsWithKeydownListener.add(cell.node);
    }

    try {
      this.createCellPlaceholder(cell);
      this.cellPlaceholderListener(cell);
    } catch (e) {
      console.error(`Couldn't setup placeholder: ${e}`);
    }

    // Add buttons to cell
    cell.node.appendChild(buttonsContainer);
  }

  private cellPlaceholderListener(cell: Cell) {
    cell.model.contentChanged.connect(ev => {
      const sageEditButton = cell.node.querySelector(
        '.sage-ai-quick-generation'
      );
      const hasContent = ev.sharedModel.source;
      const placeholder = <HTMLElement>(
        cell.node.querySelector('.sage-ai-placeholder-quick-gen')
      );
      const isPlaceholderHidden = placeholder?.classList.contains(
        'sage-ai-placeholder-quick-gen-hidden'
      );

      if (!hasContent && isPlaceholderHidden) {
        placeholder?.classList.remove('sage-ai-placeholder-quick-gen-hidden');
        sageEditButton?.classList.add('sage-ai-quick-generation-hidden');
        return;
      }

      if (hasContent) {
        placeholder?.classList.add('sage-ai-placeholder-quick-gen-hidden');
        sageEditButton?.classList.remove('sage-ai-quick-generation-hidden');
        return;
      }
    });
  }

  private createCellPlaceholder(cell: Cell) {
    const placeholder = cell.node.querySelector(
      '.sage-ai-placeholder-quick-gen'
    );
    if (placeholder) {
      return;
    }

    const placeholderQuickGen = document.createElement('span');
    placeholderQuickGen.className = 'sage-ai-placeholder-quick-gen';
    if (cell.model.sharedModel.source) {
      placeholderQuickGen.classList.add('sage-ai-placeholder-quick-gen-hidden');
    }
    const isMac = /Mac|iPod|iPhone|iPad/.test(navigator.platform);
    // Unicode icons for Cmd, Ctrl, and Enter
    const cmdIcon = '\u2318'; // ⌘
    const ctrlIcon = '\u2303'; // ⌃
    const kIcon = 'K';

    // Compose label: [Cmd|Ctrl] + Enter
    const modifierIcon = isMac ? cmdIcon : ctrlIcon;

    const quickGenButton = document.createElement('a');
    quickGenButton.className = 'sage-ai-placeholder-quick-gen-button';
    quickGenButton.textContent = `Inline Edit (${modifierIcon} ${kIcon})`;
    placeholderQuickGen.textContent = 'Start coding or use ';
    placeholderQuickGen.append(quickGenButton);

    quickGenButton.addEventListener('click', ev => {
      ev.stopPropagation();
      const generateWithSageButton = <HTMLElement>(
        cell.node.querySelector('.sage-ai-quick-generation')
      );
      const isOpen = cell.node.querySelector(
        '.sage-ai-quick-gen-prompt-container'
      );
      if (generateWithSageButton && !isOpen) {
        generateWithSageButton.click();
      }
    });

    placeholderQuickGen.addEventListener('click', () => {
      const editor = <HTMLElement>cell.node.querySelector('.cm-content');
      editor?.focus();
    });

    cell.node.append(placeholderQuickGen);
  }

  /**
   * Highlight a cell to indicate it's in context
   */
  private highlightCell(cell: Cell, isInContext: boolean): void {
    // Remove existing highlighting
    cell.node.classList.remove('sage-ai-in-context-cell');
    const existingIndicator = cell.node.querySelector(
      '.sage-ai-context-indicator'
    );
    if (existingIndicator) {
      existingIndicator.remove();
    }

    const existingBadge = cell.node.querySelector('.sage-ai-context-badge');
    if (existingBadge) {
      existingBadge.remove();
    }

    if (isInContext) {
      // Add the highlighting class
      cell.node.classList.add('sage-ai-in-context-cell');

      // Create and add the indicator
      const indicator = document.createElement('div');
      indicator.className = 'sage-ai-context-indicator';
      cell.node.appendChild(indicator);

      // Create and add the badge
      const badge = document.createElement('div');
      badge.className = 'sage-ai-context-badge';
      badge.textContent = 'In Context';
      cell.node.appendChild(badge);
    }
  }
}

const UNDO_ICON = `
      <svg width="20px" height="20px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" stroke="var(--jp-ui-font-color3)">
        <path d="M3 7v6h6" stroke="var(--jp-ui-font-color3)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13" stroke="var(--jp-ui-font-color3)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    `;

interface IEditOperation {
  line: number;
  action: 'KEEP' | 'MODIFY' | 'REMOVE' | 'INSERT';
  content: string;
}

interface IEditSelectionResponse {
  operations: IEditOperation[];
}
