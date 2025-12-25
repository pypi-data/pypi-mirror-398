"""
示例：内网报销自动化（上传发票）
登录工作台，进入报销单
依次上传多张 PDF 电子发票，并保存与提交
重点：变量注入（用户名/密码）、文件上传、多步流程
"""

import asyncio
import os, asyncio
from agentbay import AsyncAgentBay
from agentbay import CreateSessionParams
from agentbay import BrowserOption
from agentbay import ActOptions


async def main():
    api_key = os.getenv("AGENTBAY_API_KEY")
    if not api_key:
        print("Error: AGENTBAY_API_KEY not set")
        return

    agent_bay = AsyncAgentBay(api_key=api_key)
    session_result = await agent_bay.create(CreateSessionParams(image_id="browser_latest"))
    
    if not session_result.success or session_result.session is None:
        print(f"Failed to create session: {session_result.error_message}")
        return
    
    session = session_result.session

    try:
        ok = await session.browser.initialize(BrowserOption())
        if not ok:
            print("Browser init failed")
            return

        agent = session.browser.agent

        await agent.navigate("https://work.aliyun-inc.com/")
        await agent.act(
            ActOptions(
                action="帮我登陆",
                variables={"用户名": "xxx", "密码": "123456"},
            )
        )
        await agent.act(ActOptions(action="点击报销链接或按钮"))
        await agent.act(ActOptions(action="在报销单列表中点击第一个项目"))

        invoices = [
            "/Users/user/Desktop/20250711114033.pdf",
            "/Users/user/Desktop/20250711114034.pdf",
            "/Users/user/Desktop/20250711114035.pdf",
        ]
        for path in invoices:
            await agent.act(
                ActOptions(action="在快速新增费用列表中选择'差旅-餐费'")
            )
            await agent.act(ActOptions(action="点击'上传电子发票'按钮"))
            await agent.act(ActOptions(action=f"上传位于 '{path}' 的文件"))
            await agent.act(ActOptions(action="点击'保存'按钮"))

        await agent.act(ActOptions(action="点击提交报销单"))
        await asyncio.sleep(3)
    finally:
        if session is not None:
            try:
                await session.browser.agent.close()
            except Exception:
                pass
            await agent_bay.delete(session)


if __name__ == "__main__":
    asyncio.run(main())
