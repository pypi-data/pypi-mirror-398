# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Required, TypedDict

from .._types import SequenceNotStr

__all__ = ["DeviceCreateParams"]


class DeviceCreateParams(TypedDict, total=False):
    apps: Required[Optional[SequenceNotStr[str]]]

    files: Required[Optional[SequenceNotStr[str]]]

    country: str

    name: str
