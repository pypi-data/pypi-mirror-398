# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import TypeAlias

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["HookGetSampleDataResponse", "HookGetSampleDataResponseItem"]


class HookGetSampleDataResponseItem(BaseModel):
    """Sample webhook event data for testing/mapping in Zapier."""

    id: str
    """The subscription ID"""

    created_at: str = FieldInfo(alias="createdAt")
    """ISO timestamp of when the subscription was created"""

    events: List[str]
    """List of subscribed events"""

    state: str
    """The hook state"""

    url: str
    """The webhook URL"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO timestamp of the last update"""


HookGetSampleDataResponse: TypeAlias = List[HookGetSampleDataResponseItem]
