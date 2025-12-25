# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from .._models import BaseModel

__all__ = ["SessionRetrieveResponse"]


class SessionRetrieveResponse(BaseModel):
    configuration: Optional[object] = None
    """The configuration settings for the session."""

    created_at: Optional[datetime] = None
    """The timestamp when the session was created."""

    credits_used: Optional[float] = None
    """The number of credits consumed by the session."""

    duration: Optional[int] = None
    """The duration of the session in seconds."""

    playground: Optional[bool] = None
    """Whether this is a playground session."""

    proxy_bytes: Optional[int] = None
    """The number of bytes transferred through the proxy."""

    session_id: Optional[str] = None
    """The unique identifier of the session."""

    status: Optional[str] = None
    """The current status of the session."""

    steps: Optional[List[object]] = None
    """Array of steps executed in the session."""

    tags: Optional[object] = None
    """Tags associated with the session."""

    team_id: Optional[str] = None
    """The team ID associated with the session."""

    tokens: Optional[object] = None
    """Token usage information."""
