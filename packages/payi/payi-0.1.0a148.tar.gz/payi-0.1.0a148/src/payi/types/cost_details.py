# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["CostDetails"]


class CostDetails(BaseModel):
    base: float

    overrun_base: Optional[float] = None
