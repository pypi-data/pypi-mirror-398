# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Iterable, Optional
from datetime import datetime
from typing_extensions import Required, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo
from .shared_params.ingest_units import IngestUnits
from .pay_i_common_models_api_router_header_info_param import PayICommonModelsAPIRouterHeaderInfoParam

__all__ = ["BulkIngestRequestParam", "ProviderResponseFunctionCall"]


class ProviderResponseFunctionCall(TypedDict, total=False):
    name: Required[str]

    arguments: Optional[str]


class BulkIngestRequestParam(TypedDict, total=False):
    category: Required[str]

    units: Required[Dict[str, IngestUnits]]

    account_name: Optional[str]

    end_to_end_latency_ms: Optional[int]

    event_timestamp: Annotated[Union[str, datetime, None], PropertyInfo(format="iso8601")]

    http_status_code: Optional[int]

    limit_ids: Optional[SequenceNotStr[str]]

    properties: Optional[Dict[str, Optional[str]]]

    provider_request_headers: Optional[Iterable[PayICommonModelsAPIRouterHeaderInfoParam]]

    provider_request_json: Optional[str]

    provider_request_reasoning_json: Optional[str]

    provider_response_function_calls: Optional[Iterable[ProviderResponseFunctionCall]]

    provider_response_headers: Optional[Iterable[PayICommonModelsAPIRouterHeaderInfoParam]]

    provider_response_id: Optional[str]

    provider_response_json: Union[str, SequenceNotStr[str], None]

    provider_uri: Optional[str]

    request_tags: Optional[SequenceNotStr[str]]

    resource: Optional[str]

    time_to_first_completion_token_ms: Optional[int]

    time_to_first_token_ms: Optional[int]

    use_case_id: Optional[str]

    use_case_name: Optional[str]

    use_case_properties: Optional[Dict[str, Optional[str]]]

    use_case_step: Optional[str]

    use_case_version: Optional[int]

    user_id: Optional[str]
