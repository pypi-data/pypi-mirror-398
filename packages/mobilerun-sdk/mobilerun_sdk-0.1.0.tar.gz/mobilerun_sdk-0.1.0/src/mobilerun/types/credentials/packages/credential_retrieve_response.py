# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from ...._models import BaseModel
from .credential import Credential

__all__ = ["CredentialRetrieveResponse"]


class CredentialRetrieveResponse(BaseModel):
    data: Credential
