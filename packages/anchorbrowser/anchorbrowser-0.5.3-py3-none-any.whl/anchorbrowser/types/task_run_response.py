# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["RunExecuteResponse", "Data"]


class Data(BaseModel):
    message: str
    """Execution result message"""

    success: bool
    """Whether the task executed successfully"""

    task_id: str = FieldInfo(alias="taskId")
    """Task identifier"""

    error: Optional[str] = None
    """Error message if execution failed"""

    execution_time: Optional[float] = FieldInfo(alias="executionTime", default=None)
    """Execution duration in milliseconds"""

    output: Optional[str] = None
    """Task execution output"""


class RunExecuteResponse(BaseModel):
    data: Optional[Data] = None

