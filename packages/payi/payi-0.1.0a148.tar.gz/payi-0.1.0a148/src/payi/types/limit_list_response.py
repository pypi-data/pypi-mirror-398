# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from .._models import BaseModel
from .total_cost_data import TotalCostData

__all__ = ["LimitListResponse"]


class LimitListResponse(BaseModel):
    limit_creation_timestamp: datetime

    limit_id: str

    limit_name: str

    limit_type: Literal["block", "allow"]

    limit_update_timestamp: datetime

    max: float

    totals: TotalCostData

    threshold: Optional[float] = None
