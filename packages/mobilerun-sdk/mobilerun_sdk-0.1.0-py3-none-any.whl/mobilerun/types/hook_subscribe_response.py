# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from .._models import BaseModel

__all__ = ["HookSubscribeResponse"]


class HookSubscribeResponse(BaseModel):
    """Response model after successful subscription."""

    id: str
    """The subscription ID"""

    subscribed: bool
    """Whether subscription was successful"""

    url: str
    """The webhook URL"""

    events: Optional[List[str]] = None
    """List of subscribed events"""

    service: Optional[str] = None
    """Service that receives the webhook"""
