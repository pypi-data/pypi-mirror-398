# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List

from .._models import BaseModel
from .credentials.packages.credential import Credential

__all__ = ["CredentialListResponse"]


class CredentialListResponse(BaseModel):
    data: List[Credential]
