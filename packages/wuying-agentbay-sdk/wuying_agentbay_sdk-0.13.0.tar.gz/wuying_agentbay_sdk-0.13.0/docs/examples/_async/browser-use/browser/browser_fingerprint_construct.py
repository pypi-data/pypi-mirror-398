"""
Example demonstrating Browser Fingerprint construction with AgentBay SDK.

This example shows how to construct browser fingerprint by yourself.

This example will:
1. Construct browser fingerprint by yourself
2. Create AIBrowser session with constructed browser fingerprint
3. Use playwright to connect to AIBrowser instance through CDP protocol
4. Verify browser fingerprint
"""

import os
import asyncio

from agentbay import AsyncAgentBay
from agentbay import CreateSessionParams
from agentbay import BrowserOption
from agentbay import FingerprintFormat

from playwright.async_api import async_playwright

async def generate_fingerprint_by_file() -> FingerprintFormat:
    """Generate fingerprint by file."""
    with open(os.path.join(os.path.dirname(__file__), "../../../../../../resource/fingerprint.example.json"), "r") as f:
        fingerprint_format = FingerprintFormat.load(f.read())
    return fingerprint_format

async def main():
    """Main function demonstrating browser fingerprint basic usage."""
    # Get API key from environment variable
    api_key = os.getenv("AGENTBAY_API_KEY")
    if not api_key:
        print("Error: AGENTBAY_API_KEY environment variable not set")
        return

    # Initialize AgentBay client
    print("Initializing AgentBay client...")
    agent_bay = AsyncAgentBay(api_key=api_key)

    # Create a session
    print("Creating a new session...")
    params = CreateSessionParams(
        image_id="browser_latest",
    )
    try:
        session_result = await agent_bay.create(params)
    except Exception as e:
        print(f"Failed to create session: {e}")
        return

    if session_result.success:
        session = session_result.session
        print(f"Session created with ID: {session.session_id}")

        # You can generate fingerprint by file or construct FingerprintFormat by yourself totally.
        fingerprint_format = await generate_fingerprint_by_file()

        # Create browser option with fingerprint format.
        # Fingerprint format is dumped from file by generate_fingerprint_by_file()
        # automatically, you can use it to sync to remote browser fingerprint.
        browser_option = BrowserOption(
            use_stealth=True,
            fingerprint_format=fingerprint_format
        )

        try:
            browser_init_result = await session.browser.initialize(browser_option)
            if not browser_init_result:
                print("Failed to initialize browser")
                await agent_bay.delete(session)
                return
        except Exception as e:
            print(f"Failed to initialize browser: {e}")
            await agent_bay.delete(session)
            return

        endpoint_url = await session.browser.get_endpoint_url()
        print("endpoint_url =", endpoint_url)

        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(endpoint_url)
            context = browser.contexts[0]
            page = await context.new_page()
            
            # Check user agent.
            print("\n--- Check User Agent ---")
            await page.goto("https://httpbin.org/user-agent")
            
            # Wait for page to load completely
            await page.wait_for_load_state("networkidle")

            # Get the response text more safely
            try:
                response_text = await page.evaluate("() => document.body.innerText.trim()")
                print(f"Raw response: {response_text}")
                
                import json
                response = json.loads(response_text)
                user_agent = response.get("user-agent", "")
                print(f"User Agent: {user_agent}")
                assert user_agent == fingerprint_format.fingerprint.navigator.userAgent
                print("User Agent constructed correctly")
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON response: {e}")
                print(f"Raw response content: {response_text}")
                # Fallback: try to get user agent directly
                user_agent = await page.evaluate("() => navigator.userAgent")
                print(f"Fallback User Agent: {user_agent}")
                assert user_agent == fingerprint_format.fingerprint.navigator.userAgent
                print("User Agent constructed correctly (fallback)")
            except Exception as e:
                print(f"Error getting user agent: {e}")
                user_agent = await page.evaluate("() => navigator.userAgent")
                print(f"Fallback User Agent: {user_agent}")
                assert user_agent == fingerprint_format.fingerprint.navigator.userAgent
                print("User Agent constructed correctly (fallback)")

            await page.wait_for_timeout(3000)
            await browser.close()

        # Clean up session
        await agent_bay.delete(session)
    else:
        print(f"Failed to create session: {session_result}")
        if hasattr(session_result, 'error_message'):
            print(f"Error message: {session_result.error_message}")
    

if __name__ == "__main__":
    asyncio.run(main())