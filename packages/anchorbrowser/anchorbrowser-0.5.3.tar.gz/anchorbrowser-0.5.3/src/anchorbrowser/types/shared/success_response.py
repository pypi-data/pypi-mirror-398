# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from ..._models import BaseModel

__all__ = ["SuccessResponse", "Data"]


class Data(BaseModel):
    status: Optional[str] = None


class SuccessResponse(BaseModel):
    data: Optional[Data] = None
