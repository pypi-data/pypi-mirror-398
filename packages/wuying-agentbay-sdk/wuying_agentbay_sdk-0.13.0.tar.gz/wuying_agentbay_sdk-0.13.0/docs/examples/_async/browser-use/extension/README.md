# Extension Examples

This directory contains Python examples demonstrating browser extension management capabilities of the AgentBay SDK.

## Examples

### 1. basic_extension_usage.py
Demonstrates fundamental extension management and browser session creation:
- Uploading browser extensions to the cloud
- Creating browser sessions with extensions
- Extension synchronization and file access
- Multiple extension handling
- Proper resource cleanup

**Key features demonstrated:**
- ExtensionsService initialization and context management
- Extension upload and validation
- ExtensionOption creation for browser sessions
- Extension file access in sessions at `/tmp/extensions/`

### 2. extension_development_workflow.py
Shows a complete development workflow for browser extensions:
- Extension upload for development testing
- Test session creation with extensions
- Extension updates during development
- Iterative development cycle management
- Development resource cleanup

**Key features demonstrated:**
- ExtensionDevelopmentWorkflow class usage
- Extension versioning and updates
- Development session management
- Extension testing patterns

### 3. extension_testing_automation.py
Advanced example for automated extension testing:
- Automated test suite execution
- Multi-extension testing scenarios
- Test result reporting and analysis
- CI/CD integration patterns
- Comprehensive error handling

**Key features demonstrated:**
- ExtensionTestRunner class for automation
- Test suite configuration and execution
- Automated test reporting
- CI/CD compatible testing workflows

## Running the Examples

1. Install required dependencies:
```bash
pip install wuying-agentbay-sdk
```

2. Set your API key:
```bash
export AGENTBAY_API_KEY=your_api_key_here
```

3. Update extension paths in the examples with your actual extension ZIP files.

4. Run any example:
```bash
python basic_extension_usage.py
python extension_development_workflow.py
python extension_testing_automation.py
```

## Extension Requirements

- Extensions must be packaged as ZIP files
- Extensions must include a valid `manifest.json` file
- Extensions are synchronized to `/tmp/extensions/{extension_id}/` in browser sessions

## Best Practices

1. **Context Management**:
   - Use descriptive context names for different projects
   - Always call `cleanup()` when done
   - Let the service auto-generate contexts for simple use cases

2. **File Management**:
   - Use ZIP format for all extension packages
   - Validate file existence before upload
   - Include proper manifest.json in extensions

3. **Session Management**:
   - Use meaningful labels for sessions
   - Wait for extension synchronization before testing
   - Create one ExtensionOption per session

4. **Error Handling**:
   - Implement comprehensive error handling
   - Use try-finally blocks for cleanup
   - Validate extension configurations

## Extension File Structure

Extensions are synchronized to browser sessions at:
```
/tmp/extensions/
├── {extension_id_1}/
│   ├── manifest.json
│   ├── content.js
│   └── ... (other extension files)
├── {extension_id_2}/
│   ├── manifest.json
│   └── ... (other extension files)
└── ...
```

## Related Documentation

- [Extension API Reference](../../../../../../typescript/docs/api/browser-use/extension.md) - Complete API documentation
- [Browser Extensions Guide](../../../../../../docs/guides/browser-use/browser-extensions.md) - Tutorial and best practices
- [Browser Examples](../browser/README.md) - Additional browser automation examples

## Troubleshooting

**Extension not found in session:**
- Check that extension was uploaded successfully
- Verify session was created with proper ExtensionOption
- Wait for synchronization to complete before accessing files

**Upload failures:**
- Ensure file is in ZIP format
- Check file permissions and accessibility
- Verify API key and network connectivity

**Context errors:**
- Use unique context names to avoid conflicts
- Don't mix extensions from different sources
- Clean up contexts when no longer needed