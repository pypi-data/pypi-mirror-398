# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Optional
from typing_extensions import Literal

from ..._models import BaseModel

__all__ = ["PayICommonModelsBudgetManagementCreateLimitBase"]


class PayICommonModelsBudgetManagementCreateLimitBase(BaseModel):
    max: float

    limit_type: Optional[Literal["block", "allow"]] = None

    properties: Optional[Dict[str, Optional[str]]] = None

    threshold: Optional[float] = None
