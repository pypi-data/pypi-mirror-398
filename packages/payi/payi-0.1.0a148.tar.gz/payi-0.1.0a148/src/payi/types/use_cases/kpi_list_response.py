# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from ..._models import BaseModel

__all__ = ["KpiListResponse"]


class KpiListResponse(BaseModel):
    kpi_name: Optional[str] = None

    create_timestamp: Optional[datetime] = None

    kpi_type: Optional[Literal["boolean", "number", "percentage", "likert5", "likert7", "likert10"]] = None

    score: Optional[float] = None

    update_timestamp: Optional[datetime] = None
