# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Optional
from typing_extensions import Literal, Required, TypedDict

__all__ = ["PayICommonModelsBudgetManagementCreateLimitBase"]


class PayICommonModelsBudgetManagementCreateLimitBase(TypedDict, total=False):
    max: Required[float]

    limit_type: Literal["block", "allow"]

    properties: Optional[Dict[str, Optional[str]]]

    threshold: Optional[float]
