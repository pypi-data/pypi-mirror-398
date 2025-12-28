// Quick Demo Examples - Copy and paste these into your code

// ============================================
// EXAMPLE 1: Simple Text Conversation
// ============================================
import { runDemoSequence } from './demo';
import type { IDemoMessage } from './demo';

const simpleDemo: IDemoMessage[] = [
  { role: 'user', content: 'Hello!' },
  { role: 'assistant', content: 'Hi! How can I help you today?' },
  { role: 'user', content: 'What can you do?' },
  {
    role: 'assistant',
    content:
      'I can help you analyze data, write code, create visualizations, and more!'
  }
];

await runDemoSequence(simpleDemo, 15);

// ============================================
// EXAMPLE 2: Data Analysis Demo
// ============================================
const dataAnalysisDemo: IDemoMessage[] = [
  {
    role: 'user',
    content: 'Can you analyze my sales data?'
  },
  {
    role: 'assistant',
    content: [
      {
        type: 'text',
        text: "I'd be happy to help! Let me read your dataset first."
      },
      {
        type: 'tool_use',
        id: 'tool_1',
        name: 'filesystem-read_dataset',
        input: { filepath: 'sales_data.csv' }
      }
    ]
  },
  {
    role: 'assistant',
    content:
      'I can see you have 150 rows of sales data. Let me create a visualization to show the trends.'
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
          content:
            'import pandas as pd\nimport matplotlib.pyplot as plt\n\ndf = pd.read_csv("sales_data.csv")\ndf.plot(x="date", y="revenue", kind="line")\nplt.title("Sales Over Time")\nplt.show()'
        }
      }
    ]
  },
  {
    role: 'assistant',
    content: [
      {
        type: 'tool_use',
        id: 'tool_3',
        name: 'notebook-run_cell',
        input: { cell_id: 'cell_1' }
      }
    ]
  },
  {
    role: 'assistant',
    content:
      'Great! The chart shows your sales have been growing steadily over the past 6 months. Would you like me to calculate some statistics?'
  }
];

await runDemoSequence(dataAnalysisDemo, 15);

// ============================================
// EXAMPLE 3: Code Debugging Demo
// ============================================
const debuggingDemo: IDemoMessage[] = [
  {
    role: 'user',
    content: 'My code is throwing an error. Can you help?'
  },
  {
    role: 'assistant',
    content: [
      {
        type: 'text',
        text: "Of course! Let me read your cells to see what's going on."
      },
      {
        type: 'tool_use',
        id: 'tool_1',
        name: 'notebook-read_cells',
        input: { start: 0, count: 5 }
      }
    ]
  },
  {
    role: 'assistant',
    content:
      "I see the issue - you're missing an import. Let me fix that for you."
  },
  {
    role: 'assistant',
    content: [
      {
        type: 'tool_use',
        id: 'tool_2',
        name: 'notebook-edit_cell',
        input: {
          cell_id: 'cell_1',
          content:
            'import pandas as pd\nimport numpy as np\n\ndata = pd.read_csv("data.csv")'
        }
      }
    ]
  },
  {
    role: 'assistant',
    content: 'Fixed! Now let me run it to make sure it works.'
  },
  {
    role: 'assistant',
    content: [
      {
        type: 'tool_use',
        id: 'tool_3',
        name: 'notebook-run_cell',
        input: { cell_id: 'cell_1' }
      }
    ]
  },
  {
    role: 'assistant',
    content:
      'Perfect! The cell ran successfully. The error was caused by the missing numpy import.'
  }
];

await runDemoSequence(debuggingDemo, 15);

// ============================================
// EXAMPLE 4: Machine Learning Demo
// ============================================
const mlDemo: IDemoMessage[] = [
  {
    role: 'user',
    content: 'I want to build a simple ML model to predict house prices.'
  },
  {
    role: 'assistant',
    content: "Great! Let's start by loading and exploring your data."
  },
  {
    role: 'assistant',
    content: [
      {
        type: 'tool_use',
        id: 'tool_1',
        name: 'notebook-add_cell',
        input: {
          cell_type: 'code',
          content:
            'import pandas as pd\nfrom sklearn.model_selection import train_test_split\nfrom sklearn.linear_model import LinearRegression\n\n# Load data\ndf = pd.read_csv("housing.csv")\nprint(df.head())\nprint(df.describe())'
        }
      }
    ]
  },
  {
    role: 'assistant',
    content: [
      {
        type: 'tool_use',
        id: 'tool_2',
        name: 'notebook-run_cell',
        input: { cell_id: 'cell_1' }
      }
    ]
  },
  {
    role: 'assistant',
    content: "Good! Now let's prepare the features and train a model."
  },
  {
    role: 'assistant',
    content: [
      {
        type: 'tool_use',
        id: 'tool_3',
        name: 'notebook-add_cell',
        input: {
          cell_type: 'code',
          content:
            '# Prepare features\nX = df[["bedrooms", "sqft", "age"]]\ny = df["price"]\n\n# Split data\nX_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)\n\n# Train model\nmodel = LinearRegression()\nmodel.fit(X_train, y_train)\n\n# Evaluate\nscore = model.score(X_test, y_test)\nprint(f"Model R² score: {score:.2f}")'
        }
      }
    ]
  },
  {
    role: 'assistant',
    content: [
      {
        type: 'tool_use',
        id: 'tool_4',
        name: 'notebook-run_cell',
        input: { cell_id: 'cell_2' }
      }
    ]
  },
  {
    role: 'assistant',
    content:
      'Excellent! Your model has a good R² score. You can now use it to make predictions.'
  }
];

await runDemoSequence(mlDemo, 15);

// ============================================
// EXAMPLE 5: Terminal Command Demo
// ============================================
const terminalDemo: IDemoMessage[] = [
  {
    role: 'user',
    content: 'Can you install the seaborn library?'
  },
  {
    role: 'assistant',
    content: [
      { type: 'text', text: "Sure! I'll use pip to install seaborn for you." },
      {
        type: 'tool_use',
        id: 'tool_1',
        name: 'terminal-execute_command',
        input: { command: 'pip install seaborn' }
      }
    ]
  },
  {
    role: 'assistant',
    content:
      'Seaborn has been installed successfully! You can now import it in your notebook.'
  }
];

await runDemoSequence(terminalDemo, 15);

// ============================================
// MANUAL CONTROL - Build Your Own Flow
// ============================================
import { sendDemoMessage, getChatMessages } from './demo';

const chatMessages = getChatMessages();
if (chatMessages) {
  // Clear and start fresh
  chatMessages['container'].innerHTML = '';
  chatMessages.addContinueButton();
  chatMessages.addSystemMessage('🎬 Custom Demo Starting...');

  // Send messages with custom delays
  await sendDemoMessage(
    chatMessages,
    {
      role: 'user',
      content: 'Your message'
    },
    20
  );

  await new Promise(resolve => setTimeout(resolve, 2000)); // 2 second pause

  await sendDemoMessage(
    chatMessages,
    {
      role: 'assistant',
      content: 'AI response'
    },
    20
  );

  chatMessages.addSystemMessage('✅ Demo Complete!');
}

// ============================================
// ADVANCED: Custom Tool Results
// ============================================
// If you need to customize tool behavior, modify generateDemoToolResult in demo.ts

/*
In demo.ts:

function generateDemoToolResult(toolName: string, input: any): any {
  switch (toolName) {
    case 'custom-tool':
      return JSON.stringify({ 
        custom: 'result',
        data: input.some_param
      });
    
    default:
      return JSON.stringify({ success: true });
  }
}
*/
