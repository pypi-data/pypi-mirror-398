# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Required, TypedDict

__all__ = ["KpiUpdateParams"]


class KpiUpdateParams(TypedDict, total=False):
    use_case_name: Required[str]

    description: Optional[str]

    goal: Optional[float]
