import Anthropic from '@anthropic-ai/sdk';

export interface IStreamHandlerConfig {
  onTextChunk?: (text: string) => void;
  onToolUse?: (toolUse: any) => void;
  errorLogger?: (message: any) => Promise<void>;
  isRequestCancelled: () => boolean;
}

export interface IStreamResult {
  cancelled?: boolean;
  role: string;
  content: any[];
  needsUserConfirmation?: boolean;
  [key: string]: any;
}

export interface IStreamCreationParams {
  client: Anthropic;
  modelName: string;
  messages: any[];
  tools?: any[];
  systemPrompt: string;
  extraSystemMessages?: any[];
  abortSignal: AbortSignal;
}

/**
 * Handles Anthropic API stream creation and processing
 * Separated from AnthropicService to reduce cyclic complexity
 */
export class AnthropicStreamHandler {
  private static readonly DELTA_CHUNK_THRESHOLD = 30;
  private static readonly DELTA_UPDATE_INTERVAL = 100;

  /**
   * Processes a message stream and returns the final result
   */
  static async processStream(
    stream: any,
    config: IStreamHandlerConfig,
    conversationHistory: any[]
  ): Promise<IStreamResult> {
    if (!stream) {
      const error = new Error('Message stream is undefined');
      await config.errorLogger?.({ message: error.message, stream });
      throw error;
    }

    const context = this.initializeStreamContext();
    this.setupTextChunkHandler(stream, config);

    try {
      await this.processStreamEvents(stream, context, config);

      if (config.isRequestCancelled()) {
        return this.createCancelledResult();
      }

      const finalMessage = await this.getFinalMessage(stream, config);

      return {
        ...finalMessage,
        needsUserConfirmation: context.needsUserConfirmation
      };
    } catch (error: any) {
      return this.handleStreamError(error, config, context);
    }
  }

  /**
   * Initializes the stream processing context
   */
  private static initializeStreamContext() {
    return {
      toolUseInfo: null as any,
      needsUserConfirmation: false,
      messageContent: [] as any[],
      // Track delta buffers per content block index
      deltaBuffersByIndex: new Map<
        number,
        { buffer: string; lastUpdateTime: number }
      >()
    };
  }

  /**
   * Sets up the text chunk handler for streaming
   */
  private static setupTextChunkHandler(
    stream: any,
    config: IStreamHandlerConfig
  ) {
    if (config.onTextChunk) {
      stream.on('text', (text: string) => {
        if (!config.isRequestCancelled()) {
          config.onTextChunk!(text);
        }
      });
    }
  }

  /**
   * Processes all stream events
   */
  private static async processStreamEvents(
    stream: any,
    context: any,
    config: IStreamHandlerConfig
  ) {
    for await (const event of stream) {
      if (config.isRequestCancelled()) {
        await config.errorLogger?.({
          message: 'Stream processing stopped due to cancellation',
          event,
          requestStatus: 'CANCELLED'
        });
        return;
      }

      await this.handleStreamEvent(event, context, config);
    }
  }

  /**
   * Handles individual stream events
   */
  private static async handleStreamEvent(
    event: any,
    context: any,
    config: IStreamHandlerConfig
  ) {
    switch (event.type) {
      case 'content_block_start':
        this.handleContentBlockStart(event, context, config);
        break;
      case 'content_block_delta':
        this.handleContentBlockDelta(event, context, config);
        break;
      case 'content_block_stop':
        await this.handleContentBlockStop(event, context, config);
        break;
    }
  }

  /**
   * Handles content block start events
   */
  private static handleContentBlockStart(
    event: any,
    context: any,
    config: IStreamHandlerConfig
  ) {
    const index = event.index;

    // Ensure messageContent array is large enough
    while (context.messageContent.length <= index) {
      context.messageContent.push(null as any);
    }

    if (event.content_block.type === 'text') {
      context.messageContent[index] = {
        type: 'text',
        text: ''
      };
    } else if (event.content_block.type === 'tool_use') {
      this.handleToolUseStart(event.content_block, context, config, index);
    }
  }

