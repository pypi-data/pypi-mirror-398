# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Required, TypedDict

from ..shared_params.pay_i_common_models_budget_management_create_limit_base import (
    PayICommonModelsBudgetManagementCreateLimitBase,
)

__all__ = ["DefinitionCreateParams"]


class DefinitionCreateParams(TypedDict, total=False):
    description: Required[str]

    name: Required[str]

    limit_config: PayICommonModelsBudgetManagementCreateLimitBase

    logging_enabled: Optional[bool]
