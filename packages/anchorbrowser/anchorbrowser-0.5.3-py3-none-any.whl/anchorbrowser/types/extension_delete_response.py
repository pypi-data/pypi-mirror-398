# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel
from .shared.success_response import SuccessResponse

__all__ = ["ExtensionDeleteResponse"]


class ExtensionDeleteResponse(BaseModel):
    data: Optional[SuccessResponse] = None
