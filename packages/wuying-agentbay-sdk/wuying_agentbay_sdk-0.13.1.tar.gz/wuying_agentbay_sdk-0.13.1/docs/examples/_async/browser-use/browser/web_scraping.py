"""
Example demonstrating web scraping with AgentBay SDK.

This example shows how to:
- Extract data from web pages
- Handle pagination
- Parse structured data
- Save scraped data
- Handle dynamic content
"""

import asyncio
import os
import json
from typing import List, Dict, Any

from agentbay import AsyncAgentBay
from agentbay import CreateSessionParams
from agentbay import BrowserOption

from playwright.async_api import async_playwright


async def scrape_basic_data(page) -> Dict[str, Any]:
    """Scrape basic data from a web page."""
    print("\n🔍 Scraping basic page data...")
    
    # Get page title
    title = await page.title()
    
    # Get all headings
    headings = await page.eval_on_selector_all(
        "h1, h2, h3",
        "elements => elements.map(e => ({ tag: e.tagName, text: e.textContent.trim() }))"
    )
    
    # Get all links
    links = await page.eval_on_selector_all(
        "a[href]",
        "elements => elements.map(e => ({ text: e.textContent.trim(), href: e.href }))"
    )
    
    # Get all images
    images = await page.eval_on_selector_all(
        "img[src]",
        "elements => elements.map(e => ({ alt: e.alt, src: e.src }))"
    )
    
    data = {
        "title": title,
        "url": page.url,
        "headings": headings[:10],  # First 10 headings
        "links": links[:20],  # First 20 links
        "images": images[:10]  # First 10 images
    }
    
    print(f"✅ Scraped data from: {title}")
    print(f"   - Headings: {len(headings)}")
    print(f"   - Links: {len(links)}")
    print(f"   - Images: {len(images)}")
    
    return data


async def scrape_table_data(page, selector: str) -> List[Dict[str, str]]:
    """Scrape data from an HTML table."""
    print(f"\n📊 Scraping table data from selector: {selector}")
    
    try:
        # Wait for table to load
        await page.wait_for_selector(selector, timeout=5000)
        
        # Extract table data
        table_data = await page.evaluate(f"""
            () => {{
                const table = document.querySelector('{selector}');
                if (!table) return [];
                
                const headers = Array.from(table.querySelectorAll('th')).map(th => th.textContent.trim());
                const rows = Array.from(table.querySelectorAll('tbody tr'));
                
                return rows.map(row => {{
                    const cells = Array.from(row.querySelectorAll('td'));
                    const rowData = {{}};
                    cells.forEach((cell, index) => {{
                        rowData[headers[index] || `column_${{index}}`] = cell.textContent.trim();
                    }});
                    return rowData;
                }});
            }}
        """)
        
        print(f"✅ Scraped {len(table_data)} rows from table")
        return table_data
        
    except Exception as e:
        print(f"❌ Failed to scrape table: {e}")
        return []


async def scrape_with_pagination(page, max_pages: int = 3) -> List[Dict[str, Any]]:
    """Scrape data across multiple pages."""
    print(f"\n📄 Scraping data with pagination (max {max_pages} pages)...")
    
    all_data = []
    current_page = 1
    
    while current_page <= max_pages:
        print(f"\n  Scraping page {current_page}...")
        
        # Scrape current page
        page_data = await scrape_basic_data(page)
        page_data["page_number"] = current_page
        all_data.append(page_data)
        
        # Look for next page button
        next_button = await page.query_selector('a.next, button.next, a[rel="next"]')
        
        if not next_button or current_page >= max_pages:
            print(f"✅ Reached end of pagination at page {current_page}")
            break
        
        # Click next page
        await next_button.click()
        await page.wait_for_load_state("networkidle")
        
        current_page += 1
        await asyncio.sleep(1)  # Be polite to the server
    
    print(f"\n✅ Total pages scraped: {len(all_data)}")
    return all_data


async def scrape_dynamic_content(page):
    """Scrape content that loads dynamically."""
    print("\n⚡ Scraping dynamic content...")
    
    # Scroll to load more content
    print("  Scrolling to load dynamic content...")
    for _ in range(3):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(1)
    
    # Wait for dynamic content to load
    try:
        await page.wait_for_selector('.dynamic-content', timeout=5000)
        print("✅ Dynamic content loaded")
    except:
        print("⚠️  No dynamic content selector found")


async def save_scraped_data(data: Any, filename: str):
    """Save scraped data to a JSON file."""
    print(f"\n💾 Saving scraped data to {filename}...")
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ Data saved successfully")
    except Exception as e:
        print(f"❌ Failed to save data: {e}")


async def main():
    """Main function demonstrating web scraping."""
    api_key = os.getenv("AGENTBAY_API_KEY")
    if not api_key:
        print("❌ Error: AGENTBAY_API_KEY environment variable not set")
        return
    
    agent_bay = AsyncAgentBay(api_key=api_key)
    session = None
    
    try:
        print("=" * 60)
        print("Web Scraping Example")
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
            
            # Example: Scrape a public website
            print("\n" + "=" * 60)
            print("Scraping Example Website")
            print("=" * 60)
            
            await page.goto("https://example.com")
            
            # Scrape basic data
            basic_data = await scrape_basic_data(page)
            
            # Save scraped data
            await save_scraped_data(basic_data, "/tmp/scraped_data.json")
            
            await browser.close()
        
        print("\n✅ Web scraping examples completed")
        print("\n💡 Tips:")
        print("   - Always respect robots.txt")
        print("   - Add delays between requests")
        print("   - Handle rate limiting gracefully")
        print("   - Check website's terms of service")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        
    finally:
        if session:
            print("\n🧹 Cleaning up session...")
            await agent_bay.delete(session)
            print("✅ Session deleted")


if __name__ == "__main__":
    asyncio.run(main())

