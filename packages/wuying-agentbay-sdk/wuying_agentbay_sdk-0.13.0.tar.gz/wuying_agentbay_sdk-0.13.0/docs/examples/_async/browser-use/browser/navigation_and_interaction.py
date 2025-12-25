"""
Browser Navigation and Interaction Example

This example demonstrates:
1. Basic browser navigation
2. Element interaction (click, type, select)
3. Page state verification
4. Navigation history management
"""

import asyncio
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from agentbay import AsyncAgentBay, CreateSessionParams
from agentbay import BrowserOption
from agentbay import ActOptions, ExtractOptions
from pydantic import BaseModel, Field


class TextContent(BaseModel):
    """Simple model to extract text content."""
    content: str = Field(description="The extracted text content")


async def main():
    """Demonstrate browser navigation and interaction."""
    print("=== Browser Navigation and Interaction Example ===\n")

    # Initialize AgentBay client
    client = AsyncAgentBay()
    session = None

    try:
        # Create a session with browser enabled
        print("Creating session with browser...")
        session_result = await client.create(
            CreateSessionParams(image_id="browser_latest")
        )
        if not session_result.success or not session_result.session:
            raise Exception(f"Failed to create session: {session_result.error_message}")
        session = session_result.session
        print(f"Session created: {session.session_id}")

        # Initialize browser
        print("Initializing browser...")
        if not await session.browser.initialize(BrowserOption()):
            raise Exception("Failed to initialize browser")
        print("Browser initialized")

        # Navigate to a test page
        print("\n1. Navigating to example.com...")
        await session.browser.agent.navigate("https://example.com")
        print("Navigation successful")

        # Take a screenshot
        print("\n2. Taking screenshot...")
        screenshot_path = await session.browser.agent.screenshot()
        print(f"Screenshot saved to: {screenshot_path}")

        # Navigate to another page
        print("\n3. Navigating to httpbin.org/forms/post...")
        await session.browser.agent.navigate("https://httpbin.org/forms/post")

        # Interact with form elements
        print("\n4. Filling form...")
        await session.browser.agent.act(ActOptions(action="Fill in the customer name field with 'John Doe'"))
        await session.browser.agent.act(ActOptions(action="Fill in the telephone field with '1234567890'"))
        await session.browser.agent.act(ActOptions(action="Fill in the email field with 'john@example.com'"))
        print("Form filled successfully")

        # Navigate back
        print("\n5. Navigating back...")
        await session.browser.agent.navigate("back")
        print("Navigated back to previous page")

        # Navigate forward
        print("\n6. Navigating forward...")
        await session.browser.agent.navigate("forward")
        print("Navigated forward")

        # Get current URL
        print("\n7. Extracting current URL...")
        success, url_result = await session.browser.agent.extract(ExtractOptions(
            instruction="What is the current page URL?",
            schema=TextContent
        ))
        if success:
            print(f"Current URL: {url_result.content}")
        else:
            print("Failed to extract current URL")

        # Verify page state
        print("\n8. Verifying page state...")
        success2, state_result = await session.browser.agent.extract(ExtractOptions(
            instruction="Is there a form on this page?",
            schema=TextContent
        ))
        if success2:
            print(f"Page state: {state_result.content}")
        else:
            print("Failed to extract page state")

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

