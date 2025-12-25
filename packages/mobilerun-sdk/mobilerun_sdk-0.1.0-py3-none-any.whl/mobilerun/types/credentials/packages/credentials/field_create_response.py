# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing_extensions import Literal

from ....._models import BaseModel
from ..credential import Credential

__all__ = ["FieldCreateResponse"]


class FieldCreateResponse(BaseModel):
    data: Credential

    message: str

    success: Literal[True]
