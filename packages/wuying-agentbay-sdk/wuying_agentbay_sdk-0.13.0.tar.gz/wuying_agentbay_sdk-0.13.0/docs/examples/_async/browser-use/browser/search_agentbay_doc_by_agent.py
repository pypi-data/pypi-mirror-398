"""
示例：使用PageUse Agent的AgentBay接口访问阿里云并搜索“AgentBay帮助文档”
打开 https://www.aliyun.com
搜索“AgentBay帮助文档”，点击第一条搜索结果并进入“帮助文档”，滚动到页面底部
重点：全程使用 BrowserAgent API
"""

import asyncio
import os

from agentbay import AsyncAgentBay as AgentBay
from agentbay import CreateSessionParams
from agentbay import BrowserOption
from agentbay import ActOptions


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

        await agent.navigate("https://www.aliyun.com")
        await agent.act(ActOptions(action="搜索框输入'AgentBay帮助文档'并回车"))
        await agent.act(ActOptions(action="点击搜索结果中的第一项"))
        await agent.act(ActOptions(action="点击'帮助文档'"))
        await agent.act(ActOptions(action="滚动页面到底部"))

        await asyncio.sleep(5)
    finally:
        await agent_bay.delete(session)


if __name__ == "__main__":
    asyncio.run(main())
