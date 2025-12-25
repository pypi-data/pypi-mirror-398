from typing import Any, Dict, List, Optional

from .response import ApiResponse


class ContextInfoResult(ApiResponse):
    def __init__(
        self,
        request_id: str = "",
        success: bool = True,
        context_status_data: Optional[List["ContextStatusData"]] = None,
        error_message: str = "",
    ):
        super().__init__(request_id)
        self.success = success
        self.context_status_data = context_status_data or []
        self.error_message = error_message


class ContextSyncResult(ApiResponse):
    def __init__(
        self, request_id: str = "", success: bool = False, error_message: str = ""
    ):
        super().__init__(request_id)
        self.success = success
        self.error_message = error_message


class ContextStatusData:
    def __init__(
        self,
        context_id: str = "",
        path: str = "",
        error_message: str = "",
        status: str = "",
        start_time: int = 0,
        finish_time: int = 0,
        task_type: str = "",
    ):
        self.context_id = context_id
        self.path = path
        self.error_message = error_message
        self.status = status
        self.start_time = start_time
        self.finish_time = finish_time
        self.task_type = task_type

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextStatusData":
        return cls(
            context_id=data.get("contextId", ""),
            path=data.get("path", ""),
            error_message=data.get("errorMessage", ""),
            status=data.get("status", ""),
            start_time=data.get("startTime", 0),
            finish_time=data.get("finishTime", 0),
            task_type=data.get("taskType", ""),
        )