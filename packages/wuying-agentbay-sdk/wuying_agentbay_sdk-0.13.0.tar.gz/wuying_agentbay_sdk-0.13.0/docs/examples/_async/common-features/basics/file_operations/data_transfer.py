"""Data Transfer Example"""
import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from agentbay import AsyncAgentBay
from agentbay import CreateSessionParams


async def main():
    print("=== Data Transfer ===\n")
    client = AsyncAgentBay()
    session = None

    try:
        session_result = await client.create(CreateSessionParams(image_id="linux_latest"))
        session = session_result.session

        # Write data
        data = "Line 1\nLine 2\nLine 3\n" * 10
        await session.file_system.write_file("/tmp/data.txt", data)
        print("1. Data written")

        # Read data back
        result = await session.file_system.read_file("/tmp/data.txt")
        print(f"2. Data size: {len(result.content)} bytes")

        # Verify data
        lines = result.content.split('\n')
        print(f"3. Lines: {len(lines)}")

        print("\n=== Completed ===")

    finally:
        if session:
            await client.delete(session)


if __name__ == "__main__":
    asyncio.run(main())

