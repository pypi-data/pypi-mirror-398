"""
BrowserAgent module data models.
"""

from typing import Dict, Generic, Optional, Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class ActOptions:
    """
    Options for configuring the behavior of the act method.
    """

    def __init__(
        self,
        action: str,
        variables: Optional[Dict[str, str]] = None,
        use_vision: Optional[bool] = None,
        timeout: Optional[int] = None,
    ):
        self.action = action
        self.variables = variables
        self.use_vision = use_vision
        self.timeout = timeout


class ActResult:
    """
    Result of the act method.
    """

    def __init__(self, success: bool, message: str):
        self.success = success
        self.message = message


class ObserveOptions:
    """
    Options for configuring the behavior of the observe method.
    """

    def __init__(
        self,
        instruction: str,
        use_vision: Optional[bool] = None,
        selector: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self.instruction = instruction
        self.use_vision = use_vision
        self.selector = selector
        self.timeout = timeout


class ObserveResult:
    """
    Result of the observe method.
    """

    def __init__(self, selector: str, description: str, method: str, arguments: dict):
        self.selector = selector
        self.description = description
        self.method = method
        self.arguments = arguments


class ExtractOptions(Generic[T]):
    """
    Options for configuring the behavior of the extract method.
    """

    def __init__(
        self,
        instruction: str,
        schema: Type[T],
        use_text_extract: Optional[bool] = None,
        use_vision: Optional[bool] = None,
        selector: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self.instruction = instruction
        self.schema = schema
        self.use_text_extract = use_text_extract
        self.use_vision = use_vision
        self.selector = selector
        self.timeout = timeout
