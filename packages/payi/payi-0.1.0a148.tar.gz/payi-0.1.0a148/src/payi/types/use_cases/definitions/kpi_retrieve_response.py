# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from ...._models import BaseModel

__all__ = ["KpiRetrieveResponse"]


class KpiRetrieveResponse(BaseModel):
    description: str

    name: str

    request_id: str

    created_timestamp: Optional[datetime] = None

    goal: Optional[float] = None

    kpi_type: Optional[Literal["boolean", "number", "percentage", "likert5", "likert7", "likert10"]] = None

    updated_timestamp: Optional[datetime] = None
