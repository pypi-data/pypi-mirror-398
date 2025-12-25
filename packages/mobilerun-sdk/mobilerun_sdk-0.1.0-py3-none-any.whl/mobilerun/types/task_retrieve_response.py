# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from .task import Task
from .._models import BaseModel

__all__ = ["TaskRetrieveResponse"]


class TaskRetrieveResponse(BaseModel):
    task: Task
    """The task"""
