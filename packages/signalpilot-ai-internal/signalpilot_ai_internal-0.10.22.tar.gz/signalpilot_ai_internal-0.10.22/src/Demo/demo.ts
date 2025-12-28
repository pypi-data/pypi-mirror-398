import { AppStateService } from '../AppState';
import { ChatMessages } from '../Chat/ChatMessages';
import { IToolCall, IChatMessage } from '../types';
import testHistory from './test_sp.json';
import { DemoControlPanel } from './DemoControlPanel';
import { IChatThread } from '../Chat/ChatHistoryManager';
import { v4 as uuidv4 } from 'uuid';
import {
  handleEditPlan,
  executeAllCells,
  isEditPlanTool,
  processDemoMessages
} from './demo_cell_actions';
import { JWTAuthModalService } from '../Services/JWTAuthModalService';
import { NotebookActions } from '@jupyterlab/notebook';
import { ReplayLoadingOverlayWidget } from '../Components/ReplayLoadingOverlay/ReplayLoadingOverlayWidget';
import {
  enableTakeoverMode,
  getStoredReplayId
} from '../utils/replayIdManager';
import { posthogService } from '../Services/PostHogService';

/**
 * Demo message system that directly interacts with ChatMessages
 * to add and stream messages without using the API
 *
 * CELL STREAMING CONFIGURATION:
 * To adjust the speed of cell content generation, modify CELL_STREAMING_CONFIG below:
 * - baseDelay: Higher = slower generation (in milliseconds)
 * - minChunkSize/maxChunkSize: Control characters per chunk
 * - variationFactor: Controls randomness (0-1, higher = more variation)
 */

// Global flag to control streaming vs instant mode
let isSkipToResultMode = false;
let demoControlPanel: DemoControlPanel | null = null;
let isDemoAborted = false; // Flag to abort ongoing demo
let hasHiddenLoadingOverlay = false; // Track if we've already hidden the loading overlay
let isDemoActivelyRunning = false; // Track if demo is currently running
let appInstance: any = null; // Store app instance for activating chat panel

// Track overlay elements for cleanup
const overlayElements: HTMLElement[] = [];

/**
 * Create a reusable grey overlay with tooltip
 */
function createOverlay(zIndex: number = 9999): HTMLElement {
  const overlay = document.createElement('div');
  overlay.className = 'sage-demo-overlay';
  overlay.style.cssText = `
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(128, 128, 128, 0.3);
    z-index: ${zIndex};
    cursor: not-allowed;
    pointer-events: auto;
  `;

  // Add tooltip
  overlay.title = 'Disabled on replay';

  overlayElements.push(overlay);
  return overlay;
}

/**
 * Replace send button SVG with spinner
 */
