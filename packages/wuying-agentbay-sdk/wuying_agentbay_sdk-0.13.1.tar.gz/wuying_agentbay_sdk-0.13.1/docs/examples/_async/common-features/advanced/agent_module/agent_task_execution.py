"""
Agent Task Execution Example

This example demonstrates:
1. Async task execution
2. Task status monitoring
3. Task result retrieval
"""

import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from agentbay import AsyncAgentBay
from agentbay import CreateSessionParams


async def main():
    """Demonstrate agent task execution."""
    print("=== Agent Task Execution Example ===\n")

    client = AsyncAgentBay()
    session = None

    try:
        # Create a session
        print("Creating session...")
        session_result = await client.create(
            CreateSessionParams(image_id="linux_latest")
        )
        session = session_result.session
        print(f"Session created: {session.session_id}")

        # Execute a simple task asynchronously
        print("\n1. Executing async task...")
        task_description = "Create a file named test.txt with content 'Hello from Agent'"
        
        # Note: This demonstrates the workflow
        # Actual implementation would use: session.agent.async_execute_task(task_description)
        print(f"Task: {task_description}")
        
        # Simulate task execution using command
        result = await session.command.execute_command("echo 'Hello from Agent' > /tmp/test.txt")
        print(f"Task executed: {result.success}")

        # Verify task result
        print("\n2. Verifying task result...")
        result = await session.command.execute_command("cat /tmp/test.txt")
        print(f"File content: {result.output}")

        # Execute another task
        print("\n3. Executing another task...")
        task_description = "List all files in /tmp directory"
        print(f"Task: {task_description}")
        
        result = await session.command.execute_command("ls -la /tmp | head -10")
        print(f"Task result:\n{result.output}")

        # Demonstrate task status checking (conceptual)
        print("\n4. Task status monitoring pattern...")
        print("In real implementation:")
        print("  - result = await session.agent.async_execute_task(task)")
        print("  - status = await session.agent.get_task_status(result.task_id)")
        print("  - Poll until status indicates completion")

        print("\n=== Example completed successfully ===")

    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        raise

    finally:
        if session:
            print("\nCleaning up session...")
            await client.delete(session)
            print("Session closed")


if __name__ == "__main__":
    asyncio.run(main())

