# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, TypedDict

__all__ = ["CredentialListParams"]


class CredentialListParams(TypedDict, total=False):
    ending_before: str

    limit: int

    name: str
    """Filter credentials by name"""

    sort_by: str

    sort_order: Literal["asc", "desc"]

    starting_after: str
