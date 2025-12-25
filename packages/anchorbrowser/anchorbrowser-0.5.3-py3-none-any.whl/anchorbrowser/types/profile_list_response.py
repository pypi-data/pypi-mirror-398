# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal

from .._models import BaseModel

__all__ = ["ProfileListResponse", "Data", "DataItem"]


class DataItem(BaseModel):
    created_at: Optional[datetime] = None
    """The timestamp when the profile was created."""

    description: Optional[str] = None
    """A description of the profile."""

    name: Optional[str] = None
    """The name of the profile."""

    session_id: Optional[str] = None
    """The browser session ID used to create this profile, if applicable."""

    source: Optional[Literal["session"]] = None
    """The source of the profile data."""

    status: Optional[str] = None
    """The current status of the profile."""


class Data(BaseModel):
    count: Optional[int] = None
    """Total number of profiles"""

    items: Optional[List[DataItem]] = None


class ProfileListResponse(BaseModel):
    data: Optional[Data] = None
