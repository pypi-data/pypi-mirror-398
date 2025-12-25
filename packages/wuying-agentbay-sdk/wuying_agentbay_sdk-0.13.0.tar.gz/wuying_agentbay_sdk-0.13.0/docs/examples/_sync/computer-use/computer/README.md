# Windows Application Management Example

This example demonstrates how to use the AgentBay SDK to manage desktop applications on Windows.

## Overview

The example shows a complete workflow:

1. **Find installed applications** - Discover all applications available in the Windows environment
2. **Launch an application** - Start Notepad as an example
3. **Monitor running applications** - List currently visible applications with windows
4. **Stop the application** - Gracefully terminate the running application

## Prerequisites

- Python 3.7+
- AgentBay SDK
- Valid `AGENTBAY_API_KEY` environment variable

## Installation

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install AgentBay SDK
pip install -e /path/to/wuying-agentbay-sdk/python
```

## Usage

```bash
# Set your API key
export AGENTBAY_API_KEY="your_api_key_here"

# Run the example
python windows_app_management_example.py
```

## What the Example Does

### Step 1: Finding Installed Applications

```python
apps_result = session.computer.get_installed_apps(
    start_menu=True,
    desktop=False,
    ignore_system_apps=True
)
```

Discovers all installed applications in the Windows start menu, filtering out system apps.

### Step 2: Finding Target Application

Searches for Notepad in the list of installed applications. Falls back to the default Windows path if not found.

### Step 3: Launching Application

```python
start_result = session.computer.start_app(notepad_cmd)
```

Starts Notepad and returns information about all spawned processes.

### Step 4: Monitoring Running Applications

```python
visible_result = session.computer.list_visible_apps()
```

Lists all applications with visible windows currently running.

### Step 5: Stopping Application

```python
# Method 1: Stop by Process ID
stop_result = session.computer.stop_app_by_pid(pid)

# Method 2: Stop by Process Name (fallback)
stop_result = session.computer.stop_app_by_pname(process_name)
```

Attempts to stop the application, first by PID, then by process name if needed.

## Expected Output

```
================================================================================
Windows Application Management Example
================================================================================

Initializing AgentBay client...
✅ Client initialized

Creating Windows session...
  Attempt 1/2...
✅ Session created: session-xxxxxxxxxxxxxxxxx

================================================================================
Step 1: Finding installed applications...
================================================================================
✅ Found 120 installed applications

First 5 applications:

1. Notepad
   Start Command: C:\Windows\System32\notepad.exe

2. Paint
   Start Command: C:\Windows\System32\mspaint.exe

...

================================================================================
Step 2: Finding Notepad application...
================================================================================
✅ Found application: Notepad
Start Command: C:\Windows\System32\notepad.exe

================================================================================
Step 3: Launching application...
================================================================================
✅ Application started with 1 process(es)
  - notepad.exe (PID: 12345)
    Command: C:\Windows\System32\notepad.exe

================================================================================
Step 4: Waiting for application to load...
================================================================================
Waiting 5 seconds...
✅ Wait complete

================================================================================
Step 5: Checking running applications...
================================================================================
✅ Found 1 visible application(s)
  - notepad.exe (PID: 12345)

================================================================================
Step 6: Stopping application...
================================================================================
Attempting to stop process by PID: 12345
✅ Application stopped successfully (by PID)

================================================================================
Workflow Summary
================================================================================
✅ Session creation: Success
✅ Get installed apps: 120 applications found
✅ Find target app: Found
✅ Start application: 1 processes started
✅ List visible apps: 1 visible applications
✅ Stop application: Success
================================================================================

🎉 Workflow completed successfully!

================================================================================
Cleaning up session...
================================================================================
✅ Session deleted
```

## Features Demonstrated

- **Session Management**: Creating and cleaning up Windows sessions
- **Application Discovery**: Finding installed desktop applications
- **Process Management**: Starting and stopping applications
- **Process Monitoring**: Listing visible applications
- **Error Handling**: Robust error handling with fallback strategies
- **Retry Logic**: Automatic retry for resource creation delays

## API Methods Used

| Method | Purpose |
|--------|---------|
| `session.computer.get_installed_apps()` | Get list of installed applications |
| `session.computer.start_app()` | Start an application |
| `session.computer.list_visible_apps()` | List currently visible applications |
| `session.computer.stop_app_by_pid()` | Stop application by process ID |
| `session.computer.stop_app_by_pname()` | Stop application by process name |

## Troubleshooting

### Resource Creation Delay

If you see "Resource creation in progress" message, the script will automatically wait and retry. This is normal for Windows sessions.

### Application Not Found

The example uses Notepad which is available on all Windows systems. If you want to use a different application:

1. Run the example once to see the list of available applications
2. Modify the code to search for your target application
3. Update the start command accordingly

## Related Documentation

- [Computer Application Management Guide](../../../../../../docs/guides/computer-use/computer-application-management.md)
- [Session Management](../../../../../../docs/guides/common-features/basics/session-management.md)
- [Computer UI Automation](../../../../../../docs/guides/computer-use/computer-ui-automation.md)

## License

This example is part of the Wuying AgentBay SDK.
