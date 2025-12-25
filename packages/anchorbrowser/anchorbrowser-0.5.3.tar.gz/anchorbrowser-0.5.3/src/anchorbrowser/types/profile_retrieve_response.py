# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from .._models import BaseModel

__all__ = ["ProfileRetrieveResponse", "Data"]


class Data(BaseModel):
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


class ProfileRetrieveResponse(BaseModel):
    data: Optional[Data] = None
