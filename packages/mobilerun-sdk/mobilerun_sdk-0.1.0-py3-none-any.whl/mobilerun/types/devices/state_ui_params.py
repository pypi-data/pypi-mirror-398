# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["StateUiParams"]


class StateUiParams(TypedDict, total=False):
    filter: bool

    x_device_display_id: Annotated[int, PropertyInfo(alias="X-Device-Display-ID")]
