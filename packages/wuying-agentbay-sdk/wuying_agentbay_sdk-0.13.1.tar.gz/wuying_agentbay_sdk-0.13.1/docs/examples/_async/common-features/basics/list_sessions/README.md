# List Sessions Example

This example demonstrates how to use the `list()` API to query and filter sessions in AgentBay.

## Overview

The `list()` API provides a simple and intuitive interface for querying sessions with optional filtering and pagination support. It's designed to be more user-friendly than the deprecated `list_by_labels()` API.

## Features Demonstrated

This example shows:

1. **List all sessions** - Query all sessions without any filters
2. **Filter by labels** - Query sessions that match specific labels
3. **Multiple label filtering** - Query sessions that match multiple label criteria
4. **Pagination** - Retrieve results page by page
5. **Iterate all pages** - Automatically fetch all results across multiple pages

## Prerequisites

Before running this example, ensure you have:

1. **AgentBay SDK installed**:
   ```bash
   pip install wuying-agentbay-sdk
   ```

2. **API Key configured**:
   ```bash
   export AGENTBAY_API_KEY='your-api-key-here'
   ```

## Running the Example

```bash
cd /path/to/wuying-agentbay-sdk/python/docs/examples/list_sessions
python main.py
```

## API Reference

### Method Signature

```python
async def list(
    labels: Optional[Dict[str, str]] = None,
    page: Optional[int] = None,
    limit: Optional[int] = None
) -> SessionListResult
```

### Parameters

- **labels** (Optional[Dict[str, str]]): Labels to filter sessions. All specified labels must match.
  - Default: `None` (no filtering, returns all sessions)
  - Example: `{"project": "demo", "environment": "prod"}`

- **page** (Optional[int]): Page number for pagination, starting from 1.
  - Default: `None` (returns first page)
  - Example: `2` (returns second page)

- **limit** (Optional[int]): Maximum number of items per page.
  - Default: `None` (uses default of 10)
  - Example: `20` (returns up to 20 items per page)

### Return Value

Returns a `SessionListResult` object with:

- **success** (bool): Whether the operation was successful
- **sessions** (List[Session]): List of Session objects matching the filter
- **total_count** (int): Total number of matching sessions
- **next_token** (str): Token for the next page (empty if no more pages)
- **max_results** (int): Maximum results per page
- **request_id** (str): Unique request identifier for tracking
- **error_message** (str): Error message if operation failed

## Use Cases

### 1. Session Inventory
List all sessions to get an overview of your current session inventory.

### 2. Project Management
Find all sessions for a specific project.

### 3. Environment-Specific Queries
Query sessions by environment (dev, staging, prod).

### 4. Bulk Operations
Retrieve all matching sessions and perform batch operations.

## Key Advantages over list_by_labels()

The new `list()` API offers several advantages:

1. **Simpler Interface**: No need to create `ListSessionParams` objects
2. **Intuitive Pagination**: Use familiar `page` and `limit` parameters
3. **Request Tracking**: All responses include `request_id` for debugging
4. **Cleaner Code**: More readable and maintainable code
5. **Type Safety**: Better IDE autocomplete support

## Expected Output

```
✅ AgentBay client initialized

📝 Creating test sessions...
✅ Created session 1: session-xxxxx
   Request ID: xxxxx-xxxxx-xxxxx
✅ Created session 2: session-yyyyy
   Request ID: yyyyy-yyyyy-yyyyy
✅ Created session 3: session-zzzzz
   Request ID: zzzzz-zzzzz-zzzzz

============================================================
Example 1: List all sessions (no filter)
============================================================
✅ Found 15 total sessions
📄 Showing 10 sessions on this page
🔑 Request ID: req-xxxxx-xxxxx
📊 Max results per page: 10
   1. Session ID: session-xxxxx
   2. Session ID: session-yyyyy
   3. Session ID: session-zzzzz

[... more examples ...]

============================================================
🧹 Cleaning up test sessions...
============================================================
✅ Deleted session: session-xxxxx
   Request ID: req-delete-xxxxx
✅ Deleted session: session-yyyyy
   Request ID: req-delete-yyyyy
✅ Deleted session: session-zzzzz
   Request ID: req-delete-zzzzz

✨ Demo completed successfully!
```

## Troubleshooting

### API Key Not Set
```
Error: AGENTBAY_API_KEY environment variable not set
```
**Solution**: Set your API key:
```bash
export AGENTBAY_API_KEY='your-api-key-here'
```

### No Sessions Found
```
Found 0 sessions with specified labels
```
**Solution**: Check that:
1. You have active sessions with the specified labels
2. Label keys and values match exactly (case-sensitive)
3. All specified labels must match (AND logic, not OR)

### Rate Limiting
If you encounter rate limiting, add delays between requests.

## Related Documentation

- [Session Management Guide](../../../../../../../docs/guides/common-features/basics/session-management.md)
- [AgentBay API Reference](../../../../../../../typescript/docs/api/common-features/basics/agentbay.md)
- [Label Management Example](../label_management/README.md)

## Support

For issues or questions:
- GitHub Issues: https://github.com/aliyun/wuying-agentbay-sdk/issues
- Documentation: https://github.com/aliyun/wuying-agentbay-sdk