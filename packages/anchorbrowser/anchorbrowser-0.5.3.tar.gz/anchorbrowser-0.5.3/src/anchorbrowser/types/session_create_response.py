# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["SessionCreateResponse", "Data"]


class Data(BaseModel):
    id: Optional[str] = None
    """Unique identifier for the browser session"""

    cdp_url: Optional[str] = None
    """The CDP websocket connection string"""

    live_view_url: Optional[str] = None
    """The browser session live view url"""


class SessionCreateResponse(BaseModel):
    data: Optional[Data] = None
