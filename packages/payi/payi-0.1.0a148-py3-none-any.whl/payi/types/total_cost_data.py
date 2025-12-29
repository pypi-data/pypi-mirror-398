# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from .._models import BaseModel
from .cost_data import CostData
from .requests_data import RequestsData

__all__ = ["TotalCostData"]


class TotalCostData(BaseModel):
    cost: CostData

    requests: RequestsData
