# Context Sync Demo Example

This example demonstrates the `session.context.sync()` method for synchronizing context data with the AgentBay cloud environment.

## Overview

The example showcases:

- **Context Creation**: Creating persistent contexts for data storage
- **Context Synchronization**: Using `sync()` to sync data to cloud storage
- **Timing Analysis**: Measuring sync operation duration
- **File Management**: Creating and managing test files in the context
- **Error Handling**: Managing sync failures and API errors

## Key Features Demonstrated

### 1. Context Sync Function

The `session.context.sync()` method provides asynchronous context synchronization:

```python
# Async call - wait for completion
sync_result = session.context.sync()
if sync_result.success:
    print("✅ Sync completed successfully")
    print(f"Duration: {sync_duration:.2f} seconds")
```

### 2. Timing Analysis

The example includes timing analysis for sync operations:

- **Small files** (< 1KB): Typically under 1 second
- **Medium files** (1-10KB): Typically 1-5 seconds
- **Multiple files**: Duration depends on total size and file count

### 3. Test Data Creation

Creates structured test data to demonstrate sync functionality:

```python
test_files = [
    ("/tmp/sync_data/test_files/small.txt", "Small test file content\n" * 10),
    ("/tmp/sync_data/test_files/medium.txt", "Medium test file content\n" * 100),
    ("/tmp/sync_data/config.json", json.dumps({...}, indent=2))
]
```

### 4. Session Management

Demonstrates proper session lifecycle management:

```python
# Create session with context sync
params = CreateSessionParams()
params.context_syncs = [context_sync]
session_result = agent_bay.create(params)

# Clean up session after use
delete_result = agent_bay.delete(session)
```

## Example Structure

### Step 1: Context Creation

- Creates a persistent context for data storage using `agent_bay.context.get()`
- Configures sync policy and context sync settings

### Step 2: Session Setup

- Creates session with context synchronization enabled
- Mounts context to `/tmp/sync_data` path in the session environment

### Step 3: Test Data Creation

- Creates multiple test files of different sizes
- Sets up directory structure for organized file management
- Writes configuration and log files to demonstrate various data types

### Step 4: Context Synchronization

- Calls `session.context.sync()` to sync all data to cloud storage
- Measures and reports sync timing and success status
- Handles both success and failure scenarios with appropriate logging
