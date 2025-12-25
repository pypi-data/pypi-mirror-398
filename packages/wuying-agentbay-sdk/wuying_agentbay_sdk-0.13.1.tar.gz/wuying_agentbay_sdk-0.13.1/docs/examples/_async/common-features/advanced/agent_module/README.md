# Agent Module Example

This example demonstrates how to use the Agent module to execute AI-powered tasks using natural language descriptions.

## Overview

The Agent module allows you to execute complex tasks using human-readable instructions, monitor task status, and terminate running tasks. This capability extends the functionality of cloud sessions by adding AI-powered automation.

## Running the Example

1. Ensure you have the AgentBay SDK installed
2. Set the `AGENTBAY_API_KEY` environment variable with your valid API key
3. Run the example:

```bash
cd docs/examples/python/agent_module
python main.py
```

## What the Example Does

1. Initializes the AgentBay client with your API key
2. Creates a new session
3. Executes a simple task using the Agent module ("Create a word document, input some words and save the document.")
4. Displays the task results
5. Cleans up by deleting the session

## Key Concepts

- **Session Creation**: All Agent operations happen within a session context
- **Task Execution**: Tasks are executed using natural language descriptions
- **Result Handling**: Task results include success status, output, and error information
- **Resource Management**: Sessions should be properly deleted when no longer needed

## Next Steps

Try modifying the task description to perform different operations, such as:
- "Find out the current weather in New York City by Google/Baidu"
- "Copy all the text files from folder A to folder B"
- "Navigate to bilibili.com and search for 'Wuying AgentBay ' and play the first video."