# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["ResourceListParams"]


class ResourceListParams(TypedDict, total=False):
    category: Required[str]

    active: Annotated[bool, PropertyInfo(alias="Active")]

    cursor: str

    limit: int

    sort_ascending: bool