  /**
   * Handles tool use start
   */
  private static handleToolUseStart(
    contentBlock: any,
    context: any,
    config: IStreamHandlerConfig,
    index: number
  ) {
    context.toolUseInfo = contentBlock;

    const toolUseData = {
      type: 'tool_use',
      id: contentBlock.id,
      name: contentBlock.name,
      input: contentBlock.input,
      contentBlockIndex: index
    };

    config.onToolUse?.(toolUseData);
    // Place at the correct index (array should already be sized in handleContentBlockStart)
    context.messageContent[index] = toolUseData;

    // Initialize delta buffer for this content block index
    context.deltaBuffersByIndex.set(index, {
      buffer: '',
      lastUpdateTime: 0
    });

    // Check if this tool requires user confirmation
    if (
      contentBlock.name === 'execute_cell' ||
      contentBlock.name === 'edit_cell'
    ) {
      context.needsUserConfirmation = true;
    }
  }

  /**
   * Handles content block delta events
   */
  private static handleContentBlockDelta(
    event: any,
    context: any,
    config: IStreamHandlerConfig
  ) {
    const index = event.index;

    if (event.delta.type === 'text_delta') {
      this.handleTextDelta(event.delta, context, index);
    } else if (event.delta.type === 'input_json_delta') {
      this.handleInputJsonDelta(event.delta, context, config, index);
    }
  }

  /**
   * Handles text delta updates
   */
  private static handleTextDelta(delta: any, context: any, index: number) {
    // Index directly corresponds to position in messageContent array
    if (index >= 0 && index < context.messageContent.length) {
      const contentBlock = context.messageContent[index];
      if (contentBlock && contentBlock.type === 'text') {
        contentBlock.text += delta.text;
      }
    }
  }

  /**
   * Handles input JSON delta updates with chunking
   */
  private static handleInputJsonDelta(
    delta: any,
    context: any,
    config: IStreamHandlerConfig,
    index: number
  ) {
    // Index directly corresponds to position in messageContent array
    if (index >= 0 && index < context.messageContent.length) {
      const contentBlock = context.messageContent[index];
      if (contentBlock && contentBlock.type === 'tool_use') {
        this.processInputJsonDelta(delta, context, config, index);
      }
    }
  }

  /**
   * Processes input JSON delta with throttling
   */
  private static processInputJsonDelta(
    delta: any,
    context: any,
    config: IStreamHandlerConfig,
    contentBlockIndex: number
  ) {
    const currentTime = Date.now();
    const deltaJson = delta.partial_json;

    console.log('ON TOOL USE JSON', deltaJson);

    // Get or create delta buffer for this content block index
    let deltaBufferInfo = context.deltaBuffersByIndex.get(contentBlockIndex);
    if (!deltaBufferInfo) {
      deltaBufferInfo = { buffer: '', lastUpdateTime: 0 };
      context.deltaBuffersByIndex.set(contentBlockIndex, deltaBufferInfo);
    }

    deltaBufferInfo.buffer += deltaJson;

    const toolMessage = context.messageContent[contentBlockIndex];
    if (!toolMessage) {
      return;
    }

    const shouldUpdate =
      deltaBufferInfo.buffer.length >= this.DELTA_CHUNK_THRESHOLD ||
      currentTime - deltaBufferInfo.lastUpdateTime >=
        this.DELTA_UPDATE_INTERVAL;

    if (shouldUpdate && config.onToolUse) {
      config.onToolUse({
        type: 'tool_use_delta',
        id: toolMessage.id,
        name: toolMessage.name,
        input_delta: deltaBufferInfo.buffer
      });

      deltaBufferInfo.buffer = '';
      deltaBufferInfo.lastUpdateTime = currentTime;
    }

    // Accumulate partial JSON input
    if (!toolMessage.partialInput) {
      toolMessage.partialInput = '';
    }
    toolMessage.partialInput += deltaJson;
  }

