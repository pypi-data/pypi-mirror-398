# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["ToolPerformWebTaskResponse", "Data"]


class Data(BaseModel):
    result: Optional[str] = None
    """The outcome or answer produced by the autonomous task."""


class ToolPerformWebTaskResponse(BaseModel):
    data: Optional[Data] = None
