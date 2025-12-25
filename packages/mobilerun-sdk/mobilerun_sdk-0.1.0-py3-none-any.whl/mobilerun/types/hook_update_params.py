# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

from .._types import SequenceNotStr

__all__ = ["HookUpdateParams"]


class HookUpdateParams(TypedDict, total=False):
    events: Optional[SequenceNotStr[str]]
    """Updated list of events to subscribe to"""

    state: Optional[str]
    """Updated hook state (active, disabled, deleted)"""
