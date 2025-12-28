# SignalPilot Demo System

This demo system provides a tighter, more controlled way to demonstrate SignalPilot AI's capabilities without making actual API calls. It directly manipulates the chat components to simulate a conversation.

## Architecture

### Core Components

1. **demo.ts** - Main demo logic that directly interacts with ChatMessages
   - `sendDemoMessage()` - Sends individual messages (user or assistant)
   - `runDemoSequence()` - Runs a complete demo conversation
   - `createSampleDemoSequence()` - Provides a pre-built demo

2. **demo_commands.ts** - JupyterLab command registration
   - Registers the `signalpilot:demo` command
   - Accessible via command palette

3. **ChatMessages.ts** - Enhanced with `is_demo` parameter
   - `addUserMessage(message, hidden, is_demo)` - Adds user messages
   - `finalizeStreamingMessage(element, is_demo)` - Finalizes AI messages
   - `finalizeStreamingToolCall(element, is_demo)` - Finalizes tool calls
   - `addToolResult(name, id, result, data, is_demo)` - Adds tool results

## Key Features

### 1. Direct Chat Manipulation
The demo bypasses the entire API and ChatService layer:
- No network calls
- No authentication required
- Instant responses with configurable streaming delays

### 2. No History Pollution
When `is_demo = true`:
- Messages are not saved to chat history
- No persistent storage updates
- No checkpoint creation
- Clean demo that doesn't affect user's actual conversations

### 3. Streaming Simulation
Realistic streaming effects:
- Text streams character-by-character
- Tool calls appear with delays
- Tool execution is simulated
- Configurable streaming speed

## Usage

### Running the Demo

**Via Command Palette:**
1. Open Command Palette (Ctrl+Shift+C / Cmd+Shift+C)
2. Type "Start SignalPilot Demo"
3. Press Enter

**Programmatically:**
```typescript
import { runDemoSequence, createSampleDemoSequence } from './Demo/demo';

// Use the built-in sample demo
const messages = createSampleDemoSequence();
await runDemoSequence(messages, 15); // 15ms streaming delay
```

### Creating Custom Demos

```typescript
import { sendDemoMessage } from './Demo/demo';
import { AppStateService } from '../AppState';

const chatMessages = AppStateService.getChatContainer().chatWidget.messageComponent;

// User message
await sendDemoMessage(chatMessages, {
  role: 'user',
  content: 'Your question here'
}, 20);

// Assistant text response
await sendDemoMessage(chatMessages, {
  role: 'assistant',
  content: 'AI response text'
}, 20);

// Assistant with tool call
await sendDemoMessage(chatMessages, {
  role: 'assistant',
  content: [
    {
      type: 'text',
      text: 'Let me help with that.'
    },
    {
      type: 'tool_use',
      id: 'tool_123',
      name: 'notebook-add_cell',
      input: {
        cell_type: 'code',
        content: 'print("Hello")'
      }
    }
  ]
}, 20);
```

## Message Types

### User Messages
```typescript
{
  role: 'user',
  content: 'Message text'
}
```

### Assistant Text Messages
```typescript
{
  role: 'assistant',
  content: 'Response text'
}
```

### Assistant with Tool Calls
```typescript
{
  role: 'assistant',
  content: [
    {
      type: 'text',
      text: 'Optional text before tool'
    },
    {
      type: 'tool_use',
      id: 'unique_id',
      name: 'tool-name',
      input: { /* tool parameters */ }
    }
  ]
}
```

## Supported Tools

The demo system generates fake results for these tools:

- `notebook-add_cell` - Returns `cell_X` ID
- `notebook-edit_cell` - Returns cell ID
- `notebook-run_cell` - Returns success status
- `notebook-read_cells` - Returns cell data
- `filesystem-read_dataset` - Returns dataset info
- `terminal-execute_command` - Returns command output

## Streaming Configuration

Control streaming speed via the `streamingDelay` parameter:

```typescript
await runDemoSequence(messages, 10);  // Fast (10ms)
await runDemoSequence(messages, 20);  // Default (20ms)
await runDemoSequence(messages, 50);  // Slow (50ms)
```

## Implementation Details

### How Demo Mode Works

1. **Message Addition**: When `is_demo = true` is passed to message methods:
   - Messages are rendered to UI normally
   - But NOT added to `messageHistory` array
   - NOT saved via `historyManager.updateCurrentThreadMessages()`
   - NO checkpoint created

2. **Streaming**: Uses same streaming components as real messages:
   - `addStreamingAIMessage()` - Creates streaming container
   - `updateStreamingMessage()` - Adds text chunks
   - `finalizeStreamingMessage()` - Completes streaming

3. **Tool Calls**:
   - `addStreamingToolCall()` - Shows tool loading
   - `updateStreamingToolCall()` - Updates with tool details
   - `finalizeStreamingToolCall()` - Marks as complete
   - `addToolResult()` - Shows fake result

### Cleanup

Demo messages only exist in the DOM. To clear:
```typescript
const chatContainer = AppStateService.getChatContainer();
const chatMessages = chatContainer.chatWidget.messageComponent;

// Clear DOM
chatMessages['container'].innerHTML = '';

// Re-add UI elements
chatMessages.addContinueButton();
```

## Best Practices

1. **Always use `is_demo = true`** - Prevents history pollution
2. **Add delays between messages** - Makes demo feel natural
3. **Use realistic tool calls** - Match actual tool names/inputs
4. **Clear before starting** - Fresh slate for each demo
5. **Show system messages** - Indicate demo mode to users

## Example: Complete Demo Sequence

```typescript
import { runDemoSequence } from './Demo/demo';

const demoMessages = [
  {
    role: 'user',
    content: 'Analyze sales data'
  },
  {
    role: 'assistant',
    content: [
      { type: 'text', text: 'I\'ll read the dataset.' },
      {
        type: 'tool_use',
        id: 'tool_1',
        name: 'filesystem-read_dataset',
        input: { filepath: 'sales.csv' }
      }
    ]
  },
  {
    role: 'assistant',
    content: 'The dataset has 100 rows. I\'ll create a chart.'
  },
  {
    role: 'assistant',
    content: [
      {
        type: 'tool_use',
        id: 'tool_2',
        name: 'notebook-add_cell',
        input: {
          cell_type: 'code',
          content: 'import pandas as pd\ndf = pd.read_csv("sales.csv")\ndf.plot()'
        }
      }
    ]
  }
];

await runDemoSequence(demoMessages, 15);
```

## Troubleshooting

**Demo not appearing:**
- Check that chat container is initialized
- Verify notebook is open
- Check console for errors

**Messages saving to history:**
- Ensure `is_demo = true` is passed
- Check that you're using the new demo.ts methods

**Streaming too fast/slow:**
- Adjust `streamingDelay` parameter
- Lower values = faster streaming

## Future Enhancements

Possible improvements:
- Load demo scenarios from JSON files
- Interactive demo selector UI
- Demo recording from actual conversations
- Multi-step demo with user interactions
- Demo metrics and analytics
