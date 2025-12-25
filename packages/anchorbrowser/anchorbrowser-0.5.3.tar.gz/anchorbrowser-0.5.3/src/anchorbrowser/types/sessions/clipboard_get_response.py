# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from ..._models import BaseModel

__all__ = ["ClipboardGetResponse", "Data"]


class Data(BaseModel):
    text: Optional[str] = None
    """Text content of the clipboard"""


class ClipboardGetResponse(BaseModel):
    data: Optional[Data] = None
