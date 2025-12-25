# MCP Tool Direct Call Example (Python)

This example demonstrates how to list available MCP tools and call them directly using the AgentBay Python SDK.

## Prerequisites

- Python 3.8 or higher
- AgentBay Python SDK installed (`pip install wuying-agentbay-sdk`)
- AgentBay API Key (set as environment variable `AGENTBAY_API_KEY`)

## Running the Example

```bash
# Set your API key
export AGENTBAY_API_KEY=your_api_key_here

# Run the example
cd python/docs/examples/common-features/advanced/mcp_tool_direct_call
python main.py
```

## What This Example Does

1. **Creates a Session**: Initializes an AgentBay session
2. **Lists MCP Tools**: Retrieves all available MCP tools using `session.list_mcp_tools()`
3. **Finds Shell Tool**: Locates the 'shell' tool and displays its details
4. **Calls Shell Tool**: Executes commands using `session.call_mcp_tool()`:
   - Echo command: `echo 'Hello from MCP Tool!'`
   - Directory command: `pwd`
   - Error handling: Invalid command demonstration
5. **Cleanup**: Properly deletes the session

## Expected Output

```
Initializing AgentBay client...

1. Creating session...
✓ Session created successfully
  Session ID: sess-xxxxx
  Request ID: req-xxxxx

2. Listing available MCP tools...
✓ Found 69 MCP tools
  Request ID: req-xxxxx

  Available tools (showing first 10):
  1. get_resource
     Description: The command to retrieve a wuying mcp runtime URL...
     Server: mcp-server

  2. system_screenshot
     Description: Captures a full-screen screenshot...
     Server: mcp-server

  ...

3. Finding 'shell' tool details...
✓ Found 'shell' tool
  Description: Executes an shell command with timeout...
  Server: wuying_shell
  Input Schema:
    {
      "type": "object",
      "required": ["command", "timeout_ms"],
      "properties": {
        "command": {
          "type": "string",
          "description": "client input command"
        },
        "timeout_ms": {
          "type": "integer",
          "default": 1000,
          "description": "Command execution timeout (unit: milliseconds)..."
        }
      }
    }

4. Calling 'shell' tool...
✓ Tool call successful
  Request ID: req-xxxxx
  Output:
    Hello from MCP Tool!

5. Calling 'shell' tool with different command...
✓ Tool call successful
  Request ID: req-xxxxx
  Current directory:
    /home/wuying

6. Demonstrating error handling (invalid command)...
✓ Error handled correctly
  Request ID: req-xxxxx
  Error message: Execution failed. Error code:127 Error message: sh: 1: this_command_does_not_exist_12345: not found

7. Cleaning up...
✓ Session deleted successfully
  Request ID: req-xxxxx

============================================================
Example completed successfully!
============================================================
```

## Key API Methods

### `session.list_mcp_tools()`

Lists all available MCP tools for the session.

**Returns:** `McpToolsResult` containing:
- `tools`: List of `McpTool` objects
- `request_id`: API request identifier

### `session.call_mcp_tool(tool_name, args)`

Calls an MCP tool directly.

**Parameters:**
- `tool_name` (str): Name of the MCP tool
- `args` (dict): Tool arguments

**Returns:** `McpToolResult` containing:
- `success` (bool): Whether the call succeeded
- `data` (str): Tool output
- `error_message` (str): Error message if failed
- `request_id` (str): API request identifier

## Use Cases

This direct MCP tool calling approach is useful when you need to:

1. **Discover Available Tools**: List all tools before deciding which to use
2. **Call Tools Directly**: Bypass module-specific wrappers for direct access
3. **Custom Tool Integration**: Build custom workflows with any available tool
4. **Tool Exploration**: Inspect tool schemas and test different arguments

## Related Documentation

- [Session API Reference](../../../../../../docs/api/async/async-session.md)
- [Common Features Guide](../../../../../../../docs/guides/common-features/README.md)

