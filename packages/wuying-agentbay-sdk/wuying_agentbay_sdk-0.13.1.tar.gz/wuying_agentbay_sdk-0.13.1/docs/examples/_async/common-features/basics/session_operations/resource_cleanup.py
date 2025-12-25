"""
Resource Cleanup Example

This example demonstrates:
1. Proper resource cleanup
2. Using context managers
3. Handling cleanup on errors
4. Best practices for resource management
"""

import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from agentbay import AsyncAgentBay
from agentbay import CreateSessionParams


async def main():
    """Demonstrate resource cleanup."""
    print("=== Resource Cleanup Example ===\n")

    client = AsyncAgentBay()
    session = None

    try:
        print("1. Creating session...")
        session_result = await client.create(CreateSessionParams(image_id="linux_latest"))
        session = session_result.session
        print(f"Session created: {session.session_id}")

        print("\n2. Performing operations...")
        await session.command.execute_command("echo 'Operation 1'")
        await session.command.execute_command("echo 'Operation 2'")
        print("Operations completed")

        print("\n3. Cleaning up resources...")

    except Exception as e:
        print(f"\nError occurred: {str(e)}")

    finally:
        if session:
            print("Deleting session...")
            await client.delete(session)
            print("Session deleted successfully")

        print("\n=== Example completed ===")


if __name__ == "__main__":
    asyncio.run(main())

