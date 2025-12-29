from __future__ import annotations

import inspect
from abc import abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional, Sequence
from dataclasses import dataclass

from payi.types import IngestUnitsParams
from payi.lib.helpers import PayiPropertyNames
from payi.types.ingest_units_params import ProviderResponseFunctionCall
from payi.types.shared.xproxy_error import XproxyError
from payi.types.shared.xproxy_result import XproxyResult
from payi.types.shared_params.ingest_units import IngestUnits
from payi.types.pay_i_common_models_api_router_header_info_param import PayICommonModelsAPIRouterHeaderInfoParam

from .helpers import _set_attr_safe

if TYPE_CHECKING:
    from .instrument import _PayiInstrumentor

class _StreamingType(Enum):
    generator = 0
    iterator = 1
    stream_manager = 2

@dataclass
class _ChunkResult:
    send_chunk_to_caller: bool
    ingest: bool = False

@dataclass
class PriceAs:
    category: Optional[str]
    resource: Optional[str]
    resource_scope: Optional[str]

class _ProviderRequest:
    excluded_headers = {
        "transfer-encoding",
    }

    _instrumented_response_headers_attr = "_instrumented_response_headers"
    _xproxy_result_attr = "xproxy_result"

    def __init__(
            self,
            instrumentor: _PayiInstrumentor,
            category: str,
            streaming_type: _StreamingType,
            module_name: str,
            module_version: str,
            is_aws_client: Optional[bool] = None,
            is_google_vertex_or_genai_client: Optional[bool] = None,
            ) -> None:
        self._instrumentor: _PayiInstrumentor = instrumentor
        self._module_name: str = module_name
        self._module_version: str = module_version  
        self._estimated_prompt_tokens: Optional[int] = None
        self._category: str = category
        self._ingest: IngestUnitsParams = { "category": category, "units": {} } # type: ignore
        self._streaming_type: '_StreamingType' = streaming_type
        self._is_aws_client: Optional[bool] = is_aws_client
        self._is_google_vertex_or_genai_client: Optional[bool] = is_google_vertex_or_genai_client
        self._function_call_builder: Optional[dict[int, ProviderResponseFunctionCall]] = None
        self._building_function_response: bool = False
        self._function_calls: Optional[list[ProviderResponseFunctionCall]] = None
        self._is_large_context: bool = False
        self._internal_request_properties: dict[str, Optional[str]] = {}
        self._price_as: PriceAs = PriceAs(category=None, resource=None, resource_scope=None)
        self._log_prompt_and_response: bool = instrumentor._log_prompt_and_response

    def process_chunk(self, _chunk: Any) -> _ChunkResult:
        return _ChunkResult(send_chunk_to_caller=True)

    def process_synchronous_response(self, response: Any, kwargs: Any) -> Optional[object]:  # noqa: ARG002
        return None
    
    @abstractmethod
    def process_request(self, instance: Any, extra_headers: 'dict[str, str]', args: Sequence[Any], kwargs: Any) -> bool:
        ...
    
    def process_request_prompt(self, prompt: 'dict[str, Any]', args: Sequence[Any], kwargs: 'dict[str, Any]') -> None:
        ...
    
    def process_initial_stream_response(self, response: Any) -> None:
        self.add_instrumented_response_headers(response)

    def remove_inline_data(self, prompt: 'dict[str, Any]') -> bool:# noqa: ARG002
        return False

    @property
    def is_aws_client(self) -> bool:
        return self._is_aws_client if self._is_aws_client is not None else False

    @property
    def is_google_vertex_or_genai_client(self) -> bool:
        return self._is_google_vertex_or_genai_client if self._is_google_vertex_or_genai_client is not None else False

    def process_exception(self, exception: Exception, kwargs: Any, ) -> bool: # noqa: ARG002
        self.exception_to_semantic_failure(exception)
        return True
    
    @property
    def supports_extra_headers(self) -> bool:
        return not self.is_aws_client and not self.is_google_vertex_or_genai_client
    
    @property
    def streaming_type(self) -> '_StreamingType':
        return self._streaming_type

    def add_internal_request_property(self, key: str, value: str) -> None:
        self._internal_request_properties[key] = value

    def exception_to_semantic_failure(self, e: Exception) -> None:
        exception_str = f"{type(e).__name__}"
    
        fields: list[str] = []
    
        for attr in dir(e):
            if not attr.startswith("__"):
                try:
                    value = getattr(e, attr)
                    if value and not inspect.ismethod(value) and not inspect.isfunction(value) and not callable(value):
                        fields.append(f"{attr}={value}")
                except Exception as _ex:
                    pass
 
        self.add_internal_request_property(PayiPropertyNames.failure, exception_str)
        if fields:
            failure_description = ",".join(fields)
            self.add_internal_request_property(PayiPropertyNames.failure_description, failure_description)

        if "http_status_code" not in self._ingest:
            # use a non existent http status code so when presented to the user, the origin is clear
            self._ingest["http_status_code"] = 299

    def add_streaming_function_call(self, index: int, name: Optional[str], arguments: Optional[str]) -> None:
        if not self._function_call_builder:
            self._function_call_builder = {}

        if not index in self._function_call_builder:
            self._function_call_builder[index] = ProviderResponseFunctionCall(name=name or "", arguments=arguments or "")
        else:
            function = self._function_call_builder[index]
            if name:
                function["name"] = function["name"] + name
            if arguments:
                function["arguments"] = (function.get("arguments", "") or "") + arguments

    def add_synchronous_function_call(self, name: str, arguments: Optional[str]) -> None:
        if not self._function_calls:
            self._function_calls = []
            self._ingest["provider_response_function_calls"] = self._function_calls
        self._function_calls.append(ProviderResponseFunctionCall(name=name, arguments=arguments))
    
    def add_instrumented_response_headers(self, response: Any) -> None:
        response_headers  = getattr(response, _ProviderRequest._instrumented_response_headers_attr, {})
        if response_headers:
            self.add_response_headers(response_headers)

    def add_response_headers(self, response_headers: 'dict[str, Any]') -> None:
        self._ingest["provider_response_headers"] = [
            PayICommonModelsAPIRouterHeaderInfoParam(name=k, value=v) 
            for k, v in response_headers.items() 
            if (k_lower := k.lower()) not in _ProviderRequest.excluded_headers and not k_lower.startswith("content-")
        ]

    def find_response_header_value(self, header_name: str) -> Optional[str]:
        response_headers = self._ingest.get("provider_response_headers", None)
        if response_headers:
            header_name = header_name.lower()
            for header in response_headers:
                if header.get("name", "").lower() == header_name:
                    return header.get("value", None)
        return None

    def merge_internal_request_properties(self) -> None:
        if not self._internal_request_properties:
            return
        
        properties = self._ingest.get("properties") or {}
        self._ingest["properties"] = properties
        for key, value in self._internal_request_properties.items():
            if key not in properties:
                properties[key] = value
                
    def update_for_vision(self, input: int) -> int:
        if self._estimated_prompt_tokens:
            vision = input - self._estimated_prompt_tokens
            if (vision > 0):
                key = "vision_large_context" if self._is_large_context else "vision"
                self._ingest["units"][key] = IngestUnits(input=vision, output=0)
                input = self._estimated_prompt_tokens
        
        return input

    @staticmethod
    def assign_xproxy_result(o: Any, xproxy_result: XproxyResult |  XproxyError| None) -> None:
        if xproxy_result:
            _set_attr_safe(o, _ProviderRequest._xproxy_result_attr, xproxy_result)

    @staticmethod
    def process_response_wrapper(wrapped: Any, _instance: Any, args: Any, kwargs: Any) -> Any:
        httpResponse = kwargs.get("response", None)

        r =  wrapped(*args, **kwargs)

        if httpResponse:
            headers = getattr(httpResponse, "headers", None)
            _set_attr_safe(r, _ProviderRequest._instrumented_response_headers_attr, dict(headers) if headers else {})

        return r

    @staticmethod
    async def aprocess_response_wrapper(wrapped: Any, _instance: Any, args: Any, kwargs: Any) -> Any:
        httpResponse = kwargs.get("response", None)

        r = await wrapped(*args, **kwargs)

        if httpResponse:
            headers = getattr(httpResponse, "headers", None)
            _set_attr_safe(r, _ProviderRequest._instrumented_response_headers_attr, dict(headers) if headers else {})

        return r

