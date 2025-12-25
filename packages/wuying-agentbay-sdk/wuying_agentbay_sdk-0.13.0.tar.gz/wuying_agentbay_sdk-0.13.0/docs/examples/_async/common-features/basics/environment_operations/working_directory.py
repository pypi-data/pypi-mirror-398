"""Working Directory Example"""
import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from agentbay import AsyncAgentBay
from agentbay import CreateSessionParams


async def main():
    print("=== Working Directory ===\n")
    client = AsyncAgentBay()
    session = None

    try:
        session_result = await client.create(CreateSessionParams(image_id="linux_latest"))
        session = session_result.session

        # Check current directory
        result = await session.command.execute_command("pwd")
        print(f"1. Current dir: {result.output}")

        # Change directory
        result = await session.command.execute_command("cd /tmp && pwd")
        print(f"2. After cd: {result.output}")

        # Create and navigate
        result = await session.command.execute_command("mkdir -p /tmp/mydir && cd /tmp/mydir && pwd")
        print(f"3. New dir: {result.output}")

        print("\n=== Completed ===")

    finally:
        if session:
            await client.delete(session)


if __name__ == "__main__":
    asyncio.run(main())

