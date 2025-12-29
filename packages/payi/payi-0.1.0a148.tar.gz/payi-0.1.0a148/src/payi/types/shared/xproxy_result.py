# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Optional
from typing_extensions import Literal

from ..._models import BaseModel
from .ingest_units import IngestUnits
from ..cost_details import CostDetails
from .pay_i_common_models_budget_management_cost_details_base import PayICommonModelsBudgetManagementCostDetailsBase

__all__ = ["XproxyResult", "Cost", "Limits"]


class Cost(BaseModel):
    currency: Optional[Literal["usd"]] = None

    input: Optional[PayICommonModelsBudgetManagementCostDetailsBase] = None

    output: Optional[PayICommonModelsBudgetManagementCostDetailsBase] = None

    total: Optional[CostDetails] = None


class Limits(BaseModel):
    state: Optional[Literal["ok", "blocked", "blocked_external", "exceeded", "overrun", "failed"]] = None


class XproxyResult(BaseModel):
    account_name: Optional[str] = None

    actions: Optional[List[str]] = None

    blocked_limit_ids: Optional[List[str]] = None

    cost: Optional[Cost] = None

    duplicate_request: Optional[bool] = None

    limits: Optional[Dict[str, Limits]] = None

    request_id: Optional[str] = None

    request_tags: Optional[List[str]] = None

    resource_id: Optional[str] = None

    unknown_units: Optional[Dict[str, IngestUnits]] = None

    use_case_id: Optional[str] = None

    use_case_name: Optional[str] = None

    use_case_step: Optional[str] = None

    user_id: Optional[str] = None

    warnings: Optional[List[str]] = None
