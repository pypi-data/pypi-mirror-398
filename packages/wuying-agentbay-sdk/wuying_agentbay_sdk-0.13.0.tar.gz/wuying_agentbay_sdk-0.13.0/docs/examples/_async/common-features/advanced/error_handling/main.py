"""
Example demonstrating comprehensive error handling with AgentBay SDK.

This example shows how to:
- Handle session creation failures
- Handle API errors gracefully
- Implement retry logic
- Handle timeout errors
- Clean up resources on failure
"""

import asyncio
import os
from typing import Optional

from agentbay import AsyncAgentBay
from agentbay import CreateSessionParams
from agentbay import AgentBayError


async def create_session_with_retry(
    agent_bay: AsyncAgentBay,
    params: CreateSessionParams,
    max_retries: int = 3,
    retry_delay: float = 2.0
):
    """Create a session with retry logic."""
    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1}/{max_retries} to create session...")
            result = await agent_bay.create(params)
            
            if result.success and result.session:
                print(f"✅ Session created successfully: {result.session.session_id}")
                return result.session
            else:
                print(f"❌ Session creation failed: {result.error_message}")
                
        except AgentBayError as e:
            print(f"❌ AgentBay error on attempt {attempt + 1}: {e}")
            
        except Exception as e:
            print(f"❌ Unexpected error on attempt {attempt + 1}: {e}")
        
        if attempt < max_retries - 1:
            print(f"Waiting {retry_delay} seconds before retry...")
            await asyncio.sleep(retry_delay)
    
    print("❌ Failed to create session after all retries")
    return None


async def safe_command_execution(session, command: str, timeout: float = 30.0):
    """Execute a command with error handling."""
    try:
        print(f"Executing command: {command}")
        result = await session.command.execute_command(command)
        
        if result.success:
            print(f"✅ Command succeeded: {result.output[:100]}")
            return result.output
        else:
            print(f"❌ Command failed: {result.error_message}")
            return None
            
    except AgentBayError as e:
        print(f"❌ AgentBay error during command execution: {e}")
        return None
        
    except Exception as e:
        print(f"❌ Unexpected error during command execution: {e}")
        return None


async def safe_file_operation(session, file_path: str, content: str):
    """Perform file operations with error handling."""
    try:
        # Try to write file
        print(f"Writing to file: {file_path}")
        write_result = await session.file_system.write_file(file_path, content)
        
        if not write_result.success:
            print(f"❌ Failed to write file: {write_result.error_message}")
            return False
        
        print(f"✅ File written successfully")
        
        # Verify by reading
        print(f"Verifying file content...")
        read_result = await session.file_system.read_file(file_path)
        
        if not read_result.success:
            print(f"❌ Failed to read file: {read_result.error_message}")
            return False
        
        if read_result.content == content:
            print(f"✅ File content verified")
            return True
        else:
            print(f"❌ File content mismatch")
            return False
            
    except AgentBayError as e:
        print(f"❌ AgentBay error during file operation: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error during file operation: {e}")
        return False


async def main():
    """Main function demonstrating error handling."""
    api_key = os.getenv("AGENTBAY_API_KEY")
    if not api_key:
        print("❌ Error: AGENTBAY_API_KEY environment variable not set")
        return
    
    agent_bay = AsyncAgentBay(api_key=api_key)
    session: Optional[object] = None
    
    try:
        print("=" * 60)
        print("Example 1: Session Creation with Retry")
        print("=" * 60)
        
        params = CreateSessionParams(image_id="linux_latest")
        session = await create_session_with_retry(agent_bay, params, max_retries=3)
        
        if not session:
            print("❌ Could not create session, exiting")
            return
        
        print("\n" + "=" * 60)
        print("Example 2: Safe Command Execution")
        print("=" * 60)
        
        # Execute a safe command
        await safe_command_execution(session, "echo 'Hello World'")
        
        # Execute a command that might take longer
        await safe_command_execution(session, "sleep 2 && echo 'Done'")
        
        # Execute a command with potential issues
        await safe_command_execution(session, "nonexistent_command")
        
        print("\n" + "=" * 60)
        print("Example 3: Safe File Operations")
        print("=" * 60)
        
        # Try to write to a valid location
        await safe_file_operation(
            session,
            "/tmp/test_error_handling.txt",
            "This is a test file for error handling"
        )
        
        # Try to write to an invalid location (should fail gracefully)
        await safe_file_operation(
            session,
            "/root/protected_file.txt",
            "This should fail"
        )
        
        print("\n" + "=" * 60)
        print("Example 4: Handling Invalid Operations")
        print("=" * 60)
        
        try:
            # Try to read a non-existent file
            result = await session.file_system.read_file("/nonexistent/file.txt")
            if not result.success:
                print(f"✅ Gracefully handled non-existent file: {result.error_message}")
        except Exception as e:
            print(f"❌ Exception when reading non-existent file: {e}")
        
        print("\n✅ Error handling examples completed")
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        
    except Exception as e:
        print(f"\n❌ Unexpected error in main: {e}")
        
    finally:
        # Always clean up resources
        if session:
            try:
                print("\n🧹 Cleaning up session...")
                delete_result = await agent_bay.delete(session)
                if delete_result.success:
                    print("✅ Session deleted successfully")
                else:
                    print(f"⚠️  Failed to delete session: {delete_result.error_message}")
            except Exception as e:
                print(f"⚠️  Error during cleanup: {e}")


if __name__ == "__main__":
    asyncio.run(main())

