"""
Example demonstrating Browser Fingerprint local sync feature with AgentBay SDK.

This example shows how to sync local browser fingerprint to remote browser fingerprint.
BrowserFingerprintGenerator has ability to dump local installed chrome browser fingerprint,
and then you can sync it to remote browser fingerprint by using BrowserOption.fingerprint_format.

This example will:
1. Generate local chrome browser fingerprint by BrowserFingerprintGenerator
2. Sync local browser fingerprint to remote browser fingerprint
3. Verify remote browser fingerprint
4. Clean up session
"""

import os
import asyncio

from agentbay import AsyncAgentBay
from agentbay import CreateSessionParams
from agentbay import BrowserOption
from agentbay import AsyncBrowserFingerprintGenerator

from playwright.async_api import async_playwright


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
    session_result = await agent_bay.create(params)

    if session_result.success:
        session = session_result.session
        print(f"Session created with ID: {session.session_id}")

        fingerprint_generator = AsyncBrowserFingerprintGenerator()
        fingerprint_format = await fingerprint_generator.generate_fingerprint()

        # Create browser option with fingerprint format.
        # Fingerprint format is dumped from local chrome browser by BrowserFingerprintGenerator
        # automatically, you can use it to sync to remote browser fingerprint.
        browser_option = BrowserOption(
            use_stealth=True,
            fingerprint_format=fingerprint_format
        )

        if await session.browser.initialize(browser_option):
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
                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON response: {e}")
                    print(f"Raw response content: {response_text}")
                    # Fallback: try to get user agent directly
                    user_agent = await page.evaluate("() => navigator.userAgent")
                    print(f"Fallback User Agent: {user_agent}")
                except Exception as e:
                    print(f"Error getting user agent: {e}")
                    user_agent = await page.evaluate("() => navigator.userAgent")
                    print(f"Fallback User Agent: {user_agent}")

                print("Please check if User Agent is synced correctly by visiting https://httpbin.org/user-agent in local chrome browser.")

                await page.wait_for_timeout(3000)
                await browser.close()

        # Clean up session
        await agent_bay.delete(session)
    

if __name__ == "__main__":
    asyncio.run(main())