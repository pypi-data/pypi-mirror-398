import logging
from typing import Any, Dict

from ..page_agent import PageAgent


async def run(
    agent: PageAgent, _logger: logging.Logger, config: Dict[str, Any]
) -> dict:
    await agent.goto("https://www.homedepot.com/")

    try:
        result = await agent.act("what is the capital of the moon?")

        if not result.success:
            _logger.info(
                "✅ Test Passed: Agent correctly reported failure for a nonsense action."
            )
            return {"_success": True}
        else:
            error_msg = (
                "Validation failed: Agent unexpectedly succeeded on a nonsense action."
            )
            _logger.error(error_msg)
            return {"_success": False, "error": error_msg}

    except Exception as e:
        _logger.info(
            f"✅ Test Passed: Agent correctly raised an exception for a nonsense action. Error: {e}"
        )
        return {"_success": True}
