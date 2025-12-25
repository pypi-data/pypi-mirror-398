"""
Example demonstrating browser cookies management with AgentBay SDK.

This example shows how to:
- Get all cookies from a browser session
- Set custom cookies
- Delete specific cookies
- Clear all cookies
- Export and import cookies
- Handle cookie persistence
"""

import asyncio
import os
import json
from typing import List, Dict, Any

from agentbay import AsyncAgentBay
from agentbay import CreateSessionParams
from agentbay import BrowserOption

from playwright.async_api import async_playwright


async def get_all_cookies(context) -> List[Dict[str, Any]]:
    """Get all cookies from the browser context."""
    print("\n🍪 Getting all cookies...")
    
    cookies = await context.cookies()
    print(f"✅ Found {len(cookies)} cookies")
    
    for cookie in cookies:
        print(f"   - {cookie['name']}: {cookie['value'][:20]}...")
    
    return cookies


async def set_custom_cookies(context, cookies: List[Dict[str, Any]]):
    """Set custom cookies in the browser context."""
    print(f"\n🍪 Setting {len(cookies)} custom cookies...")
    
    try:
        await context.add_cookies(cookies)
        print("✅ Cookies set successfully")
    except Exception as e:
        print(f"❌ Failed to set cookies: {e}")


async def delete_specific_cookie(context, cookie_name: str):
    """Delete a specific cookie by name."""
    print(f"\n🗑️  Deleting cookie: {cookie_name}")
    
    try:
        # Get all cookies
        cookies = await context.cookies()
        
        # Filter out the cookie to delete
        remaining_cookies = [c for c in cookies if c['name'] != cookie_name]
        
        # Clear all cookies
        await context.clear_cookies()
        
        # Re-add remaining cookies
        if remaining_cookies:
            await context.add_cookies(remaining_cookies)
        
        print(f"✅ Cookie '{cookie_name}' deleted")
    except Exception as e:
        print(f"❌ Failed to delete cookie: {e}")


async def clear_all_cookies(context):
    """Clear all cookies from the browser context."""
    print("\n🗑️  Clearing all cookies...")
    
    try:
        await context.clear_cookies()
        print("✅ All cookies cleared")
    except Exception as e:
        print(f"❌ Failed to clear cookies: {e}")


async def export_cookies(context, filename: str):
    """Export cookies to a JSON file."""
    print(f"\n💾 Exporting cookies to {filename}...")
    
    try:
        cookies = await context.cookies()
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, indent=2)
        
        print(f"✅ Exported {len(cookies)} cookies")
    except Exception as e:
        print(f"❌ Failed to export cookies: {e}")


async def import_cookies(context, filename: str):
    """Import cookies from a JSON file."""
    print(f"\n📥 Importing cookies from {filename}...")
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        
        await context.add_cookies(cookies)
        print(f"✅ Imported {len(cookies)} cookies")
    except Exception as e:
        print(f"❌ Failed to import cookies: {e}")


async def demonstrate_cookie_persistence(page, context):
    """Demonstrate cookie persistence across page navigations."""
    print("\n🔄 Demonstrating cookie persistence...")
    
    # Navigate to a website
    await page.goto("https://example.com")
    
    # Set a custom cookie
    custom_cookie = {
        "name": "test_cookie",
        "value": "test_value_123",
        "domain": "example.com",
        "path": "/"
    }
    
    await context.add_cookies([custom_cookie])
    print("✅ Set custom cookie")
    
    # Reload page
    await page.reload()
    
    # Check if cookie persists
    cookies = await context.cookies()
    test_cookie = next((c for c in cookies if c['name'] == 'test_cookie'), None)
    
    if test_cookie:
        print(f"✅ Cookie persisted after reload: {test_cookie['value']}")
    else:
        print("❌ Cookie did not persist")


async def main():
    """Main function demonstrating cookies management."""
    api_key = os.getenv("AGENTBAY_API_KEY")
    if not api_key:
        print("❌ Error: AGENTBAY_API_KEY environment variable not set")
        return
    
    agent_bay = AsyncAgentBay(api_key=api_key)
    session = None
    
    try:
        print("=" * 60)
        print("Browser Cookies Management Example")
        print("=" * 60)
        
        # Create browser session
        print("\nCreating browser session...")
        params = CreateSessionParams(image_id="browser_latest")
        result = await agent_bay.create(params)
        
        if not result.success or not result.session:
            print(f"❌ Failed to create session: {result.error_message}")
            return
        
        session = result.session
        print(f"✅ Session created: {session.session_id}")
        
        # Initialize browser
        browser_option = BrowserOption()
        if not await session.browser.initialize(browser_option):
            print("❌ Failed to initialize browser")
            return
        
        print("✅ Browser initialized")
        
        # Get browser endpoint
        endpoint_url = await session.browser.get_endpoint_url()
        
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(endpoint_url)
            context = browser.contexts[0]
            page = await context.new_page()
            
            # Navigate to a website to get some cookies
            await page.goto("https://example.com")
            await page.wait_for_load_state("networkidle")
            
            # Example 1: Get all cookies
            print("\n" + "=" * 60)
            print("Example 1: Get All Cookies")
            print("=" * 60)
            cookies = await get_all_cookies(context)
            
            # Example 2: Set custom cookies
            print("\n" + "=" * 60)
            print("Example 2: Set Custom Cookies")
            print("=" * 60)
            custom_cookies = [
                {
                    "name": "user_preference",
                    "value": "dark_mode",
                    "domain": "example.com",
                    "path": "/"
                },
                {
                    "name": "session_id",
                    "value": "abc123xyz",
                    "domain": "example.com",
                    "path": "/"
                }
            ]
            await set_custom_cookies(context, custom_cookies)
            await get_all_cookies(context)
            
            # Example 3: Export cookies
            print("\n" + "=" * 60)
            print("Example 3: Export Cookies")
            print("=" * 60)
            await export_cookies(context, "/tmp/cookies_backup.json")
            
            # Example 4: Clear all cookies
            print("\n" + "=" * 60)
            print("Example 4: Clear All Cookies")
            print("=" * 60)
            await clear_all_cookies(context)
            await get_all_cookies(context)
            
            # Example 5: Import cookies
            print("\n" + "=" * 60)
            print("Example 5: Import Cookies")
            print("=" * 60)
            await import_cookies(context, "/tmp/cookies_backup.json")
            await get_all_cookies(context)
            
            # Example 6: Cookie persistence
            print("\n" + "=" * 60)
            print("Example 6: Cookie Persistence")
            print("=" * 60)
            await demonstrate_cookie_persistence(page, context)
            
            await browser.close()
        
        print("\n✅ Cookies management examples completed")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        
    finally:
        if session:
            print("\n🧹 Cleaning up session...")
            await agent_bay.delete(session)
            print("✅ Session deleted")


if __name__ == "__main__":
    asyncio.run(main())

