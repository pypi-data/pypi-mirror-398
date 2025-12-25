# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Required, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["HookSubscribeParams"]


class HookSubscribeParams(TypedDict, total=False):
    target_url: Required[Annotated[str, PropertyInfo(alias="targetUrl")]]
    """The webhook URL to send notifications to"""

    events: Optional[SequenceNotStr[str]]
    """
    List of task events to subscribe to (created, running, completed, failed,
    cancelled, paused)
    """

    service: Optional[str]
    """Service that receives the webhook"""
