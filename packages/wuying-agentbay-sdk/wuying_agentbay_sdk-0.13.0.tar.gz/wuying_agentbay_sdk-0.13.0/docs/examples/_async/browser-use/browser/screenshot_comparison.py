"""
Example demonstrating screenshot comparison with AgentBay SDK.

This example shows how to:
- Take multiple screenshots
- Compare screenshots for visual differences
- Detect layout changes
- Monitor visual regression
- Save comparison results
"""

import asyncio
import os
import base64
import hashlib
from typing import Tuple

from agentbay import AsyncAgentBay
from agentbay import CreateSessionParams
from agentbay import BrowserOption

from playwright.async_api import async_playwright


async def take_screenshot_base64(page) -> str:
    """Take a screenshot and return as base64."""
    screenshot_bytes = await page.screenshot()
    return base64.b64encode(screenshot_bytes).decode('utf-8')


async def save_screenshot(page, filename: str):
    """Save screenshot to file."""
    await page.screenshot(path=filename)
    print(f"  💾 Screenshot saved: {filename}")


async def calculate_screenshot_hash(screenshot_b64: str) -> str:
    """Calculate hash of screenshot for quick comparison."""
    return hashlib.sha256(screenshot_b64.encode()).hexdigest()


async def compare_screenshots_simple(screenshot1_b64: str, screenshot2_b64: str) -> Tuple[bool, str]:
    """Simple screenshot comparison using hash."""
    hash1 = await calculate_screenshot_hash(screenshot1_b64)
    hash2 = await calculate_screenshot_hash(screenshot2_b64)
    
    if hash1 == hash2:
        return True, "Screenshots are identical"
    else:
        return False, "Screenshots are different"


async def take_and_compare_screenshots(page, url: str, wait_time: int = 2):
    """Take screenshots at different times and compare."""
    print(f"\n📸 Taking screenshots of {url}...")
    
    # Navigate to page
    await page.goto(url)
    await page.wait_for_load_state("networkidle")
    
    # Take first screenshot
    print("  Taking first screenshot...")
    screenshot1 = await take_screenshot_base64(page)
    await save_screenshot(page, "/tmp/screenshot_1.png")
    
    # Wait a bit
    await asyncio.sleep(wait_time)
    
    # Take second screenshot
    print("  Taking second screenshot...")
    screenshot2 = await take_screenshot_base64(page)
    await save_screenshot(page, "/tmp/screenshot_2.png")
    
    # Compare
    is_same, message = await compare_screenshots_simple(screenshot1, screenshot2)
    
    if is_same:
        print(f"  ✅ {message}")
    else:
        print(f"  ⚠️  {message}")
    
    return is_same


async def monitor_page_changes(page, url: str, check_interval: int = 5, num_checks: int = 3):
    """Monitor page for visual changes over time."""
    print(f"\n👀 Monitoring {url} for changes...")
    
    await page.goto(url)
    await page.wait_for_load_state("networkidle")
    
    # Take baseline screenshot
    print("  Taking baseline screenshot...")
    baseline = await take_screenshot_base64(page)
    baseline_hash = await calculate_screenshot_hash(baseline)
    
    # Monitor for changes
    changes_detected = []
    
    for i in range(num_checks):
        print(f"\n  Check {i+1}/{num_checks}...")
        await asyncio.sleep(check_interval)
        
        # Reload page
        await page.reload()
        await page.wait_for_load_state("networkidle")
        
        # Take new screenshot
        current = await take_screenshot_base64(page)
        current_hash = await calculate_screenshot_hash(current)
        
        # Compare with baseline
        if current_hash != baseline_hash:
            print(f"    ⚠️  Change detected!")
            changes_detected.append(i+1)
        else:
            print(f"    ✅ No changes")
    
    if changes_detected:
        print(f"\n  ⚠️  Changes detected in checks: {changes_detected}")
    else:
        print(f"\n  ✅ No changes detected across all checks")
    
    return len(changes_detected) == 0


async def compare_different_viewports(page, url: str):
    """Compare screenshots at different viewport sizes."""
    print(f"\n📱 Comparing different viewport sizes for {url}...")
    
    viewports = [
        {"name": "Mobile", "width": 375, "height": 667},
        {"name": "Tablet", "width": 768, "height": 1024},
        {"name": "Desktop", "width": 1920, "height": 1080}
    ]
    
    screenshots = {}
    
    for viewport in viewports:
        print(f"\n  Taking screenshot at {viewport['name']} ({viewport['width']}x{viewport['height']})...")
        
        # Set viewport
        await page.set_viewport_size({
            "width": viewport["width"],
            "height": viewport["height"]
        })
        
        # Navigate and take screenshot
        await page.goto(url)
        await page.wait_for_load_state("networkidle")
        
        screenshot = await take_screenshot_base64(page)
        screenshots[viewport["name"]] = screenshot
        
        # Save to file
        filename = f"/tmp/screenshot_{viewport['name'].lower()}.png"
        await save_screenshot(page, filename)
    
    # Compare hashes
    hashes = {name: await calculate_screenshot_hash(ss) for name, ss in screenshots.items()}
    
    print(f"\n  📊 Comparison Results:")
    for name, hash_val in hashes.items():
        print(f"    {name}: {hash_val[:16]}...")
    
    # Check if all are different (expected for responsive design)
    unique_hashes = len(set(hashes.values()))
    if unique_hashes == len(viewports):
        print(f"  ✅ All viewports render differently (responsive design detected)")
    else:
        print(f"  ⚠️  Some viewports render identically")


async def main():
    """Main function demonstrating screenshot comparison."""
    api_key = os.getenv("AGENTBAY_API_KEY")
    if not api_key:
        print("❌ Error: AGENTBAY_API_KEY environment variable not set")
        return
    
    agent_bay = AsyncAgentBay(api_key=api_key)
    session = None
    
    try:
        print("=" * 60)
        print("Screenshot Comparison Example")
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
            
            # Example 1: Basic screenshot comparison
            print("\n" + "=" * 60)
            print("Example 1: Basic Screenshot Comparison")
            print("=" * 60)
            
            await take_and_compare_screenshots(page, "https://example.com", wait_time=2)
            
            # Example 2: Different viewport comparison
            print("\n" + "=" * 60)
            print("Example 2: Viewport Comparison")
            print("=" * 60)
            
            await compare_different_viewports(page, "https://example.com")
            
            await browser.close()
        
        print("\n✅ Screenshot comparison examples completed")
        print("\n💡 Tips:")
        print("   - Use visual regression testing tools for production")
        print("   - Consider pixel-by-pixel comparison for precise results")
        print("   - Account for dynamic content (ads, timestamps)")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        
    finally:
        if session:
            print("\n🧹 Cleaning up session...")
            await agent_bay.delete(session)
            print("✅ Session deleted")


if __name__ == "__main__":
    asyncio.run(main())

