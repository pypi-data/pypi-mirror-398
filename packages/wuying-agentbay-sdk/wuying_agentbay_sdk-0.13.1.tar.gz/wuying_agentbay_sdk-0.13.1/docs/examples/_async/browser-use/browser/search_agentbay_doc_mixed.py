"""
示例：在同一浏览器会话中混用 Playwright(连接与新页面监听)与 PageUse Agent(动作执行与页面内容提取)
用 Playwright 导航与监听新页面
用 PageUse Agent 执行动作（搜索、点击、滚动）
重点：演示 PageUse Agent 与 Playwright 混排；焦点/页面以传入的 page 为准
注意：新页面打开后，将 Playwright 的 new_page 传入 Agent(page=new_page), 确保两者指向同一页面
"""

import asyncio
import os

from agentbay import AsyncAgentBay as AgentBay
from agentbay import CreateSessionParams
from agentbay import BrowserOption
from agentbay import ActOptions
from playwright.async_api import async_playwright


async def main():
    api_key = os.getenv("AGENTBAY_API_KEY")
    agent_bay = AgentBay(api_key=api_key)
    params = CreateSessionParams(image_id="browser_latest")
    session_result = await agent_bay.create(params)
    assert session_result.success and session_result.session is not None
    session = session_result.session
    try:
        assert await session.browser.initialize(BrowserOption())
        agent = session.browser.agent

        endpoint_url = await session.browser.get_endpoint_url()
        async with async_playwright() as p:
            playwright_browser = await p.chromium.connect_over_cdp(endpoint_url)
            context = (
                playwright_browser.contexts[0]
                if playwright_browser.contexts
                else await playwright_browser.new_context()
            )
            page = await context.new_page()

            # 先用 Playwright 导航
            await page.goto(
                "https://www.aliyun.com", wait_until="domcontentloaded", timeout=60000
            )

            # 让 Agent 跟上当前 Playwright 页面（显式传 page）
            await agent.act(
                ActOptions(action="搜索框输入'AgentBay帮助文档'并回车"), page=page
            )

            # Playwright 等待新页面打开
            async with page.context.expect_page() as new_page_info:
                # 在之前的页面上使用Agent
                await agent.act(
                    ActOptions(action="点击搜索结果中的第一项"),
                    page=page,
                )
                new_page = await new_page_info.value
                await new_page.wait_for_load_state("domcontentloaded")

            # 方式一： 在新页面上继续用 Agent（传 page=new_page，确保焦点一致）
            await agent.act(ActOptions(action="点击'帮助文档'"), page=new_page)
            await agent.act(ActOptions(action="滚动页面到底部"), page=new_page)

            # 方式二： 也可不传page参数， 因上一步动作由Agent发起，Agent默认将焦点切到新打开的页面
            # await agent.act(ActOptions(action="点击'帮助文档'"))
            # await agent.act(ActOptions(action="滚动页面到底部"))

            await playwright_browser.close()
    finally:
        await agent_bay.delete(session)


if __name__ == "__main__":
    asyncio.run(main())
