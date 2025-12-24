# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from typing_extensions import Literal, Required, TypeAlias, TypedDict

from .._types import SequenceNotStr

__all__ = ["DatasetUpdateParams", "PartialDatasetRequestBase", "RestoreRequest"]


class PartialDatasetRequestBase(TypedDict, total=False):
    description: str

    name: str

    tags: SequenceNotStr[str]
    """The tags associated with the entity"""


class RestoreRequest(TypedDict, total=False):
    restore: Required[Literal[True]]
    """Set to true to restore the entity from the database."""


DatasetUpdateParams: TypeAlias = Union[PartialDatasetRequestBase, RestoreRequest]
