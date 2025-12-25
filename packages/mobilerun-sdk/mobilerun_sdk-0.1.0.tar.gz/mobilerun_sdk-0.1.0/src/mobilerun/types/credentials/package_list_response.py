# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List

from ..._models import BaseModel
from .packages.credential import Credential

__all__ = ["PackageListResponse"]


class PackageListResponse(BaseModel):
    data: List[Credential]
