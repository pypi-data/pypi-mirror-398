# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["CategoryListResourcesParams"]


class CategoryListResourcesParams(TypedDict, total=False):
    active: Annotated[bool, PropertyInfo(alias="Active")]

    cursor: str

    limit: int

    sort_ascending: bool