function replaceSendButtonWithSpinner(): void {
  const sendButton = document.querySelector(
    '.sage-ai-send-button'
  ) as HTMLElement;
  if (sendButton) {
    // Store original content for restoration
    sendButton.dataset.originalContent = sendButton.innerHTML;

    // Create spinner SVG
    const spinner = document.createElement('div');
    spinner.className = 'sage-demo-spinner';
    spinner.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#7A7A7A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10" opacity="0.25"/>
        <path d="M12 2a10 10 0 0 1 10 10" opacity="0.75">
          <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/>
        </path>
      </svg>
    `;

    sendButton.innerHTML = '';
    sendButton.appendChild(spinner);
  }
}

/**
 * Restore send button original SVG
 */
function restoreSendButton(): void {
  const sendButton = document.querySelector(
    '.sage-ai-send-button'
  ) as HTMLElement;
  if (sendButton && sendButton.dataset.originalContent) {
    sendButton.innerHTML = sendButton.dataset.originalContent;
    delete sendButton.dataset.originalContent;
  }
}

/**
 * Hide and disable all UI components during demo mode
 */
export function hide_all_components(): void {
  console.log('[Demo] Hiding and disabling UI components');

  // 1. Add overlay to sage-ai-chatbox-wrapper
  const chatboxWrapper = document.querySelector(
    '.sage-ai-chatbox-wrapper'
  ) as HTMLElement;
  if (chatboxWrapper) {
    chatboxWrapper.style.position = 'relative';
    const overlay = createOverlay(9999);
    chatboxWrapper.appendChild(overlay);
  }

  // 2. Replace send button SVG with spinner
  replaceSendButtonWithSpinner();

  // 3. Add overlay to sage-ai-toolbar
  const toolbar = document.querySelector('.sage-ai-toolbar') as HTMLElement;
  if (toolbar) {
    toolbar.style.position = 'relative';
    const overlay = createOverlay(9999);
    toolbar.appendChild(overlay);
  }

  // 4. Add overlay to right sidebar (lm-Widget lm-TabBar jp-SideBar jp-mod-right lm-BoxPanel-child)
  const rightSidebar = document.querySelector(
    '.lm-Widget.lm-TabBar.jp-SideBar.jp-mod-right.lm-BoxPanel-child'
  ) as HTMLElement;
  if (rightSidebar) {
    // Preserve original position, only ensure it's not static
    const currentPosition = window.getComputedStyle(rightSidebar).position;
    if (currentPosition === 'static') {
      rightSidebar.style.position = 'relative';
    }
    const overlay = createOverlay(9999);
    rightSidebar.appendChild(overlay);
  }

  // 5. Add overlay to left sidebar (lm-Widget lm-TabBar jp-SideBar jp-mod-left lm-BoxPanel-child)
  const leftSidebar = document.querySelector(
    '.lm-Widget.lm-TabBar.jp-SideBar.jp-mod-left.lm-BoxPanel-child'
  ) as HTMLElement;
  if (leftSidebar) {
    // Preserve original position, only ensure it's not static
    const currentPosition = window.getComputedStyle(leftSidebar).position;
    if (currentPosition === 'static') {
      leftSidebar.style.position = 'relative';
    }
    const overlay = createOverlay(9999);
    leftSidebar.appendChild(overlay);
  }

  // 6. Add overlay to notebook toolbar (lm-Widget jp-Toolbar jp-NotebookPanel-toolbar)
  const notebookToolbar = document.querySelector(
    '.lm-Widget.jp-Toolbar.jp-NotebookPanel-toolbar'
  ) as HTMLElement;
  if (notebookToolbar) {
    notebookToolbar.style.position = 'relative';
    const overlay = createOverlay(9999);
    notebookToolbar.appendChild(overlay);
  }

  // 7. Add overlay to TabBar (lm-Widget lm-TabBar lm-DockPanel-tabBar)
  const tabBar = document.querySelector(
    '.lm-Widget.lm-TabBar.lm-DockPanel-tabBar'
  ) as HTMLElement;
  if (tabBar) {
    tabBar.style.position = 'relative';
    const overlay = createOverlay(9999);
    tabBar.appendChild(overlay);
  }

  // 8. Add overlay to top panel (id=jp-top-panel)
  const topPanel = document.getElementById('jp-top-panel') as HTMLElement;
  if (topPanel) {
    topPanel.style.position = 'relative';
    const overlay = createOverlay(9999);
    topPanel.appendChild(overlay);
  }
}

/**
 * Show and re-enable all UI components after demo mode
 */
export function show_all_components(): void {
  console.log('[Demo] Showing and re-enabling UI components');

  // Remove all overlays
  overlayElements.forEach(overlay => {
    overlay.remove();
  });
  overlayElements.length = 0; // Clear the array

  // Restore send button
  restoreSendButton();
}

export interface IDemoTextBlock {
  type: 'text';
  text: string;
}

export interface IDemoToolUseBlock {
  type: 'tool_use';
  id: string;
  name: string;
  input: any;
  result?: string; // Optional tool result content
}

export type DemoContentBlock = IDemoTextBlock | IDemoToolUseBlock;

export interface IDemoMessage {
  role: 'user' | 'assistant';
  content: string | DemoContentBlock[];
}

/**
 * Check if the chat history container is properly rendered
 */
function isChatHistoryContainerRendered(): boolean {
  const historyContainer = document.querySelector('.sage-ai-history-container');
  if (!historyContainer || !(historyContainer instanceof HTMLElement)) {
    console.warn('[Demo] Chat history container not found');
    return false;
  }

  const chatHistory = historyContainer.querySelector('.sage-ai-chat-history');
  if (!chatHistory || !(chatHistory instanceof HTMLElement)) {
    console.warn('[Demo] Chat history element not found inside container');
    return false;
  }

  // Check if the container is visible (display is not 'none')
  const containerStyle = window.getComputedStyle(historyContainer);
  if (containerStyle.display === 'none') {
    console.warn('[Demo] Chat history container display is none');
    return false;
  }

  // Check if the new chat display is shown (it should be hidden during replay)
  const newChatDisplay = document.querySelector('.sage-ai-new-chat-display');
  if (newChatDisplay instanceof HTMLElement) {
    const newChatStyle = window.getComputedStyle(newChatDisplay);
    if (newChatStyle.display !== 'none') {
      console.warn(
        '[Demo] New chat display is visible (should be hidden during replay)'
      );
      return false;
    }
  }

  return true;
}

/**
 * Re-initialize the chat widget if not properly rendered
 * This handles cases where the chat might have been attached to the launcher
 */
async function ensureChatHistoryRendered(
  demoMessages: IDemoMessage[],
  currentMessageIndex: number
): Promise<void> {
  console.log('[Demo] Checking if chat history container is rendered...');

  if (isChatHistoryContainerRendered()) {
    console.log('[Demo] Chat history container is properly rendered');
    return;
  }

  console.warn(
    '[Demo] Chat history container is NOT rendered - re-initializing...'
  );

  // Get the chat container
  const chatContainer = AppStateService.getChatContainerSafe();
  if (!chatContainer || !chatContainer.chatWidget) {
    console.error('[Demo] Chat container not available for re-initialization');
    return;
  }

  const chatWidget = chatContainer.chatWidget;
  const chatHistoryManager = chatWidget.chatHistoryManager;
  const chatMessages = chatWidget.messageComponent;
  const currentNotebookId = AppStateService.getCurrentNotebookId();

  if (!currentNotebookId) {
    console.warn('[Demo] No notebook open, cannot re-initialize chat');
    return;
  }

  // CRITICAL: Destroy any launcher-attached chat first
  const isLauncherActive = AppStateService.isLauncherActive();
  if (isLauncherActive) {
    console.log(
      '[Demo] Launcher is active - disabling launcher mode and detaching from launcher'
    );
    AppStateService.setLauncherActive(false);

    // Find and remove the chatbox from launcher if it exists there
    const launcherBody = document.querySelector('.jp-Launcher-content');
    const wrapper = launcherBody?.querySelector(
      '.sage-chatbox-launcher-wrapper'
    );
    if (wrapper) {
      console.log('[Demo] Found chatbox in launcher, removing it');
      wrapper.remove();

      // Re-attach the chatbox to the chat container widget
      chatContainer.node.appendChild(chatWidget.node);
      console.log('[Demo] Chatbox re-attached to sidebar container');
    }
  }

  // Force show the history widget (this will hide new chat display and show history)
  chatWidget.showHistoryWidget();
  console.log('[Demo] Called showHistoryWidget to ensure proper display state');

  // Rebuild the chat history up to the current message
  console.log(
    '[Demo] Rebuilding chat history up to message index:',
    currentMessageIndex
  );

  // Create a new thread with the messages so far
  const processedMessages = demoMessages.slice(0, currentMessageIndex);

  // Get existing threads
  const threads =
    chatHistoryManager['notebookChats'].get(currentNotebookId) || [];

  // Find the current thread (should be the temporary demo thread)
  const currentThread = chatHistoryManager.getCurrentThread();

  if (currentThread) {
    // Update the current thread with processed messages
    currentThread.messages = processedMessages.map(msg => ({
      id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      role: msg.role,
      content: msg.content as any
    }));

    // Reload the thread to update the UI
    await chatMessages.loadFromThread(currentThread);
    console.log(
      '[Demo] Reloaded thread with',
      processedMessages.length,
      'messages'
    );
  }

  // Ensure the history widget is showing again (in case loadFromThread changed it)
  chatWidget.showHistoryWidget();

  console.log('[Demo] Chat history container re-initialized successfully');
}

/**
 * Send a demo message directly to the chat interface
 * This bypasses the API and directly manipulates the ChatMessages component
 */
export async function sendDemoMessage(
  chatMessages: ChatMessages,
  message: IDemoMessage,
  streamingDelay: number = 20,
  nextMessage?: IDemoMessage,
  loadingOverlay?: ReplayLoadingOverlayWidget | null,
  demoMessages?: IDemoMessage[],
  currentMessageIndex?: number
): Promise<void> {
  // CRITICAL: Ensure the chat is ALWAYS attached to the sidebar, not the launcher
  // This must happen before every message to prevent it from staying in the launcher
  const chatContainer = AppStateService.getChatContainerSafe();
  if (chatContainer && chatContainer.chatWidget) {
    // Check if the chatbox is currently in the launcher
    const launcherBody = document.querySelector('.jp-Launcher-content');
    const wrapper = launcherBody?.querySelector(
      '.sage-chatbox-launcher-wrapper'
    );

    if (wrapper) {
      console.log(
        '[Demo] Chat is in launcher - detaching and moving to sidebar'
      );

      // Disable launcher mode
      AppStateService.setLauncherActive(false);

      // Remove the wrapper from the launcher
      wrapper.remove();

      // Re-attach the chatbox to the chat container widget (sidebar)
      chatContainer.node.appendChild(chatContainer.chatWidget.node);
      console.log('[Demo] Chat re-attached to sidebar container');
    }

    // Force show the history widget (hides new chat display, shows chat history)
    chatContainer.chatWidget.showHistoryWidget();
    console.log('[Demo] Ensured chat history widget is visible');
  }

  // Activate the chat side panel to ensure it's open and visible (if app instance is available)
  if (appInstance && appInstance.shell) {
    try {
      appInstance.shell.activateById('sage-ai-chat-container');
      console.log('[Demo] Activated chat side panel');
    } catch (error) {
      console.warn('[Demo] Could not activate chat side panel:', error);
    }
  }

  // Check if chat history container is properly rendered
  // If not, re-initialize it with the chat history up to this point
  if (demoMessages && currentMessageIndex !== undefined) {
    await ensureChatHistoryRendered(demoMessages, currentMessageIndex);
  }

  if (message.role === 'user') {
    // Add user message directly
    await addDemoUserMessage(
      chatMessages,
      message.content as string,
      loadingOverlay
    );
  } else if (message.role === 'assistant') {
    // Stream assistant message
    await streamDemoAssistantMessage(
      chatMessages,
      message.content,
      streamingDelay,
      nextMessage
    );
  }
}

/**
 * Add a user message to the chat (demo mode)
 */
async function addDemoUserMessage(
  chatMessages: ChatMessages,
  content: string,
  loadingOverlay?: ReplayLoadingOverlayWidget | null
): Promise<void> {
  // Hide the loading overlay when the first user message is sent
  if (!hasHiddenLoadingOverlay && loadingOverlay) {
    console.log(
      '[Demo] Hiding loading overlay with fade-out - first user message sent'
    );
    loadingOverlay.hide(); // This now triggers fade-out animation
    hasHiddenLoadingOverlay = true;

    // Remove the overlay from DOM after fade animation completes
    setTimeout(() => {
      if (loadingOverlay && loadingOverlay.node.parentNode) {
        loadingOverlay.node.parentNode.removeChild(loadingOverlay.node);
      }
    }, 700); // Slightly longer than fade-out duration (600ms)
  }

  // Add the user message directly to the UI without saving to history
  chatMessages.addUserMessage(content, false, true); // is_demo = true

  // Small delay to simulate user input
  await delay(300);
}

/**
 * Stream an assistant message to the chat (demo mode)
 */
async function streamDemoAssistantMessage(
  chatMessages: ChatMessages,
  content: string | DemoContentBlock[],
  streamingDelay: number,
  nextMessage?: IDemoMessage
): Promise<void> {
  // Handle text content
  if (typeof content === 'string') {
    await streamDemoText(chatMessages, content, streamingDelay);
    return;
  }

  // Handle content blocks (text and tool calls)
  if (Array.isArray(content)) {
    for (const block of content) {
      if (block.type === 'text') {
        await streamDemoText(chatMessages, block.text, streamingDelay);
      } else if (block.type === 'tool_use') {
        // The tool result is now attached to the tool_use block
        await streamDemoToolUse(chatMessages, block, block.result);
      }
    }
  }
}

/**
 * Stream text content character by character
 * In skip mode, this will instantly show the full text
 */
async function streamDemoText(
  chatMessages: ChatMessages,
  text: string,
  streamingDelay: number
): Promise<void> {
  // Check if demo was aborted
  if (isDemoAborted) {
    console.log('[Demo] Aborting text streaming - demo was stopped');
    return;
  }

  // Create streaming message container
  const messageElement = chatMessages.addStreamingAIMessage();

  if (isSkipToResultMode) {
    // In skip mode, add all text at once
    await chatMessages.updateStreamingMessage(messageElement, text);
    await chatMessages.finalizeStreamingMessage(messageElement, true);
    return;
  }

  // Normal streaming mode: Stream the text in chunks
  const chunkSize = 3; // Characters per chunk
  for (let i = 0; i < text.length; i += chunkSize) {
    // Check if demo was aborted
    if (isDemoAborted) {
      console.log('[Demo] Aborting text streaming mid-stream');
      return;
    }

    const chunk = text.slice(i, i + chunkSize);
    await chatMessages.updateStreamingMessage(messageElement, chunk);
    await delay(streamingDelay);
  }

  // Finalize the streaming message (is_demo = true)
  await chatMessages.finalizeStreamingMessage(messageElement, true);
}

/**
 * Configuration for cell streaming effect
 */
export const CELL_STREAMING_CONFIG = {
  // Base delay between chunks in milliseconds (adjust this to speed up/slow down)
  baseDelay: 10,
  // Minimum chunk size in characters
  minChunkSize: 4,
  // Maximum chunk size in characters
  maxChunkSize: 10,
  // Variation factor (0-1, higher = more variation)
  variationFactor: 0.3
};

/**
 * Generate random chunk size with natural variation
 */
function getRandomChunkSize(): number {
  const { minChunkSize, maxChunkSize, variationFactor } = CELL_STREAMING_CONFIG;
  const range = maxChunkSize - minChunkSize;
  const baseSize = minChunkSize + Math.floor(Math.random() * range);
  const variation = Math.floor(
    (Math.random() - 0.5) * 2 * variationFactor * range
  );
  return Math.max(minChunkSize, Math.min(maxChunkSize, baseSize + variation));
}

/**
 * Stream cell content with LLM-like generation effect
 * In skip mode, this will instantly set the full content
 */
async function streamCellContent(
  toolService: any,
  cellId: string,
  fullContent: string,
  summary: string,
  notebookPath: string,
  isAddCell: boolean = false
): Promise<void> {
  // Check if demo was aborted
  if (isDemoAborted) {
    console.log('[Demo] Aborting cell streaming - demo was stopped');
    return;
  }

  // In skip mode, just set the full content immediately
  if (isSkipToResultMode) {
    if (isAddCell) {
      toolService.notebookTools?.edit_cell({
        cell_id: cellId,
        new_source: fullContent,
        summary: summary,
        is_tracking_id: true,
        notebook_path: notebookPath
      });
    } else {
      toolService.notebookTools?.edit_cell({
        cell_id: cellId,
        new_source: fullContent,
        summary: summary,
        is_tracking_id: cellId.startsWith('cell_'),
        notebook_path: notebookPath
      });
    }
    return;
  }

  // Normal streaming mode
  let currentContent = '';
  let position = 0;

  while (position < fullContent.length) {
    // Check if demo was aborted
    if (isDemoAborted) {
      console.log('[Demo] Aborting cell streaming mid-stream');
      return;
    }

    // Get random chunk size for natural variation
    const chunkSize = getRandomChunkSize();
    const chunk = fullContent.slice(position, position + chunkSize);
    currentContent += chunk;
    position += chunkSize;

    // Update the cell with accumulated content
    if (isAddCell) {
      // For add_cell, we need to use edit_cell to update existing cell
      toolService.notebookTools?.edit_cell({
        cell_id: cellId,
        new_source: currentContent,
        summary: summary,
        is_tracking_id: true,
        notebook_path: notebookPath
      });
    } else {
      // For edit_cell, just update normally
      toolService.notebookTools?.edit_cell({
        cell_id: cellId,
        new_source: currentContent,
        summary: summary,
        is_tracking_id: cellId.startsWith('cell_'),
        notebook_path: notebookPath
      });
    }

    // Wait before next chunk with slight random variation
    const delayVariation =
      (Math.random() - 0.5) * CELL_STREAMING_CONFIG.baseDelay * 0.2;
    await delay(CELL_STREAMING_CONFIG.baseDelay + delayVariation);
  }
}

/**
 * Stream a tool use (show tool call and execute it using ToolService)
 */
async function streamDemoToolUse(
  chatMessages: ChatMessages,
  toolUse: IDemoToolUseBlock,
  toolResultContent?: string
): Promise<void> {
  // Check if demo was aborted
  if (isDemoAborted) {
    console.log('[Demo] Aborting tool use - demo was stopped');
    return;
  }

  // Create the tool call
  const toolCall: IToolCall = {
    id: toolUse.id,
    name: toolUse.name,
    input: toolUse.input
  };

  console.log(
    '[Demo] Streaming tool use:',
    toolUse.name,
    toolUse.id,
    toolUse,
    toolResultContent
  );

  // Check if this is an edit_plan tool - handle it specially
  if (isEditPlanTool(toolUse.name) && toolResultContent) {
    // Add streaming tool call container
    const toolCallContainer = chatMessages.addStreamingToolCall();

    // Small delay to simulate thinking
    await delay(300);

    // Check abort again
    if (isDemoAborted) {
      return;
    }

    // Update the streaming tool call
    chatMessages.updateStreamingToolCall(toolCallContainer, toolCall);

    // Wait a bit to simulate tool execution starting
    await delay(500);

    // Check abort again
    if (isDemoAborted) {
      return;
    }

    // Finalize the tool call (is_demo = true)
    chatMessages.finalizeStreamingToolCall(toolCallContainer, true);

    // Execute the optimized edit_plan handler
    await delay(200);

    // Check abort again
    if (isDemoAborted) {
      return;
    }

    try {
      await handleEditPlan(toolUse, toolResultContent, chatMessages);

      // Add tool result to UI
      chatMessages.addToolResult(
        toolUse.name,
        toolUse.id,
        toolResultContent,
        {
          assistant: {
            content: [toolUse]
          }
        },
        true
      ); // is_demo = true

      const toolService = AppStateService.getToolService();

      if (toolService.notebookTools) {
        await delay(100); // Small delay before running
        const planCell = toolService.notebookTools.getPlanCell();
        const nb = toolService.notebookTools.getCurrentNotebook();
        if (planCell && nb) {
          await NotebookActions.runCells(
            nb.notebook,
            [planCell],
            nb.widget?.sessionContext
          );
        }
      }
    } catch (error) {
      console.error('Error executing edit_plan:', error);
      const errorContent = `Error: ${error instanceof Error ? error.message : String(error)}`;
      chatMessages.addToolResult(
        toolUse.name,
        toolUse.id,
        errorContent,
        {
          assistant: {
            content: [toolUse]
          }
        },
        true
      ); // is_demo = true
    }
    return;
  }

  // Add streaming tool call container
  const toolCallContainer = chatMessages.addStreamingToolCall();

  // Small delay to simulate thinking
  await delay(300);

  // Check abort again
  if (isDemoAborted) {
    return;
  }

  // Update the streaming tool call
  chatMessages.updateStreamingToolCall(toolCallContainer, toolCall);

  // Wait a bit to simulate tool execution starting
  await delay(500);

  // Check abort again
  if (isDemoAborted) {
    return;
  }

  // Finalize the tool call (is_demo = true)
  chatMessages.finalizeStreamingToolCall(toolCallContainer, true);

  // Check if this is an add_cell or edit_cell operation
  const isAddCell = toolUse.name === 'notebook-add_cell';
  const isEditCell = toolUse.name === 'notebook-edit_cell';
  const isRunCell = toolUse.name === 'notebook-run_cell';

  // In skip mode, skip run_cell operations (they'll be executed all at once at the end)
  if (isRunCell && isSkipToResultMode) {
    console.log('[Demo] Skip mode: Skipping run_cell, will execute all at end');
    chatMessages.addToolResult(
      toolUse.name,
      toolUse.id,
      'Cell execution skipped - will run all cells at end',
      {
        assistant: {
          content: [toolUse]
        }
      },
      true
    );
    return;
  }

  // Execute the tool using ToolService
  await delay(200);

  // Check abort again
  if (isDemoAborted) {
    return;
  }

  let resultContent: string;

  try {
    const toolService = AppStateService.getToolService();
    const notebookPath =
      toolUse.input.notebook_path ||
      AppStateService.getCurrentNotebook()?.context.path;
    // Handle cell operations with streaming effect
    if (isAddCell && toolUse.input.source) {
      // First, create the cell with empty content
      const cellId = toolService.notebookTools?.add_cell({
        cell_type: toolUse.input.cell_type || 'code',
        summary: toolUse.input.summary || 'Creating cell...',
        source: '', // Start with empty content
        notebook_path: notebookPath,
        position: toolUse.input.position
      });

      if (cellId) {
        // Now stream the content into the cell
        await streamCellContent(
          toolService,
          cellId,
          toolUse.input.source,
          toolUse.input.summary || 'Creating cell...',
          notebookPath,
          true // isAddCell
        );

        // Check abort before running markdown cell
        if (isDemoAborted) {
          return;
        }

        // If it's a markdown cell, run it to render the content
        const isMarkdown = toolUse.input.cell_type === 'markdown';
        const nb = toolService.notebookTools?.getCurrentNotebook();
        const { cell } =
          toolService.notebookTools?.findCellByAnyId(cellId) || {};
        if (isMarkdown && nb && cell) {
          await delay(100); // Small delay before running
          await NotebookActions.runCells(
            nb.notebook,
            [cell],
            nb.widget?.sessionContext
          );
        }

        resultContent = cellId;
      } else {
        throw new Error('Failed to create cell');
      }
    } else if (isEditCell && toolUse.input.new_source) {
      // For edit_cell, stream the new content
      await streamCellContent(
        toolService,
        toolUse.input.cell_id,
        toolUse.input.new_source,
        toolUse.input.summary || 'Editing cell...',
        notebookPath,
        false // not isAddCell
      );

      // Check abort before running markdown cell
      if (isDemoAborted) {
        return;
      }

      // If it's a markdown cell, run it to render the content
      const isMarkdown = toolUse.input.cell_type === 'markdown';
      const nb = toolService.notebookTools?.getCurrentNotebook();
      const { cell } =
        toolService.notebookTools?.findCellByAnyId(toolUse.input.cell_id) || {};
      if (isMarkdown && nb && cell) {
        await delay(100); // Small delay before running
        await NotebookActions.runCells(
          nb.notebook,
          [cell],
          nb.widget?.sessionContext
        );
      }

      resultContent = 'true';
    } else {
      // Execute other tools normally
      const result = await toolService.executeTool(toolCall);

      // Extract the content from the tool result
      if (result && result.content) {
        if (typeof result.content === 'string') {
          resultContent = result.content;
        } else if (Array.isArray(result.content)) {
          // Handle array of content blocks
          resultContent = result.content
            .map((item: any) => item.text || JSON.stringify(item))
            .join('\n');
        } else {
          resultContent = JSON.stringify(result.content);
        }
      } else {
        resultContent = JSON.stringify(result);
      }
    }
  } catch (error) {
    console.error(`Error executing tool ${toolUse.name}:`, error);
    resultContent = `Error: ${error instanceof Error ? error.message : String(error)}`;
  }

  // Check abort before adding tool result
  if (isDemoAborted) {
    return;
  }

  chatMessages.addToolResult(
    toolUse.name,
    toolUse.id,
    resultContent,
    {
      assistant: {
        content: [toolUse]
      }
    },
    true
  ); // is_demo = true
}

/**
 * Run a complete demo sequence
 * @param messages Demo messages to run
 * @param streamingDelay Delay between streaming chunks (ignored in skip mode)
 * @param showControlPanel Whether to show the control panel (default: true)
 * @param originalThreadData Optional original thread data from API (for proper history restoration)
 * @param loadingOverlay Optional loading overlay widget to hide when first message is sent
 */
export async function runDemoSequence(
  messages: IDemoMessage[],
  streamingDelay: number = 20,
  showControlPanel: boolean = true,
  originalThreadData?: any,
  loadingOverlay?: ReplayLoadingOverlayWidget | null,
  app?: any
): Promise<void> {
  const chatContainer = AppStateService.getChatContainerSafe();
  if (!chatContainer || !chatContainer.chatWidget) {
    console.error('[Demo] Chat container not available');
    throw new Error('Chat container not available');
  }

  // Store the app instance globally so it can be used in sendDemoMessage
  appInstance = app;
  console.log('[Demo] Stored app instance for chat panel activation');

  // Collapse left sidebar if it's expanded (only if app is provided)
  if (app && app.commands) {
    try {
      if (app.commands.isToggled('application:toggle-left-area')) {
        await app.commands.execute('application:toggle-left-area');
        console.log('[Demo] Collapsed left sidebar for demo mode');
      }
    } catch (error) {
      console.warn('[Demo] Could not collapse left sidebar:', error);
    }
  }

  const chatMessages = chatContainer.chatWidget.messageComponent;
  const chatHistoryManager = chatContainer.chatWidget.chatHistoryManager;
  chatMessages.scrollToBottom();

  // Reset skip mode and abort flag
  isSkipToResultMode = false;
  isDemoAborted = false;
  hasHiddenLoadingOverlay = false; // Reset overlay hidden flag

  // Store the messages and original thread data for later use
  const demoMessages = messages;
  let demoStarted = false;
  let newThread: any = null;
  const storedOriginalThreadData = originalThreadData;
  const storedLoadingOverlay = loadingOverlay;

  const startDemo = async (skipMode: boolean = false) => {
    if (demoStarted) {
      return;
    }
    demoStarted = true;
    isDemoActivelyRunning = true; // Mark demo as actively running

    isSkipToResultMode = skipMode;

    console.log(
      `[Demo] Starting demo in ${skipMode ? 'SKIP' : 'INTERACTIVE'} mode`
    );

    // Capture the load time
    posthogService.captureTimeToBeginDemo();

    // Create a new empty thread to clear chat history
    newThread = chatHistoryManager.createNewThread('Temporary Demo Thread');
    if (!newThread) {
      console.error('[Demo] Failed to create new thread');
      throw new Error('Failed to create new thread');
    }

    // Load the empty thread to clear all messages properly
    await chatMessages.loadFromThread(newThread);

    console.log(
      '[Demo] Created temporary thread and cleared chat messages:',
      newThread.id
    );

    // Hide all UI components during demo
    hide_all_components();

    // Process messages for skip mode if needed
    const processedMessages = skipMode
      ? processDemoMessages(demoMessages, true)
      : demoMessages;

    console.log(processedMessages);

    console.log(
      `[Demo] Using ${processedMessages.length} messages (${skipMode ? 'filtered' : 'original'})`
    );

    // Show demo indicator
    chatMessages.addSystemMessage(
      isSkipToResultMode
        ? '⚡ Demo Mode: Fast-forwarding to result...'
        : '🎬 Demo Mode: Interactive demonstration'
    );

    // Send each message in sequence
    for (let i = 0; i < processedMessages.length; i++) {
      // Check if demo was aborted
      if (isDemoAborted) {
        console.log('[Demo] Demo aborted, stopping message sequence');
        chatMessages.addSystemMessage('⚠️ Demo stopped');
        break;
      }

      const message = processedMessages[i];
      const nextMessage =
        i < processedMessages.length - 1 ? processedMessages[i + 1] : undefined;
      console.log(
        `[Demo] Sending message ${i + 1}/${processedMessages.length}`
      );

      await sendDemoMessage(
        chatMessages,
        message,
        streamingDelay,
        nextMessage,
        storedLoadingOverlay,
        processedMessages,
        i
      );

      // Add a pause between messages (shorter in skip mode)
      if (i < processedMessages.length - 1) {
        await delay(isSkipToResultMode ? 100 : 1000);
      }
    }

    // Only proceed with completion if not aborted
    if (!isDemoAborted) {
      // If in skip mode, execute all cells at the end
      if (isSkipToResultMode) {
        console.log('[Demo] Skip mode: Executing all cells now');
        await delay(500);
        await executeAllCells();
      }

      // Show completion message
      chatMessages.addSystemMessage('✅ Demo completed!');

      console.log('[Demo] Demo sequence completed');

      // Show all UI components again
      show_all_components();

      // Mark demo as finished and update button text
      if (demoControlPanel) {
        demoControlPanel.markDemoFinished();
        // Check if user is authenticated and hide panel if needed
        void updateDemoControlPanelVisibility();
      }

      // Delete the temporary thread and create a new thread with the demo messages
      await replaceTempThreadWithDemoThread(
        newThread.id,
        storedOriginalThreadData
      );

      // Save the notebook after demo completes
      try {
        const currentNotebook = AppStateService.getCurrentNotebook();
        if (currentNotebook) {
          await currentNotebook.context.save();
          console.log(
            '[Demo] Notebook saved successfully after demo completion'
          );
        } else {
          console.warn('[Demo] No current notebook found to save');
        }
      } catch (saveError) {
        console.error('[Demo] Error saving notebook:', saveError);
      }
    } else {
      console.log('[Demo] Demo was aborted, skipping completion steps');
      // Still show UI components even if aborted
      show_all_components();
    }

    // Mark demo as no longer actively running
    isDemoActivelyRunning = false;
  };

  const handleSkipToResult = async () => {
    console.log('[Demo] Skip to result clicked - switching to instant mode');

    // Mark demo as finished since user clicked Results
    if (demoControlPanel) {
      demoControlPanel.markDemoFinished();
      // Check if user is authenticated and hide panel if needed
      void updateDemoControlPanelVisibility();
    }

    // Set the flag to skip mode immediately
    isSkipToResultMode = true;

    // If demo hasn't started yet, start in skip mode
    if (!demoStarted) {
      await startDemo(true);
    } else {
      // Demo is already running - the flag change will affect ongoing operations
      console.log(
        '[Demo] Demo already running - switching to instant mode for remaining operations'
      );

      // Add a system message to indicate the mode change
      chatMessages.addSystemMessage('⚡ Fast-forwarding to result...');

      // Note: We'll execute all cells at the end when the demo completes
    }
  };

  if (showControlPanel) {
    // Show the control panel with callbacks
    showDemoControlPanel(
      async () => {
        // Try it yourself - create notebook and send first message
        hideDemoControlPanel();
        await tryItYourself(demoMessages);
      },
      handleSkipToResult // Skip to result
    );
  }
  await startDemo(false);
}

/**
 * Create a sample demo sequence from test_history.json
 * Returns both the demo messages and the original thread data
 */
export function createSampleDemoSequence(): {
  messages: IDemoMessage[];
  originalThreadData: any;
} {
  // Load the test history (should be an array with thread objects)
  if (!testHistory || testHistory.length === 0) {
    console.error('[Demo] No test history available');
    return { messages: [], originalThreadData: null };
  }

  // Get the first thread's messages
  const thread = testHistory[0];
  if (!thread || !thread.messages) {
    console.error('[Demo] Invalid thread structure');
    return { messages: [], originalThreadData: null };
  }

  const demoMessages: IDemoMessage[] = [];

  // Create a map of tool_use_id to tool_result content for easy lookup
  const toolResultMap = new Map<string, string>();

  // First pass: collect all tool results
  for (const message of thread.messages) {
    if (message.role === 'user' && Array.isArray(message.content)) {
      for (const block of message.content) {
        if (
          block.type === 'tool_result' &&
          'tool_use_id' in block &&
          'content' in block
        ) {
          toolResultMap.set(block.tool_use_id, block.content);
        }
      }
    }
  }

  // Convert each message to demo format
  for (const message of thread.messages) {
    // Skip tool_result messages (they're attached to tool_use blocks now)
    if (message.role === 'user' && Array.isArray(message.content)) {
      const hasToolResult = message.content.some(
        (block: any) => block.type === 'tool_result'
      );
      if (hasToolResult) {
        continue; // Skip tool results - they'll be accessed from toolResultMap
      }
    }

    // Skip diff_approval messages (these are internal)
    if (message.role === 'diff_approval') {
      continue;
    }

    // Convert message content to demo format
    let demoContent: string | DemoContentBlock[];

    if (typeof message.content === 'string') {
      demoContent = message.content;
    } else if (Array.isArray(message.content)) {
      // Filter and convert content blocks
      const contentArray = message.content as any[];
      const blocks: (DemoContentBlock | null)[] = contentArray
        .filter(
          (block: any) => block.type === 'text' || block.type === 'tool_use'
        )
        .map((block: any): DemoContentBlock | null => {
          if (block.type === 'text') {
            return {
              type: 'text' as const,
              text: block.text
            };
          } else if (block.type === 'tool_use') {
            // Attach the tool result content to the tool_use block
            const toolResult = toolResultMap.get(block.id);
            return {
              type: 'tool_use' as const,
              id: block.id,
              name: block.name,
              input: block.input,
              result: toolResult // Add the result to the block
            };
          }
          return null;
        });

      demoContent = blocks.filter(
        (block): block is DemoContentBlock => block !== null
      );
    } else {
      // Skip messages with unknown content format
      continue;
    }

    // Create demo message
    const demoMessage: IDemoMessage = {
      role: message.role as 'user' | 'assistant',
      content: demoContent
    };

    demoMessages.push(demoMessage);
  }

  return { messages: demoMessages, originalThreadData: testHistory };
}

/**
 * Utility function to delay execution
 * When in skip mode, returns immediately
 */
function delay(ms: number): Promise<void> {
  if (isSkipToResultMode) {
    return Promise.resolve();
  }
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Helper function to get ChatMessages instance from AppState
 */
export function getChatMessages(): ChatMessages | null {
  const chatContainer = AppStateService.getChatContainerSafe();
  return chatContainer?.chatWidget?.messageComponent || null;
}

/**
 * Create a new thread from demo messages and switch to it
 */
// eslint-disable-next-line @typescript-eslint/no-unused-vars
async function createThreadFromDemo(
  demoMessages: IDemoMessage[]
): Promise<void> {
  const chatContainer = AppStateService.getChatContainerSafe();
  if (!chatContainer || !chatContainer.chatWidget) {
    console.error('[Demo] Chat container not available for thread creation');
    return;
  }

  const chatHistoryManager = chatContainer.chatWidget.chatHistoryManager;
  const chatMessages = chatContainer.chatWidget.messageComponent;
  const currentNotebookId = AppStateService.getCurrentNotebookId();

  if (!currentNotebookId) {
    console.warn('[Demo] No notebook open, cannot create thread');
    return;
  }

  // Convert demo messages to IChatMessage format
  const threadMessages: IChatMessage[] = [];

  for (const demoMsg of demoMessages) {
    const message: IChatMessage = {
      id: uuidv4(),
      role: demoMsg.role,
      content: demoMsg.content as any
    };
    threadMessages.push(message);
  }

  // Create a new thread with these messages
  const newThread: IChatThread = {
    id: chatHistoryManager['generateThreadId'](),
    name: 'Demo: S&P 500 Analysis',
    messages: threadMessages,
    lastUpdated: Date.now(),
    contexts: new Map(),
    message_timestamps: new Map(),
    continueButtonShown: false
  };

  // Add the thread to the notebook
  const threads =
    chatHistoryManager['notebookChats'].get(currentNotebookId) || [];
  threads.unshift(newThread); // Add at the beginning
  chatHistoryManager['notebookChats'].set(currentNotebookId, threads);

  // Save to storage
  await chatHistoryManager['saveNotebookToStorage'](currentNotebookId);

  // Switch to the new thread
  chatHistoryManager['currentThreadId'] = newThread.id;
  await chatHistoryManager['storeCurrentThreadInLocalStorage'](
    currentNotebookId,
    newThread.id
  );

  // Load the thread into the UI
  await chatMessages.loadFromThread(newThread);

  // Update thread name display
  const threadNameDisplay = chatContainer.chatWidget['threadNameDisplay'];
  if (threadNameDisplay) {
    threadNameDisplay.textContent = newThread.name;
  }

  console.log('[Demo] Created and switched to new thread:', newThread.id);
}

/**
 * Replace temporary thread with a new thread using the original chat history from the endpoint/JSON
 * @param tempThreadId The temporary thread ID to replace
 * @param originalThreadData The original thread data from the API or JSON file
 */
async function replaceTempThreadWithDemoThread(
  tempThreadId: string,
  originalThreadData: any
): Promise<void> {
  const chatContainer = AppStateService.getChatContainerSafe();
  if (!chatContainer || !chatContainer.chatWidget) {
    console.error('[Demo] Chat container not available for thread replacement');
    return;
  }

  const chatHistoryManager = chatContainer.chatWidget.chatHistoryManager;
  const chatMessages = chatContainer.chatWidget.messageComponent;
  const currentNotebookId = AppStateService.getCurrentNotebookId();

  if (!currentNotebookId) {
    console.warn('[Demo] No notebook open, cannot replace thread');
    return;
  }

  // Get existing threads
  const threads =
    chatHistoryManager['notebookChats'].get(currentNotebookId) || [];

  // Remove the temporary thread
  const filteredThreads = threads.filter(t => t.id !== tempThreadId);

  // Use the original thread data from the endpoint/JSON
  if (!originalThreadData) {
    console.error('[Demo] No original thread data available');
    return;
  }

  // Support both array format (like test_sp.json) and direct thread object
  let originalThread = originalThreadData;
  if (Array.isArray(originalThreadData) && originalThreadData.length > 0) {
    originalThread = originalThreadData[0];
  }

  if (!originalThread || !originalThread.messages) {
    console.error('[Demo] Invalid thread structure in original data');
    return;
  }

  // Generate thread name from first user message (same logic as ThreadManager)
  let threadName = 'Demo Chat';
  const firstUserMessage = originalThread.messages.find(
    (msg: any) => msg.role === 'user' && typeof msg.content === 'string'
  );

  if (firstUserMessage && typeof firstUserMessage.content === 'string') {
    // Use the same paraphrasing logic as ThreadManager
    const words = firstUserMessage.content.split(/\s+/);
    const selectedWords = words.slice(0, Math.min(8, words.length));
    threadName = selectedWords.join(' ');

    // Truncate if too long
    if (threadName.length > 30) {
      threadName = threadName.substring(0, 27) + '...';
    }
  }

  // Create a new thread using the original messages from the endpoint/JSON
  const newThread: IChatThread = {
    id: chatHistoryManager['generateThreadId'](),
    name: threadName,
    messages: originalThread.messages,
    lastUpdated: Date.now(),
    contexts: new Map(),
    message_timestamps: new Map(),
    continueButtonShown: false
  };

  // Add the new thread at the beginning
  filteredThreads.unshift(newThread);
  chatHistoryManager['notebookChats'].set(currentNotebookId, filteredThreads);

  // Save to storage
  await chatHistoryManager['saveNotebookToStorage'](currentNotebookId);

  // Switch to the new thread
  chatHistoryManager['currentThreadId'] = newThread.id;
  await chatHistoryManager['storeCurrentThreadInLocalStorage'](
    currentNotebookId,
    newThread.id
  );

  // Load the thread into the UI
  await chatMessages.loadFromThread(newThread);

  // Update thread name display
  const threadNameDisplay = chatContainer.chatWidget['threadNameDisplay'];
  if (threadNameDisplay) {
    threadNameDisplay.textContent = newThread.name;
  }

  console.log(
    '[Demo] Replaced temporary thread with original chat history:',
    newThread.id,
    'Name:',
    threadName
  );
}

/**
 * Show the demo control panel
 * @param onTryIt Callback for when user clicks "Takeover"
 * @param onSkip Callback for when user clicks "Results"
 * @param container Optional container element to attach the panel to. If not provided, attempts to get it from ChatBoxWidget.
 */
export function showDemoControlPanel(
  onTryIt: () => void,
  onSkip: () => void,
  container?: HTMLElement
): DemoControlPanel {
  // Clean up existing panel if any
  if (demoControlPanel) {
    demoControlPanel.detach();
  }

  demoControlPanel = new DemoControlPanel(onTryIt, onSkip);

  // If container not provided, try to get it from ChatBoxWidget
  let targetContainer = container;
  if (!targetContainer) {
    const chatContainer = AppStateService.getChatContainerSafe();
    if (chatContainer?.chatWidget) {
      targetContainer =
        chatContainer.chatWidget.getStateDisplayContainer() || undefined;
    }
  }

  demoControlPanel.attach(targetContainer);

  return demoControlPanel;
}

/**
 * Check if user is authenticated and hide demo panel if needed
 * This should be called after authentication state changes
 */
export async function updateDemoControlPanelVisibility(): Promise<void> {
  // Only hide if demo is not actively running
  const isDemoMode = AppStateService.isDemoMode();

  if (!isDemoActivelyRunning && isDemoMode && demoControlPanel) {
    // Check if user is authenticated
    const { JupyterAuthService } = await import(
      '../Services/JupyterAuthService'
    );
    const isAuthenticated = await JupyterAuthService.isAuthenticated();

    if (isAuthenticated) {
      console.log(
        '[Demo] User is authenticated and demo is not running - hiding demo panel completely'
      );
      hideDemoControlPanel(true); // Pass true to completely hide the panel
    }
  }
}

/**
 * Hide and cleanup the demo control panel
 * @param completelyHide If true, hide the entire panel. If false, just hide the skip button.
 */
export function hideDemoControlPanel(completelyHide: boolean = false): void {
  if (demoControlPanel) {
    if (completelyHide) {
      // Completely hide and cleanup the panel
      demoControlPanel.hide();
      setTimeout(() => {
        if (demoControlPanel) {
          demoControlPanel.detach();
          demoControlPanel = null;
        }
      }, 300);
    } else {
      // Just hide the skip button (old behavior)
      demoControlPanel.hideSkipButton();
      setTimeout(() => {
        demoControlPanel?.hideSkipButton();
      }, 300);
    }
  }

  // Make sure to re-enable all components when control panel is hidden
  if (completelyHide) {
    show_all_components();
  }
}

/**
 * Try it yourself! - Create a new notebook and send the first prompt
 * If demo is finished, only show login modal without takeover logic
 */
async function tryItYourself(demoMessages: IDemoMessage[]): Promise<void> {
  console.log('[Takeover] Try it yourself clicked - stopping demo');

  // Check if demo is finished (via Results or natural completion)
  const isDemoFinished = demoControlPanel?.getDemoFinished() || false;

  if (isDemoFinished) {
    // Demo is finished - this is "Login to Chat" mode
    console.log('[Takeover] Demo finished - showing login modal only');

    // Check if user is already authenticated
    const { JupyterAuthService } = await import(
      '../Services/JupyterAuthService'
    );
    const isAuthenticated = await JupyterAuthService.isAuthenticated();

    if (!isAuthenticated) {
      // User is not authenticated - save current notebook path and show the JWT modal
      const currentNotebook = AppStateService.getCurrentNotebook();
      if (currentNotebook) {
        const notebookPath = currentNotebook.context.path;
        console.log(
          '[Takeover] Storing notebook path for later:',
          notebookPath
        );

        // Save the notebook first (using notebook tracker)
        try {
          await currentNotebook.context.save();
          console.log('[Takeover] Notebook saved successfully');
        } catch (saveError) {
          console.error('[Takeover] Error saving notebook:', saveError);
        }

        // Store the notebook path in localStorage
        const { storeLastNotebookPath } = await import(
          '../utils/replayIdManager'
        );
        storeLastNotebookPath(notebookPath);
      }

      const jwtModalService = JWTAuthModalService.getInstance();
      jwtModalService.show();
    } else {
      // User is already authenticated - just hide the demo control panel completely
      console.log(
        '[Takeover] User already authenticated, hiding demo panel completely'
      );
      hideDemoControlPanel(true);
    }

    return; // Exit early - don't do takeover logic
  }

  // IMMEDIATELY stop the demo
  isDemoAborted = true;
  console.log('[Takeover] Demo stopped');

  // Show all UI components when user wants to try it themselves
  show_all_components();

  // Find the first user message to send when they return
  const firstUserMessage = demoMessages.find(msg => msg.role === 'user');
  if (!firstUserMessage || typeof firstUserMessage.content !== 'string') {
    console.error('[Takeover] No valid first user message found');
    return;
  }

  // Check if user is already authenticated
  const { JupyterAuthService } = await import('../Services/JupyterAuthService');
  const isAuthenticated = await JupyterAuthService.isAuthenticated();

  if (isAuthenticated) {
    // User is already authenticated - skip to after-login steps immediately
    console.log(
      '[Takeover] User is authenticated - proceeding with takeover immediately'
    );
    // Set takeover mode in AppState (no localStorage needed for authenticated users)
    AppStateService.setTakeoverMode(true, firstUserMessage.content);
    await handleTakeoverAfterAuth(firstUserMessage.content);
  } else {
    // User is not authenticated - store takeover data in localStorage AND AppState
    console.log(
      '[Takeover] User not authenticated - storing takeover data and showing login'
    );

    const replayId = getStoredReplayId();
    if (replayId) {
      enableTakeoverMode({
        messages: firstUserMessage.content,
        replayId: replayId
      });
      // Also set in AppState for immediate use
      AppStateService.setTakeoverMode(true, firstUserMessage.content);
      console.log('[Takeover] Takeover mode enabled with first message');
    }

    // Show the JWT modal for the user to sign in
    const jwtModalService = JWTAuthModalService.getInstance();
    jwtModalService.show();
  }
}

/**
 * Handle takeover after authentication
 * Creates new notebook, puts prompt in chatbox, and sends message
 */
export async function handleTakeoverAfterAuth(
  firstMessage: string
): Promise<void> {
  console.log('[Takeover] Handling takeover after authentication');

  try {
    // Add waits like how we wait for replay (500ms or reset url hits race condition)
    await new Promise(resolve => setTimeout(resolve, 500));
    console.log('[Takeover] Initial wait completed');

    // Wait for essential services to be initialized
    let retries = 50;
    while (retries > 0) {
      const notebookTools = AppStateService.getNotebookTools();
      const chatContainer = AppStateService.getChatContainerSafe();

      if (notebookTools && chatContainer && chatContainer.chatWidget) {
        console.log('[Takeover] All services are ready');
        break;
      }

      await new Promise(resolve => setTimeout(resolve, 200));
      retries--;
    }

    if (retries === 0) {
      throw new Error('Timeout waiting for services to initialize');
    }

    const notebookTools = AppStateService.getNotebookTools();
    if (!notebookTools) {
      throw new Error('NotebookTools not available');
    }

    // Clear takeover flag and data from localStorage
    const { disableTakeoverMode } = await import('../utils/replayIdManager');
    disableTakeoverMode();
    console.log('[Takeover] Cleared takeover mode from localStorage');

    // Clear from AppState but keep the prompt for sending
    const takeoverPrompt = AppStateService.getTakeoverPrompt();
    AppStateService.setTakeoverMode(false, null);
    console.log('[Takeover] Cleared takeover mode from AppState');

    // Create a new notebook
    console.log('[Takeover] Creating new notebook with tracking');
    const timestamp = new Date()
      .toISOString()
      .replace(/[:.]/g, '-')
      .slice(0, -5);
    const notebookName = `takeover-${timestamp}.ipynb`;

    const result = await notebookTools.createNotebookWithTracking(notebookName);

    if (!result.success) {
      throw new Error('Failed to create notebook for takeover');
    }

    console.log(`[Takeover] Notebook created with ID: ${result.notebookId}`);

    // Wait for notebook to open
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Get the chat container and set up the message
    const chatContainer = AppStateService.getChatContainerSafe();
    if (!chatContainer || !chatContainer.chatWidget) {
      throw new Error('Chat container not available');
    }

    const chatWidget = chatContainer.chatWidget;
    const inputManager = chatWidget.inputManager;

    // Create a new chat thread for this takeover session
    console.log('[Takeover] Creating new chat thread');
    const newThread = await chatWidget.threadManager.createNewThread();
    if (!newThread) {
      console.warn('[Takeover] Failed to create new thread, continuing anyway');
    } else {
      console.log('[Takeover] Created new thread:', newThread.id);
    }

    // Show the chat widget
    chatWidget.showHistoryWidget();

    // Wait a bit for UI to be ready
    await new Promise(resolve => setTimeout(resolve, 500));

    // Use the prompt we saved earlier (or the parameter if AppState was cleared)
    const promptToSend = takeoverPrompt || firstMessage;

    // Put the takeover prompt in the chatbox
    inputManager.setInputValue(promptToSend);
    console.log('[Takeover] Set first message in chatbox:', promptToSend);

    // Send the message
    await inputManager.sendMessage();
    console.log('[Takeover] Sent first message');

    console.log('[Takeover] Takeover completed successfully');
  } catch (error) {
    console.error('[Takeover] Error during takeover after auth:', error);
    // Clear takeover mode on error
    AppStateService.setTakeoverMode(false, null);
    alert(
      `Takeover failed: ${error instanceof Error ? error.message : String(error)}`
    );
  }
}
