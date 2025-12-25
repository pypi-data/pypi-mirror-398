# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from .._models import BaseModel

__all__ = ["HookUpdateResponse"]


class HookUpdateResponse(BaseModel):
    """Response model after successfully editing a hook."""

    id: str
    """The subscription ID"""

    state: str
    """The hook state"""

    updated: bool
    """Whether the hook was updated"""

    url: str
    """The webhook URL"""

    events: Optional[List[str]] = None
    """List of subscribed events"""
