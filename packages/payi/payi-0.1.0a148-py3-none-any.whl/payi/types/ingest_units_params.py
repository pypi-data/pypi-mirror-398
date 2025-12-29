# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Iterable, Optional
from datetime import datetime
from typing_extensions import Required, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo
from .shared_params.ingest_units import IngestUnits
from .pay_i_common_models_api_router_header_info_param import PayICommonModelsAPIRouterHeaderInfoParam

__all__ = ["IngestUnitsParams", "ProviderResponseFunctionCall"]


class IngestUnitsParams(TypedDict, total=False):
    category: Required[str]

    units: Required[Dict[str, IngestUnits]]

    end_to_end_latency_ms: Optional[int]

    event_timestamp: Annotated[Union[str, datetime, None], PropertyInfo(format="iso8601")]

    http_status_code: Optional[int]

    properties: Optional[Dict[str, Optional[str]]]

    provider_request_headers: Optional[Iterable[PayICommonModelsAPIRouterHeaderInfoParam]]

    provider_request_json: Optional[str]

    provider_request_reasoning_json: Optional[str]

    provider_response_function_calls: Optional[Iterable[ProviderResponseFunctionCall]]

    provider_response_headers: Optional[Iterable[PayICommonModelsAPIRouterHeaderInfoParam]]

    provider_response_id: Optional[str]

    provider_response_json: Union[str, SequenceNotStr[str], None]

    provider_uri: Optional[str]

    resource: Optional[str]

    time_to_first_completion_token_ms: Optional[int]

    time_to_first_token_ms: Optional[int]

    use_case_properties: Optional[Dict[str, Optional[str]]]

    limit_ids: Annotated[Union[list[str], None], PropertyInfo(alias="xProxy-Limit-IDs")]

    request_tags: Annotated[Union[list[str], None], PropertyInfo(alias="xProxy-Request-Tags")]

    use_case_name: Annotated[Union[str, None], PropertyInfo(alias="xProxy-UseCase-Name")]

    use_case_id: Annotated[Union[str, None], PropertyInfo(alias="xProxy-UseCase-ID")]

    use_case_version: Annotated[Union[int, None], PropertyInfo(alias="xProxy-UseCase-Version")]

    resource_scope: Annotated[Union[str, None], PropertyInfo(alias="xProxy-Resource-Scope")]

    use_case_step: Annotated[Union[str, None], PropertyInfo(alias="xProxy-UseCase-Step")]

    user_id: Annotated[Union[str, None], PropertyInfo(alias="xProxy-User-ID")]

    account_name: Annotated[str, PropertyInfo(alias="xProxy-Account-Name")]

class ProviderResponseFunctionCall(TypedDict, total=False):
    name: Required[str]

    arguments: Optional[str]

class Units(TypedDict, total=False):
    input: int

    output: int
