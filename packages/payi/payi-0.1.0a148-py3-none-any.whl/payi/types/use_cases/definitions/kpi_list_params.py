# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import TypedDict

__all__ = ["KpiListParams"]


class KpiListParams(TypedDict, total=False):
    cursor: str

    kpi_name: str

    limit: int

    sort_ascending: bool
