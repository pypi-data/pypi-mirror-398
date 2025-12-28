import * as React from 'react';
import { ILLMState, LLMDisplayState } from './types';
import { DiffItem } from './DiffItem';
import { AppStateService } from '../../AppState';
import { IPendingDiff } from '../../types';
import { MENU_CLOSE_ICON, MENU_ICON, WARNING_ICON } from './icons';
import { getToolDisplayMessage, getToolIcon } from '../../utils/toolDisplay';
import { diffStateService } from '../../Services/DiffStateService';
import { NotebookDiffTools } from '../../Notebook/NotebookDiffTools';

/**
 * React component for displaying LLM processing state content
 */
export function LLMStateContent({
  isVisible,
  state,
  text,
  toolName,
  diffs,
  waitingForUser,
  isRunContext,
  onRunClick,
  onRejectClick
}: ILLMState): JSX.Element | null {
  const [isExpanded, setIsExpanded] = React.useState(false);
  const [allDiffsResolved, setAllDiffsResolved] = React.useState(false);
  const [currentDiffs, setCurrentDiffs] = React.useState<IPendingDiff[]>(
    diffs || []
  );
  const [shouldHideForDemoMode, setShouldHideForDemoMode] =
    React.useState(false);

  // Refs for run buttons to enable keyboard shortcuts
  const runButtonRef = React.useRef<HTMLButtonElement>(null);
  const runAllButtonRef = React.useRef<HTMLButtonElement>(null);

  // Check if we should hide the display when in demo mode and not authenticated
  React.useEffect(() => {
    const checkDemoModeAuth = async () => {
      const isDemoMode = AppStateService.isDemoMode();

      if (!isDemoMode) {
        setShouldHideForDemoMode(false);
        return;
      }

      // In demo mode, check authentication
      let isAuthenticated = false;

      // First check user profile in AppState
      const userProfile = AppStateService.getUserProfile();
      if (userProfile) {
        isAuthenticated = true;
      } else {
        // If not in AppState, try to get it from JupyterAuthService
        try {
          const { JupyterAuthService } = await import(
            '../../Services/JupyterAuthService'
          );
          isAuthenticated = await JupyterAuthService.isAuthenticated();
        } catch (error) {
          console.warn(
            '[LLMStateContent] Failed to check authentication:',
            error
          );
          isAuthenticated = false;
        }
      }

      // Hide if in demo mode and not authenticated
      setShouldHideForDemoMode(isDemoMode && !isAuthenticated);
    };

    checkDemoModeAuth();
  }, []);

  // Subscribe to diff state changes from DiffStateService
  React.useEffect(() => {
    const subscription = diffStateService.diffState$.subscribe(diffState => {
      const newDiffs = Array.from(diffState.pendingDiffs.values());
      setCurrentDiffs(newDiffs);

      // Check if all diffs are resolved
      if (newDiffs.length > 0) {
        const allDecided = newDiffs.every(
          diff =>
            diff.userDecision === 'approved' ||
            diff.userDecision === 'rejected' ||
            diff.userDecision === 'run' ||
            diff.approved === true ||
            diff.approved === false
        );
        setAllDiffsResolved(allDecided);
      } else {
        setAllDiffsResolved(false);
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  // Also listen for changes in the passed diffs prop for backwards compatibility
  React.useEffect(() => {
    if (diffs && diffs.length > 0) {
      setCurrentDiffs(diffs);
      // Check if all diffs have decisions (approved, rejected, or run)
      const allDecided = diffs.every(
        diff =>
          diff.userDecision === 'approved' ||
          diff.userDecision === 'rejected' ||
          diff.userDecision === 'run' ||
          diff.approved === true ||
          diff.approved === false
      );
      setAllDiffsResolved(allDecided);
    } else if (diffs && diffs.length === 0) {
      setCurrentDiffs([]);
      setAllDiffsResolved(false);
    }
  }, [diffs]);

  // Set up keyboard handler for cmd+enter / ctrl+enter
  React.useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Check for Cmd+Enter (macOS) or Ctrl+Enter (Windows/Linux)
      if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
        // Only proceed if the LLM state display is visible
        if (!isVisible) {
          return;
        }

        // For USING_TOOL state (Run/Reject buttons)
        if (state === LLMDisplayState.USING_TOOL && runButtonRef.current) {
          console.log('[LLMStateContent] Cmd+Enter pressed, clicking Run button');
          event.preventDefault();
          event.stopPropagation();
          runButtonRef.current.click();
          return;
        }

        // For DIFF state (Run All/Approve All button)
        if (state === LLMDisplayState.DIFF && runAllButtonRef.current && !allDiffsResolved) {
          console.log('[LLMStateContent] Cmd+Enter pressed, clicking Run/Approve All button');
          event.preventDefault();
          event.stopPropagation();
          runAllButtonRef.current.click();
          return;
        }

        // For RUN_KERNEL state (Run all cells button)
        if (state === LLMDisplayState.RUN_KERNEL && runButtonRef.current) {
          console.log('[LLMStateContent] Cmd+Enter pressed, clicking Run all cells button');
          event.preventDefault();
          event.stopPropagation();
          runButtonRef.current.click();
          return;
        }
      }
    };

    // Add keyboard event listener
    document.addEventListener('keydown', handleKeyDown);

    // Cleanup
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isVisible, state, allDiffsResolved]);

  // Helper function to calculate total additions and deletions
  const calculateTotals = (diffs: IPendingDiff[]) => {
    let totalAdded = 0;
    let totalRemoved = 0;

    diffs.forEach(diff => {
      const oldLines = diff.originalContent?.split('\n') || [];
      const oldLinesCount = oldLines.length;
      const newLines = diff.newContent?.split('\n') || [];
      const newLinesCount = newLines.length;

      if (diff.type === 'add') {
        totalAdded += newLinesCount;
      } else if (diff.type === 'remove') {
        totalRemoved += oldLinesCount;
      } else if (diff.type === 'edit') {
        const diffLines = NotebookDiffTools.calculateDiff(
          diff.originalContent || '',
          diff.newContent || ''
        );
        totalAdded += diffLines.filter(line => line.type === 'added').length;
        totalRemoved += diffLines.filter(
          line => line.type === 'removed'
        ).length;
      }
    });

    return { totalAdded, totalRemoved };
  };

  // Use currentDiffs for display instead of the prop diffs
  const displayDiffs = currentDiffs.length > 0 ? currentDiffs : diffs || [];

  // Hide if in demo mode and not authenticated
  if (shouldHideForDemoMode) {
    return null;
  }

  if (!isVisible) {
    return null;
  }

  // Idle state - don't show anything
  if (state === LLMDisplayState.IDLE) {
    return null;
  }

  // Generating state - show thinking indicator
  if (state === LLMDisplayState.GENERATING) {
    return (
      <div
        className="sage-ai-llm-state-display sage-ai-generating"
        style={{ display: 'flex' }}
      >
        <div className="sage-ai-llm-state-content">
          {waitingForUser && <div className="sage-ai-waiting-for-user" />}
          {!waitingForUser && <div className="sage-ai-blob-loader" />}
          <span className="sage-ai-llm-state-text">{text}</span>
        </div>

        {!waitingForUser && (
          <button
            className="sage-ai-llm-state-stop-button"
            onClick={() => {
              AppStateService.getChatContainerSafe()?.chatWidget.cancelMessage();
            }}
            title="Stop generation"
          >
            Stop
          </button>
        )}
      </div>
    );
  }

  // Using tool state - show tool usage indicator
  if (state === LLMDisplayState.USING_TOOL) {
    const toolIcon = toolName ? getToolIcon(toolName) : null;
    let toolMessage = toolName
      ? getToolDisplayMessage(toolName)
      : text || 'Using tool...';

    // Check if this is the notebook-run_cell tool that needs confirmation
    const isRunCellTool = toolName === 'notebook-run_cell';

    if (isRunCellTool) {
      toolMessage = 'Waiting to run cell...';
    }
    const isTerminalCommand = toolName === 'terminal-execute_command';
    if (isTerminalCommand) {
      toolMessage = 'Waiting to run terminal command...';
    }

    return (
      <div
        className="sage-ai-llm-state-display sage-ai-using-tool"
        style={{ display: 'flex' }}
      >
        <div className="sage-ai-llm-state-content">
          {toolIcon ? (
            <div
              className="sage-ai-tool-icon-container"
              dangerouslySetInnerHTML={{ __html: toolIcon }}
            />
          ) : (
            <div className="sage-ai-tool-loader" />
          )}
          <span
            className="sage-ai-llm-state-text"
            dangerouslySetInnerHTML={{ __html: toolMessage }}
          />
        </div>

        <div className="sage-ai-llm-state-buttons">
          {(isRunCellTool || isTerminalCommand) && onRunClick && onRejectClick ? (
            // Show Run/Reject buttons for notebook-run_cell and terminal-execute_command tools
            <>
              <button
                className="sage-ai-llm-state-reject-button"
                onClick={onRejectClick}
                title="Reject code execution"
              >
                Reject
              </button>
              <button
                ref={runButtonRef}
                className="sage-ai-llm-state-run-button"
                onClick={onRunClick}
                title="Run code (Cmd/Ctrl + Enter)"
              >
                Run
              </button>
            </>
          ) : (
            // Show Stop button for other tools
            <button
              className="sage-ai-llm-state-stop-button"
              onClick={() => {
                AppStateService.getChatContainerSafe()?.chatWidget.cancelMessage();
              }}
              title="Stop tool execution"
            >
              Stop
            </button>
          )}
        </div>
      </div>
    );
  }

  // Diff state - show diff review interface
  if (
    state === LLMDisplayState.DIFF &&
    displayDiffs &&
    displayDiffs.length > 0
  ) {
    const { totalAdded, totalRemoved } = calculateTotals(displayDiffs);

    return (
      <div className="sage-ai-llm-state-display sage-ai-diff-state">
        <div
          className="sage-ai-diff-summary-bar"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <div className="sage-ai-diff-summary-info">
            <span className="sage-ai-diff-icon">
              {!isExpanded ? (
                <MENU_ICON.react className="sage-ai-diff-menu-icon" />
              ) : (
                <MENU_CLOSE_ICON.react className="sage-ai-diff-menu-icon" />
              )}
            </span>
            <span className="sage-ai-diff-cell-count">
              {displayDiffs.length} cell{displayDiffs.length !== 1 ? 's' : ''}{' '}
              modified
            </span>
            <p className="sage-ai-diff-cell-count-info">
              {totalAdded > 0 && (
                <span className="sage-ai-diff-added-count">+{totalAdded}</span>
              )}
              {totalRemoved > 0 && (
                <span className="sage-ai-diff-removed-count">
                  -{totalRemoved}
                </span>
              )}
            </p>
          </div>
          <div className="sage-ai-diff-summary-actions">
            {!allDiffsResolved && (
              <>
                <button
                  className="sage-ai-diff-btn sage-ai-diff-reject-all"
                  onClick={async e => {
                    e.stopPropagation();
                    // Reject all diffs using DiffStateService
                    for (const diff of displayDiffs) {
                      diffStateService.updateDiffState(
                        diff.cellId,
                        false,
                        diff.notebookId
                      );
                    }
                    // Also trigger the dialog action if needed
                    await AppStateService.getNotebookDiffManager().diffApprovalDialog.rejectAll();
                    setAllDiffsResolved(true);
                  }}
                  title={`Reject${diffs && diffs.length > 1 ? ' all' : ''} change${diffs && diffs.length > 1 ? 's' : ''}`}
                >
                  {diffs && diffs.length > 1 ? 'Reject All' : 'Reject'}
                </button>
                <button
                  ref={runAllButtonRef}
                  className="sage-ai-diff-btn sage-ai-diff-approve-all"
                  onClick={async e => {
                    e.stopPropagation();

                    if (isRunContext) {
                      for (const diff of displayDiffs) {
                        if (!diff.userDecision) {
                          await AppStateService.getNotebookDiffManager().diffApprovalDialog.runCell(
                            diff.cellId
                          );
                        }
                      }
                    } else {
                      await AppStateService.getNotebookDiffManager().diffApprovalDialog.approveAll();
                    }
                    setAllDiffsResolved(true);
                  }}
                  title={
                    isRunContext
                      ? `Run${diffs && diffs.length > 1 ? ' all' : ''} change${diffs && diffs.length > 1 ? 's' : ''} (Cmd/Ctrl + Enter)`
                      : `Approve${diffs && diffs.length > 1 ? 'all' : ''} change${diffs && diffs.length > 1 ? 's' : ''} (Cmd/Ctrl + Enter)`
                  }
                >
                  {isRunContext
                    ? `${diffs && diffs.length > 1 ? 'Run All' : 'Run'}`
                    : `${diffs && diffs.length > 1 ? 'Approve All' : 'Approve'}`}
                </button>
              </>
            )}
          </div>
        </div>
        {isExpanded && (
          <div className="sage-ai-diff-list">
            {displayDiffs.map((diff, index) => (
              <DiffItem
                key={`${diff.cellId}-${index}`}
                diff={diff}
                showActionsOnHover={true}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  if (state === LLMDisplayState.RUN_KERNEL) {
    return (
      <div className="sage-ai-llm-state-display sage-ai-run-kernel">
        <div className="sage-ai-llm-state-content">
          <WARNING_ICON.react className="sage-ai-llm-state-warning-icon" />
          <span className="sage-ai-llm-state-text">
            Kernel potentially outdated.
          </span>
        </div>
        <button
          ref={runButtonRef}
          className="sage-ai-llm-state-run-button"
          onClick={() => {
            void AppStateService.getChatContainerSafe()?.chatWidget.conversationService.runAllCellsAfterRestore();
          }}
          title="The kernel might be outdated due to restoring to a checkpoint (Cmd/Ctrl + Enter)"
        >
          Run all cells
        </button>
      </div>
    );
  }

  return null;
}
