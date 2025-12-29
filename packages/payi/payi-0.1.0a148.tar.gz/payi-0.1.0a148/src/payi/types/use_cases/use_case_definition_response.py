# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from ..._models import BaseModel
from ..shared.pay_i_common_models_budget_management_create_limit_base import (
    PayICommonModelsBudgetManagementCreateLimitBase,
)

__all__ = ["UseCaseDefinitionResponse"]


class UseCaseDefinitionResponse(BaseModel):
    description: str

    name: str

    request_id: str

    limit_config: Optional[PayICommonModelsBudgetManagementCreateLimitBase] = None

    logging_enabled: Optional[bool] = None

    type_version: Optional[int] = None
