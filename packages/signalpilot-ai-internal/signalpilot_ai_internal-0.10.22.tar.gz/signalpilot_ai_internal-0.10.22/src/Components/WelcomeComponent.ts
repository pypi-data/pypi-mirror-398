import { Widget } from '@lumino/widgets';
import Anthropic from '@anthropic-ai/sdk';
import { AppStateService } from '../AppState';
import welcomeTools from '../Config/welcome_tools.json';

/**
 * WelcomeComponent - Displays a personalized welcome message using Anthropic's API
 * Attaches to the jp-Launcher-body and streams a welcome message based on workspace context
 */
export class WelcomeComponent extends Widget {
  private container: HTMLDivElement;
  private messageDiv: HTMLDivElement;
  private anthropicClient: Anthropic;
  private welcomePrompt: string = '';

  constructor() {
    super();
    this.addClass('sage-ai-welcome-component');

    // Create container
    this.container = document.createElement('div');
    this.container.className = 'sage-welcome-container';

    // Create message div where streamed content will appear
    this.messageDiv = document.createElement('div');
    this.messageDiv.className = 'sage-welcome-message';
    this.messageDiv.innerHTML =
      '<p class="sage-welcome-loading">Preparing your welcome message...</p>';

    this.container.appendChild(this.messageDiv);
    this.node.appendChild(this.container);

    // Initialize Anthropic client
    const claudeSettings = AppStateService.getClaudeSettings();
    const apiKey = claudeSettings.claudeApiKey;
    const apiUrl = claudeSettings.claudeModelUrl;

    this.anthropicClient = new Anthropic({
      apiKey: apiKey,
      baseURL: apiUrl,
      dangerouslyAllowBrowser: true
    });

    // Load welcome prompt
    this.loadWelcomePrompt();
  }

  /**
   * Load the welcome prompt from the prompts directory
   */
  private loadWelcomePrompt(): void {
    // In a browser environment, we'll need to fetch this
    // For now, using a hardcoded version that matches welcome_prompt.md
    this.welcomePrompt = `You are a knowledgeable and friendly AI assistant deeply familiar with Jupyter Lab notebooks and data science workflows. Your role is to welcome the user to their notebook environment and demonstrate your understanding of their workspace context.

**Your Task:**
Create a warm, personalized welcome message that showcases your knowledge of the user's current notebook environment. Be concise but insightful, highlighting what you observe in their workspace.

**Context Provided:**
You will receive information about the user's current notebook environment, including:
- Available notebooks and their paths
- Data files present in the workspace
- Overall workspace structure

**Welcome Message Guidelines:**
1. Start with a friendly greeting
2. Acknowledge what you see in their workspace (notebooks, data files, etc.)
3. Offer to help them get started or continue their work
4. Be encouraging and demonstrate your capabilities without being overly verbose
5. If you notice interesting patterns or opportunities in their workspace, mention them briefly
6. Keep the tone professional yet approachable

Remember: Be helpful, insightful, and ready to assist with their data science journey!`;
  }

  /**
   * Attach this component to the jp-Launcher-body selector
   */
  public attachToLauncher(): void {
    const launcherBody = document.querySelector('.jp-Launcher-content');
    if (launcherBody) {
      // Create a wrapper for our component
      const wrapper = document.createElement('div');
      wrapper.className = 'sage-welcome-wrapper';
      wrapper.appendChild(this.node);

      // Insert at the beginning of launcher body
      launcherBody.insertBefore(wrapper, launcherBody.firstChild);
    } else {
      console.warn(
        'jp-Launcher-body not found. Welcome component could not be attached.'
      );
    }
  }

  /**
   * Generate and stream the welcome message
   */
  public async generateWelcome(workspaceContext: any): Promise<void> {
    try {
      // Clear loading message
      this.messageDiv.innerHTML = '';

      // Create a container for the streamed content
      const contentDiv = document.createElement('div');
      contentDiv.className = 'sage-welcome-content';
      this.messageDiv.appendChild(contentDiv);

      // Format the workspace context for the prompt
      const contextMessage = this.formatWorkspaceContext(workspaceContext);

      const modelId = 'claude-3-7-sonnet-latest';

      // Stream the response from Anthropic
      const stream = await this.anthropicClient.messages.create({
        model: modelId,
        max_tokens: 1024,
        temperature: 0.7,
        system: this.welcomePrompt,
        messages: [
          {
            role: 'user',
            content: contextMessage
          }
        ],
        tools: welcomeTools as any,
        stream: true
      });

      let accumulatedText = '';

      // Process the stream
      for await (const event of stream) {
        if (event.type === 'content_block_start') {
          // Content block started
          continue;
        } else if (event.type === 'content_block_delta') {
          if (event.delta.type === 'text_delta') {
            accumulatedText += event.delta.text;
            // Update the display with markdown rendering
            contentDiv.innerHTML = this.renderMarkdown(accumulatedText);

            // Auto-scroll to bottom
            this.messageDiv.scrollTop = this.messageDiv.scrollHeight;
          }
        } else if (event.type === 'content_block_stop') {
          // Content block finished
          continue;
        } else if (event.type === 'message_stop') {
          // Message complete
          console.log('Welcome message streaming completed');
        }
      }
    } catch (error) {
      console.error('Error generating welcome message:', error);
      this.messageDiv.innerHTML = `
        <div class="sage-welcome-error">
          <p>⚠️ Unable to generate welcome message.</p>
          <p class="error-details">${error instanceof Error ? error.message : 'Unknown error'}</p>
        </div>
      `;
    }
  }

  /**
   * Format workspace context into a readable message
   */
  private formatWorkspaceContext(context: any): string {
    let message = "Here is the user's current notebook environment:\n\n";

    if (context.welcome_context) {
      message += context.welcome_context;
    } else {
      message += `Total notebooks found: ${context.notebook_count || 0}\n`;
      message += `Total data files found: ${context.data_file_count || 0}\n`;

      if (context.notebooks && context.notebooks.length > 0) {
        message += '\nNotebooks:\n';
        context.notebooks.forEach((nb: string) => {
          message += `- ${nb}\n`;
        });
      }

      if (context.data_files && context.data_files.length > 0) {
        message += '\nData files:\n';
        context.data_files.slice(0, 5).forEach((file: string) => {
          message += `- ${file}\n`;
        });
        if (context.data_files.length > 5) {
          message += `... and ${context.data_files.length - 5} more\n`;
        }
      }
    }

    return message;
  }

  /**
   * Simple markdown renderer for basic formatting
   */
  private renderMarkdown(text: string): string {
    // Basic markdown rendering
    let html = text;

    // Headers
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

    // Bold
    html = html.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>');

    // Italic
    html = html.replace(/\*(.*?)\*/gim, '<em>$1</em>');

    // Code
    html = html.replace(/`(.*?)`/gim, '<code>$1</code>');

    // Line breaks
    html = html.replace(/\n/gim, '<br>');

    return html;
  }

  /**
   * Remove the component from the DOM
   */
  public remove(): void {
    const wrapper = this.node.parentElement;
    if (wrapper && wrapper.className === 'sage-welcome-wrapper') {
      wrapper.remove();
    }
    this.dispose();
  }
}