  /**
   * Handles content block stop events
   */
  private static async handleContentBlockStop(
    event: any,
    context: any,
    config: IStreamHandlerConfig
  ) {
    const index = event.index;

    // Flush any remaining delta buffer for this content block index
    const deltaBufferInfo = context.deltaBuffersByIndex.get(index);
    if (
      deltaBufferInfo &&
      deltaBufferInfo.buffer.length > 0 &&
      config.onToolUse
    ) {
      this.flushDeltaBuffer(context, config, index);
    }

    await this.processFinalToolInput(context, config, index);
  }

  /**
   * Flushes remaining delta buffer for a specific content block index
   */
  private static flushDeltaBuffer(
    context: any,
    config: IStreamHandlerConfig,
    contentBlockIndex: number
  ) {
    const deltaBufferInfo = context.deltaBuffersByIndex.get(contentBlockIndex);
    if (!deltaBufferInfo || deltaBufferInfo.buffer.length === 0) {
      return;
    }

    // Index directly corresponds to position in messageContent array
    if (
      contentBlockIndex >= 0 &&
      contentBlockIndex < context.messageContent.length
    ) {
      const toolMessage = context.messageContent[contentBlockIndex];
      if (toolMessage && toolMessage.type === 'tool_use') {
        config.onToolUse!({
          type: 'tool_use_delta',
          id: toolMessage.id,
          name: toolMessage.name,
          input_delta: deltaBufferInfo.buffer
        });
        deltaBufferInfo.buffer = '';
      }
    }
  }

  /**
   * Processes the final tool input for a specific content block index
   */
  private static async processFinalToolInput(
    context: any,
    config: IStreamHandlerConfig,
    contentBlockIndex: number
  ) {
    try {
      // Index directly corresponds to position in messageContent array
      if (
        contentBlockIndex < 0 ||
        contentBlockIndex >= context.messageContent.length
      ) {
        return;
      }

      const toolMessage = context.messageContent[contentBlockIndex];
      if (
        !toolMessage ||
        toolMessage.type !== 'tool_use' ||
        !toolMessage.partialInput
      ) {
        return;
      }

      const fullInput = toolMessage.partialInput;
      const isValidJson =
        fullInput.trim().startsWith('{') && fullInput.trim().endsWith('}');

      if (!isValidJson) {
        return;
      }

      const parsedInput = JSON.parse(fullInput);

      // Update the tool message with parsed input
      toolMessage.input = parsedInput;

      config.onToolUse?.({
        type: 'tool_use_stop',
        id: toolMessage.id,
        name: toolMessage.name,
        input: parsedInput
      });
    } catch (parseError) {
      console.log('[AnthropicStreamHandler] Could not parse final input:', {
        messageContent: context.messageContent,
        contentBlockIndex,
        parseError
      });
    }
  }

  /**
   * Gets the final message from the stream
   */
  private static async getFinalMessage(
    stream: any,
    config: IStreamHandlerConfig
  ) {
    try {
      return await stream.finalMessage();
    } catch (error) {
      const errorMessage = {
        message: 'Error getting final message from stream',
        error: error instanceof Error ? error.message : error
      };
      await config.errorLogger?.(errorMessage);
      throw error;
    }
  }

  /**
   * Creates a cancelled result
   */
  private static createCancelledResult(): IStreamResult {
    return {
      cancelled: true,
      role: 'assistant',
      content: []
    };
  }

  /**
   * Handles stream processing errors
   */
  private static async handleStreamError(
    error: any,
    config: IStreamHandlerConfig,
    context: any
  ): Promise<IStreamResult> {
    if (error.name === 'AbortError' || config.isRequestCancelled()) {
      await config.errorLogger?.({
        message: 'Stream processing aborted due to cancellation',
        error: error instanceof Error ? error.message : error
      });
      return this.createCancelledResult();
    }

    await config.errorLogger?.({
      message: 'Error during stream processing',
      error: error instanceof Error ? error.message : error,
      messageContent: context.messageContent,
      toolUseInfo: context.toolUseInfo,
      needsUserConfirmation: context.needsUserConfirmation
    });

    throw error;
  }
}
