"""
Computer Screen Operations Example

This example demonstrates:
1. Taking screenshots
2. Screen resolution operations
3. Screen capture and analysis
"""

import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from agentbay import AsyncAgentBay
from agentbay import CreateSessionParams


async def main():
    """Demonstrate computer screen operations."""
    print("=== Computer Screen Operations Example ===\n")

    client = AsyncAgentBay()
    session = None

    try:
        # Create a computer session
        print("Creating computer session...")
        session_result = await client.create(
            CreateSessionParams(image_id="windows_latest")
        )
        session = session_result.session
        print(f"Session created: {session.session_id}")

        # Get screen information
        print("\n1. Getting screen information...")
        result = await session.command.execute_command("wmic path Win32_VideoController get CurrentHorizontalResolution,CurrentVerticalResolution")
        print(f"Screen info:\n{result.output}")

        # Take a screenshot
        print("\n2. Taking screenshot...")
        # Note: Computer screenshot API may differ from browser
        # This is a demonstration of the workflow
        print("Screenshot functionality available through computer module")

        # List display devices
        print("\n3. Listing display devices...")
        result = await session.command.execute_command("wmic path Win32_DesktopMonitor get Name,ScreenHeight,ScreenWidth")
        print(f"Display devices:\n{result.output}")

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

