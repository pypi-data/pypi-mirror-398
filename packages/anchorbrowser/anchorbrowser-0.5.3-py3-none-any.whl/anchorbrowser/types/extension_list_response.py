# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .extension_manifest import ExtensionManifest

__all__ = ["ExtensionListResponse", "Data"]


class Data(BaseModel):
    id: Optional[str] = None
    """Unique identifier for the extension"""

    created_at: Optional[datetime] = FieldInfo(alias="createdAt", default=None)
    """Timestamp when the extension was created"""

    manifest: Optional[ExtensionManifest] = None

    name: Optional[str] = None
    """Extension name"""

    updated_at: Optional[datetime] = FieldInfo(alias="updatedAt", default=None)
    """Timestamp when the extension was last updated"""


class ExtensionListResponse(BaseModel):
    data: Optional[List[Data]] = None
