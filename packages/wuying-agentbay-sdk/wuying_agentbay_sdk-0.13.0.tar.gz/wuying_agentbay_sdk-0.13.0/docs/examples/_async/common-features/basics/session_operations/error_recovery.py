"""Error Recovery Example"""
import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from agentbay import AsyncAgentBay
from agentbay import CreateSessionParams


async def main():
    print("=== Error Recovery ===\n")
    client = AsyncAgentBay()
    session = None

    try:
        session_result = await client.create(CreateSessionParams(image_id="linux_latest"))
        session = session_result.session

        # Try command that might fail
        result = await session.command.execute_command("ls /nonexistent 2>&1 || echo 'Recovered'")
        print(f"1. Recovery: {result.output}")

        # Continue with valid operations
        result = await session.command.execute_command("echo 'Continuing...'")
        print(f"2. Continue: {result.output}")

        print("\n=== Completed ===")

    finally:
        if session:
            await client.delete(session)


if __name__ == "__main__":
    asyncio.run(main())

