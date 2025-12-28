import { IDemoMessage } from './demo';

const REPLAY_API_BASE_URL = 'https://sage.alpinex.ai:8761';

/**
 * Fetch replay data from the backend API
 * @param replayId The replay ID from the URL parameter
 * @returns Object containing demo messages and original thread data
 */
export async function fetchReplayData(
  replayId: string
): Promise<{ messages: IDemoMessage[]; originalThreadData: any }> {
  console.log('[Replay] Fetching replay data for ID:', replayId);

  try {
    const response = await fetch(`${REPLAY_API_BASE_URL}/replay/${replayId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ error: 'Unknown error' }));
      throw new Error(
        errorData.error || `Failed to fetch replay data: ${response.status}`
      );
    }

    const data = await response.json();
    console.log('[Replay] Successfully fetched replay data:', data);

    // Convert the response to IDemoMessage format and keep original data
    const messages = convertToDemoMessages(data);
    return { messages, originalThreadData: data };
  } catch (error) {
    console.error('[Replay] Error fetching replay data:', error);
    throw error;
  }
}

/**
 * Convert API response to IDemoMessage format
 * This follows the same logic as createSampleDemoSequence in demo.ts
 */
function convertToDemoMessages(data: any): IDemoMessage[] {
  // Check if data is an array (like test_sp.json)
  if (!Array.isArray(data) || data.length === 0) {
    console.error('[Replay] Invalid data structure');
    return [];
  }

  // Get the first thread's messages
  const thread = data[0];
  if (!thread || !thread.messages) {
    console.error('[Replay] Invalid thread structure');
    return [];
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
    let demoContent: string | any[];

    if (typeof message.content === 'string') {
      demoContent = message.content;
    } else if (Array.isArray(message.content)) {
      // Filter and convert content blocks
      const contentArray = message.content as any[];
      const blocks: any[] = contentArray
        .filter(
          (block: any) => block.type === 'text' || block.type === 'tool_use'
        )
        .map((block: any): any => {
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
        })
        .filter((block: any) => block !== null);

      demoContent = blocks;
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

  return demoMessages;
}
