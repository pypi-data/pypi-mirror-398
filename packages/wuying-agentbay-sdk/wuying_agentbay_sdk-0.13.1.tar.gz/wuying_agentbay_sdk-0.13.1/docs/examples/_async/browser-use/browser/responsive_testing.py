"""
Browser Responsive Testing Example

This example demonstrates:
1. Testing different viewport sizes
2. Mobile vs desktop rendering
3. Responsive design verification
4. Screenshot comparison across sizes
"""

import asyncio
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from agentbay import AsyncAgentBay, CreateSessionParams
from agentbay import BrowserOption, ExtractOptions
from agentbay import ActOptions
from pydantic import BaseModel, Field


class TextContent(BaseModel):
    """Simple model to extract text content."""
    content: str = Field(description="The extracted text content")


async def main():
    """Demonstrate browser responsive testing."""
    print("=== Browser Responsive Testing Example ===\n")

    # Initialize AgentBay client
    client = AsyncAgentBay()
    session = None

    try:
        # Create a session with browser enabled
        print("Creating session with browser...")
        session_result = await client.create(
            CreateSessionParams(image_id="browser_latest")
        )
        session = session_result.session
        print(f"Session created: {session.session_id}")

        # Initialize browser
        print("Initializing browser...")
        if not await session.browser.initialize(BrowserOption()):
            raise Exception("Failed to initialize browser")
        print("Browser initialized")

        # Navigate to a responsive website
        print("\n1. Navigating to test website...")
        await session.browser.agent.navigate("https://example.com")

        # Test desktop viewport
        print("\n2. Testing desktop viewport (1920x1080)...")
        await session.browser.agent.act(
            ActOptions(action="Set the browser viewport size to 1920x1080 pixels")
        )
        desktop_screenshot = await session.browser.agent.screenshot()
        print(f"Desktop screenshot saved: {desktop_screenshot}")

        # Extract desktop layout info
        success, desktop_result = await session.browser.agent.extract(
            ExtractOptions(instruction="Describe the layout and visible elements on this page", schema=TextContent)
        )
        if success:
            print(f"Desktop layout:\n{desktop_result.content}")
        else:
            print("Failed to extract desktop layout")

        # Test tablet viewport
        print("\n3. Testing tablet viewport (768x1024)...")
        await session.browser.agent.act(
            ActOptions(action="Set the browser viewport size to 768x1024 pixels")
        )
        tablet_screenshot = await session.browser.agent.screenshot()
        print(f"Tablet screenshot saved: {tablet_screenshot}")

        # Extract tablet layout info
        success, tablet_result = await session.browser.agent.extract(
            ExtractOptions(instruction="Describe the layout and visible elements on this page", schema=TextContent)
        )
        if success:
            print(f"Tablet layout:\n{tablet_result.content}")
        else:
            print("Failed to extract tablet layout")

        # Test mobile viewport
        print("\n4. Testing mobile viewport (375x667)...")
        await session.browser.agent.act(
            ActOptions(action="Set the browser viewport size to 375x667 pixels")
        )
        mobile_screenshot = await session.browser.agent.screenshot()
        print(f"Mobile screenshot saved: {mobile_screenshot}")

        # Extract mobile layout info
        success, mobile_result = await session.browser.agent.extract(
            ExtractOptions(instruction="Describe the layout and visible elements on this page", schema=TextContent)
        )
        if success:
            print(f"Mobile layout:\n{mobile_result.content}")
        else:
            print("Failed to extract mobile layout")

        # Test a more complex responsive site
        print("\n5. Testing responsive design on news site...")
        await session.browser.agent.navigate("https://news.ycombinator.com")

        # Mobile view
        print("\n6. Checking mobile view...")
        await session.browser.agent.act(
            ActOptions(action="Set the browser viewport size to 375x667 pixels")
        )
        mobile_news_screenshot = await session.browser.agent.screenshot()
        print(f"Mobile news screenshot saved: {mobile_news_screenshot}")

        success, mobile_news_result = await session.browser.agent.extract(
            ExtractOptions(instruction="How many story items are visible on the mobile view?", schema=TextContent)
        )
        if success:
            print(f"Mobile view stories: {mobile_news_result.content}")
        else:
            print("Failed to extract mobile view stories")

        # Desktop view
        print("\n7. Checking desktop view...")
        await session.browser.agent.act(
            ActOptions(action="Set the browser viewport size to 1920x1080 pixels")
        )
        desktop_news_screenshot = await session.browser.agent.screenshot()
        print(f"Desktop news screenshot saved: {desktop_news_screenshot}")

        success, desktop_news_result = await session.browser.agent.extract(
            ExtractOptions(instruction="How many story items are visible on the desktop view?", schema=TextContent)
        )
        if success:
            print(f"Desktop view stories: {desktop_news_result.content}")
        else:
            print("Failed to extract desktop view stories")

        # Test orientation change
        print("\n8. Testing landscape orientation...")
        await session.browser.agent.act(
            ActOptions(action="Set the browser viewport size to 667x375 pixels (landscape)")
        )
        landscape_screenshot = await session.browser.agent.screenshot()
        print(f"Landscape screenshot saved: {landscape_screenshot}")

        print("\n=== Example completed successfully ===")

    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        raise

    finally:
        # Clean up
        if session:
            print("\nCleaning up session...")
            await client.delete(session)
            print("Session closed")


if __name__ == "__main__":
    asyncio.run(main())

