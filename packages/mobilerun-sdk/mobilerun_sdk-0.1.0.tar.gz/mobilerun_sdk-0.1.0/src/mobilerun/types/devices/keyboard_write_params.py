# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["KeyboardWriteParams"]


class KeyboardWriteParams(TypedDict, total=False):
    clear: Required[bool]

    text: Required[str]

    x_device_display_id: Annotated[int, PropertyInfo(alias="X-Device-Display-ID")]
