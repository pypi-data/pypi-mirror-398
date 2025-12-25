"""
Mobile simulate module data models.
"""
from typing import Any, Dict, List, Optional, Union

class MobileSimulateUploadResult:
    """
    Result of the upload mobile info for mobile simulate.

    Args:
        success (bool): Whether the operation was successful.
        mobile_simulate_context_id (str): The context ID of the mobile info.
            Defaults to "".
        error_message (str): The error message if the operation failed.
            Defaults to "".
    """

    def __init__(
        self,
        success: bool,
        mobile_simulate_context_id: str = "",
        error_message: str = "",
    ):
        self.success = success
        self.mobile_simulate_context_id = mobile_simulate_context_id
        self.error_message = error_message