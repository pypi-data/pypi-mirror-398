"""
示例：GV 影院 Quick Buy + 选座
打开 gv.com.sg
通过 Quick Buy 选择影院/日期/场次，进入选座并选择单个座位
重点：复杂流程的自然语言分步动作；保持只选一个座位
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
        await agent.navigate("https://www.gv.com.sg/")

        await agent.act(ActOptions(action='点击 "Quick Buy" 按钮'))
        await agent.act(
            ActOptions(
                action="在 Quick-Buy 面板中选择任意影院、任意影片，日期选择 2025-08-12"
            )
        )
        await agent.act(ActOptions(action='点击 "Go" 进入选座页面'))
        await agent.act(ActOptions(action='点击 "12:55 PM" 的场次'))
        await agent.act(
            ActOptions(
                action="选择任意可用座位，确保只选择一个，如有两座被选中则取消多余的"
            )
        )
        await asyncio.sleep(3)
        await agent.close()
    finally:
        await agent_bay.delete(session)


if __name__ == "__main__":
    asyncio.run(main())
