# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["SessionCopyResponse"]


class SessionCopyResponse(BaseModel):
    text: Optional[str] = None
    """The text that was copied"""
