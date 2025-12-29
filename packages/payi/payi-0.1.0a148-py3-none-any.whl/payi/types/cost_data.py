# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from .._models import BaseModel
from .cost_details import CostDetails
from .shared.pay_i_common_models_budget_management_cost_details_base import (
    PayICommonModelsBudgetManagementCostDetailsBase,
)

__all__ = ["CostData"]


class CostData(BaseModel):
    input: PayICommonModelsBudgetManagementCostDetailsBase

    output: PayICommonModelsBudgetManagementCostDetailsBase

    total: CostDetails
