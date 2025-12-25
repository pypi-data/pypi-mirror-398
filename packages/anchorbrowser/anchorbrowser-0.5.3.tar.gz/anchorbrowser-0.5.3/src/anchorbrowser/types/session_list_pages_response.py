# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List
from typing_extensions import TypeAlias

from .._models import BaseModel

__all__ = ["SessionListPagesResponse", "SessionListPagesResponseItem"]


class SessionListPagesResponseItem(BaseModel):
    id: str
    """The unique identifier of the page."""

    frontend_url: str
    """The frontend URL for accessing the page."""

    title: str
    """The title of the page."""

    url: str
    """The URL of the page."""


SessionListPagesResponse: TypeAlias = List[SessionListPagesResponseItem]
