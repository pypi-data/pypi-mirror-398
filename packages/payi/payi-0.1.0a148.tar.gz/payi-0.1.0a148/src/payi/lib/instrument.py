from __future__ import annotations

import os
import copy
import json
import time
import uuid
import atexit
import asyncio
import inspect
import logging
import threading
import traceback
from enum import Enum
from typing import Any, Set, Union, Optional, Sequence, TypedDict, cast
from datetime import datetime, timezone

import nest_asyncio  # type: ignore
from wrapt import wrap_function_wrapper  # type: ignore

from payi import Payi, AsyncPayi, APIStatusError, APIConnectionError, __version__ as _payi_version
from payi.types import IngestUnitsParams
from payi.lib.helpers import PayiHeaderNames, _compact_json
from payi.types.shared import XproxyResult
from payi.types.ingest_response import IngestResponse
from payi.types.shared.xproxy_error import XproxyError
from payi.types.pay_i_common_models_api_router_header_info_param import PayICommonModelsAPIRouterHeaderInfoParam

from .helpers import PayiCategories
from .Stopwatch import Stopwatch
from .StreamWrappers import _GeneratorWrapper, _StreamManagerWrapper, _StreamIteratorWrapper
from .ProviderRequest import PriceAs, _StreamingType, _ProviderRequest

global _g_logger
_g_logger: logging.Logger = logging.getLogger("payi.instrument")

class PayiInstrumentModelMapping(TypedDict, total=False):
    model: str
    price_as_category: Optional[str]
    price_as_resource: Optional[str]
    # "global", "datazone", "region", "region.<region_name>"
    resource_scope: Optional[str]   

class PayiInstrumentAwsBedrockConfig(TypedDict, total=False):
    guardrail_trace: Optional[bool]
    add_streaming_xproxy_result: Optional[bool]
    model_mappings: Optional[Sequence[PayiInstrumentModelMapping]]

class PayiInstrumentOpenAiAzureConfig(TypedDict, total=False):
    # map deployment name known model
    model_mappings: Sequence[PayiInstrumentModelMapping] 

class PayiInstrumentAnthropicAzureConfig(TypedDict, total=False):
    # map deployment name known model
    model_mappings: Sequence[PayiInstrumentModelMapping] 

class PayiInstrumentOpenAiConfig(TypedDict, total=False):
    # map deployment name known model
    azure: PayiInstrumentOpenAiAzureConfig

class PayiInstrumentAnthropicConfig(TypedDict, total=False):
    # map deployment name known model
    azure: PayiInstrumentAnthropicAzureConfig

class PayiInstrumentOfflineInstrumentationConfig(TypedDict, total=False):
    file_name: str

class PayiInstrumentConfig(TypedDict, total=False):
    proxy: bool
    global_instrumentation: bool
    instrument_inline_data: bool
    connection_error_logging_window: int
    limit_ids: Optional["list[str]"]
    use_case_name: Optional[str]
    use_case_id: Optional[str]
    use_case_version: Optional[int]
    use_case_properties: Optional["dict[str, Optional[str]]"]
    user_id: Optional[str]
    account_name: Optional[str]
    request_tags: Optional["list[str]"]
    request_properties: Optional["dict[str, Optional[str]]"]
    aws_config: Optional[PayiInstrumentAwsBedrockConfig]
    azure_openai_config: Optional[PayiInstrumentOpenAiAzureConfig]
    openai_config: Optional[PayiInstrumentOpenAiConfig]
    anthropic_config: Optional[PayiInstrumentAnthropicConfig]
    offline_instrumentation: Optional[PayiInstrumentOfflineInstrumentationConfig]

class PayiContext(TypedDict, total=False):
    use_case_name: Optional[str]
    use_case_id: Optional[str]
    use_case_version: Optional[int]
    use_case_step: Optional[str]
    use_case_properties: Optional["dict[str, Optional[str]]"]
    limit_ids: Optional['list[str]']
    user_id: Optional[str]
    account_name: Optional[str]
    request_tags: Optional["list[str]"]
    request_properties: Optional["dict[str, Optional[str]]"]
    price_as_category: Optional[str]
    price_as_resource: Optional[str]
    resource_scope: Optional[str]
    log_prompt_and_response: Optional[bool]
    last_result: Optional[Union[XproxyResult, XproxyError]]

class PayiInstanceDefaultContext(TypedDict, total=False):
    use_case_name: Optional[str]
    use_case_id: Optional[str]
    use_case_version: Optional[int]
    use_case_properties: Optional["dict[str, str]"]
    limit_ids: Optional['list[str]']
    user_id: Optional[str]
    account_name: Optional[str]
    request_properties: Optional["dict[str, str]"]
    price_as_category: Optional[str]
    price_as_resource: Optional[str]
    resource_scope: Optional[str]

class _Context(TypedDict, total=False):
    proxy: Optional[bool]
    use_case_name: Optional[str]
    use_case_id: Optional[str]
    use_case_version: Optional[int]
    use_case_step: Optional[str]
    use_case_properties: Optional["dict[str, Optional[str]]"]
    limit_ids: Optional['list[str]']
    user_id: Optional[str]
    account_name: Optional[str]
    request_properties: Optional["dict[str, Optional[str]]"]
    price_as_category: Optional[str]
    price_as_resource: Optional[str]
    resource_scope: Optional[str]
    log_prompt_and_response: Optional[bool]

class _IsStreaming(Enum):
    false = 0
    true = 1 
    kwargs = 2

class _ThreadLocalContextStorage(threading.local):
    """
    Thread-local storage for context stacks. Each thread gets its own context stack.
    
    Note: We don't use __init__ because threading.local's __init__ semantics are tricky.
    Instead, we lazily initialize the context_stack attribute in the property accessor.
    """
    context_stack: "list[_Context]"

class _InternalTrackContext:
    def __init__(
        self,
        context: _Context,
    ) -> None:
        self._context = context

    def __enter__(self) -> Any:
        if not _instrumentor:
            return self
        
        _instrumentor.__enter__()
        _instrumentor._init_current_context(**self._context)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if _instrumentor:
            _instrumentor.__exit__(exc_type, exc_val, exc_tb)

class _PayiInstrumentor:
    _not_instrumented: str = "<not_instrumented>"
    _instrumented_module_header_name: str = "xProxy-Instrumented-Module"

    def __init__(
        self,
        payi: Optional[Payi],
        apayi: Optional[AsyncPayi],
        instruments: Union[Set[str], None] = None,
        log_prompt_and_response: bool = True,
        logger: Optional[logging.Logger] = None,
        global_config: PayiInstrumentConfig = {},
        caller_filename: str = ""
    ):
        global _g_logger
        self._logger: logging.Logger = logger if logger else _g_logger

        self._logger.info(f"Pay-i instrumentor version: {_payi_version}")

        self._payi: Optional[Payi] = payi
        self._apayi: Optional[AsyncPayi] = apayi

        if self._payi:
            _g_logger.debug(f"Pay-i instrumentor initialized with Payi instance: {self._payi}")
        if self._apayi:
            _g_logger.debug(f"Pay-i instrumentor initialized with AsyncPayi instance: {self._apayi}")            

        # Thread-local storage for context stacks - each thread gets its own stack
        self._thread_local_storage = _ThreadLocalContextStorage()
        
        self._log_prompt_and_response: bool = log_prompt_and_response

        self._blocked_limits: set[str] = set()
        self._exceeded_limits: set[str] = set()

        # by not setting to time.time() the first connection error is always logged
        self._api_connection_error_last_log_time: float = 0
        self._api_connection_error_count: int = 0
        self._api_connection_error_window: int = global_config.get("connection_error_logging_window", 60)
        if self._api_connection_error_window < 0:
            raise ValueError("connection_error_logging_window must be a non-negative integer")

        # default is instrument and ingest metrics
        self._proxy_default: bool = global_config.get("proxy", False)

        self._instrument_inline_data: bool = global_config.get("instrument_inline_data", False)

        self._last_result: Optional[Union[XproxyResult, XproxyError]] = None

        self._offline_instrumentation = global_config.pop("offline_instrumentation", None)
        self._offline_ingest_packets: list[IngestUnitsParams] = []
        self._offline_instrumentation_file_name: Optional[str] = None
        
        if self._offline_instrumentation is not None:
            timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            self._offline_instrumentation_file_name = self._offline_instrumentation.get("file_name", f"payi_instrumentation_{timestamp}.json")
            
            # Register exit handler to write packets when process exits
            atexit.register(lambda: self._write_offline_ingest_packets())

        global_instrumentation = global_config.pop("global_instrumentation", True)

        # configure first, then instrument
        aws_config = global_config.get("aws_config", None)
        if aws_config:
            from .BedrockInstrumentor import BedrockInstrumentor
            BedrockInstrumentor.configure(aws_config=aws_config)

        azure_openai_config = (global_config.get("openai_config", None) or {}).get("azure", None)
        if not azure_openai_config:
            # azure_openai_config will be deprecated in the future
            azure_openai_config = global_config.get("azure_openai_config", None)
        if azure_openai_config:
            from .OpenAIInstrumentor import OpenAiInstrumentor
            OpenAiInstrumentor.configure(azure_openai_config=azure_openai_config)

        anthropic_config = global_config.get("anthropic_config", None)
        if anthropic_config:
            from .AnthropicInstrumentor import AnthropicInstrumentor
            AnthropicInstrumentor.configure(anthropic_config=anthropic_config)

        if instruments is None or "*" in instruments:
            self._instrument_all()
        else:
            self._instrument_specific(instruments=instruments)

        self._instrument_futures()

        if global_instrumentation:
            if "proxy" not in global_config:
                global_config["proxy"] = self._proxy_default

            # Use default clients if not provided for global ingest instrumentation
            self._ensure_payi_clients()

            if "use_case_name" not in global_config and caller_filename:
                description = f"Default use case for {caller_filename}.py"
                try:
                    if self._payi:
                        self._payi.use_cases.definitions.create(name=caller_filename, description=description)
                    elif self._apayi:
                        self._call_async_use_case_definition_create(use_case_name=caller_filename, use_case_description=description)
                    else:
                        # in the case of _local_instrumentation is not None
                        pass
                    global_config["use_case_name"] = caller_filename
                except Exception as e:
                    self._logger.error(f"Error creating default use case definition based on file name {caller_filename}: {e}")

            self.__enter__()

            # _init_current_context will update the current context stack location
            context: _Context = {}

            # Copy allowed keys from global_config into context
            # Dynamically use keys from _Context TypedDict
            context_keys = list(_Context.__annotations__.keys()) if hasattr(_Context, '__annotations__') else []
            for key in context_keys:
                if key in global_config:
                    context[key] = global_config[key] # type: ignore[literal-required]

            self._init_current_context(**context)
            self._logger.debug(f"Pay-i global instrumented context: {self._create_logged_context(self._context_safe)}")
        else:
            self._logger.debug(f"Pay-i global instrumented context skipped")

    def _ensure_payi_clients(self) -> None:
        if self._offline_instrumentation is not None:
            return

        if not self._payi and not self._apayi:
            self._payi = Payi()
            self._apayi = AsyncPayi()

    def _instrument_futures(self) -> None:
        """Install hooks for all common concurrent execution patterns."""
        def _thread_submit_wrapper(wrapped: Any, instance: Any, args: Any, kwargs: Any) -> Any:
            return self._thread_submit_wrapper(wrapped, instance, args, kwargs)

        def _create_task_wrapper(wrapped: Any, instance: Any, args: Any, kwargs: Any) -> Any:
            return self._create_task_wrapper(wrapped, instance, args, kwargs)

        def _gather_wrapper(wrapped: Any, instance: Any, args: Any, kwargs: Any) -> Any:
            return self._gather_wrapper(wrapped, instance, args, kwargs)

        try:
            wrap_function_wrapper("concurrent.futures", "ThreadPoolExecutor.submit", _thread_submit_wrapper)
        except Exception as e:
            self._logger.debug(f"Failed to wrap ThreadPoolExecutor.submit: {e}")

        try:
            wrap_function_wrapper("asyncio", "create_task", _create_task_wrapper)
        except Exception as e:
            self._logger.debug(f"Failed to wrap asyncio.create_task: {e}")

        try:
            wrap_function_wrapper("asyncio", "gather", _gather_wrapper)
        except Exception as e:
            self._logger.debug(f"Failed to wrap asyncio.create_task: {e}")

    def _instrument_all(self) -> None:
        self._instrument_openai()
        self._instrument_anthropic()
        self._instrument_aws_bedrock()
        self._instrument_google_vertex()
        self._instrument_google_genai()

    def _instrument_specific(self, instruments: Set[str]) -> None:
        if PayiCategories.openai in instruments or PayiCategories.azure_openai in instruments:
            self._instrument_openai()
        if PayiCategories.anthropic in instruments:
            self._instrument_anthropic()
        if PayiCategories.aws_bedrock in instruments:
            self._instrument_aws_bedrock()
        if PayiCategories.google_vertex in instruments:
            self._instrument_google_vertex()
            self._instrument_google_genai()

    def _instrument_openai(self) -> None:
        from .OpenAIInstrumentor import OpenAiInstrumentor

        try:
            OpenAiInstrumentor.instrument(self)

        except Exception as e:
            self._logger.error(f"Error instrumenting OpenAI: {e}")

    def _instrument_anthropic(self) -> None:
        from .AnthropicInstrumentor import AnthropicInstrumentor

        try:
            AnthropicInstrumentor.instrument(self)

        except Exception as e:
            self._logger.error(f"Error instrumenting Anthropic: {e}")

    def _instrument_aws_bedrock(self) -> None:
        from .BedrockInstrumentor import BedrockInstrumentor

        try:
            BedrockInstrumentor.instrument(self)

        except Exception as e:
            self._logger.error(f"Error instrumenting AWS bedrock: {e}")

    def _instrument_google_vertex(self) -> None:
        from .VertexInstrumentor import VertexInstrumentor

        try:
            VertexInstrumentor.instrument(self)

        except Exception as e:
            self._logger.error(f"Error instrumenting Google Vertex: {e}")

    def _instrument_google_genai(self) -> None:
        from .GoogleGenAiInstrumentor import GoogleGenAiInstrumentor

        try:
            GoogleGenAiInstrumentor.instrument(self)

        except Exception as e:
            self._logger.error(f"Error instrumenting Google GenAi: {e}")

    def _thread_submit_wrapper(
        self,
        wrapped: Any,
        _instance: Any,
        args: Any,
        kwargs: Any,
    ) -> Any:
        if len(args) > 0:
            fn = args[0]
            fn_args = args[1:]
            captured_context = copy.deepcopy(self._context_safe)

            def context_wrapper(*inner_args: Any, **inner_kwargs: Any) -> Any:
                with self:
                    # self._context_stack[-1].update(captured_context)
                    self._init_current_context(**captured_context)
                    return fn(*inner_args, **inner_kwargs)

            return wrapped(context_wrapper, *fn_args, **kwargs)
        return wrapped(*args, **kwargs)

    def _create_task_wrapper(
        self,
        wrapped: Any,
        _instance: Any,
        args: Any,
        kwargs: Any,
    ) -> Any:
        # Handle different create_task signatures across Python versions:
        # Python 3.7-3.10: create_task(coro, *, name=None)
        # Python 3.11+: create_task(coro, *, name=None, context=None)
        
        if len(args) > 0:
            coro = args[0]
            
            # Only wrap if it's actually a coroutine object
            if inspect.iscoroutine(coro):
                # Capture the current context before the task is created
                captured_context = copy.deepcopy(self._context_safe)

                async def context_preserving_wrapper() -> Any:
                    # Set up the context in the new task
                    with self:
                        self._init_current_context(**captured_context)
                        # Await the original coroutine
                        return await coro
                
                # Create a new coroutine with context preservation
                wrapped_coro = context_preserving_wrapper()
                
                # Replace the first argument with our wrapped coroutine
                new_args = (wrapped_coro,) + args[1:]
                
                # Call the original create_task with the wrapped coroutine
                # This works for both Python 3.7-3.10 and 3.11+ because we're
                # passing through all other args and kwargs unchanged
                return wrapped(*new_args, **kwargs)
        
        # If not a coroutine or no args, pass through unchanged
        return wrapped(*args, **kwargs)

    def _gather_wrapper(
        self,
        wrapped: Any,
        _instance: Any,
        args: Any,
        kwargs: Any,
    ) -> Any:
        # Handle asyncio.gather which accepts *coros_or_futures
        # Signature across Python versions:
        # Python 3.7-3.9: gather(*coros_or_futures, loop=None, return_exceptions=False)
        # Python 3.10+: gather(*coros_or_futures, return_exceptions=False) - loop deprecated
        # Python 3.12+: gather(*coros_or_futures, return_exceptions=False) - loop removed
        
        if not args:
            # No coroutines/futures passed, call original
            return wrapped(*args, **kwargs)
        
        # Capture the current context before wrapping
        captured_context = copy.deepcopy(self._context_safe)
        
        # Wrap each coroutine with context preservation
        wrapped_coros: list[Any] = []
        
        for coro_or_future in args:
            if inspect.iscoroutine(coro_or_future):
                # Create a wrapper coroutine that preserves context
                # We need to capture coro_or_future in a closure properly
                async def context_preserving_wrapper(coro: Any = coro_or_future, ctx: _Context = captured_context) -> Any:
                    with self:
                        self._init_current_context(**ctx)
                        return await coro
                
                wrapped_coros.append(context_preserving_wrapper())
            else:
                # Futures, Tasks, or other awaitables - pass through unchanged
                # They already have their execution context bound
                wrapped_coros.append(coro_or_future)
        
        # Call the original gather with wrapped coroutines
        # Pass through all kwargs (return_exceptions, and loop for older Python versions)
        return wrapped(*wrapped_coros, **kwargs)
        
    @staticmethod
    def _model_mapping_to_context_dict(model_mappings: Sequence[PayiInstrumentModelMapping]) -> 'dict[str, _Context]':
        context: dict[str, _Context] = {}
        for mapping in model_mappings:
            model = mapping.get("model", "")
            if not model:
                continue

            price_as_category = mapping.get("price_as_category", None)
            price_as_resource = mapping.get("price_as_resource", None)
            resource_scope = mapping.get("resource_scope", None)

            if not price_as_category and not price_as_resource:
                continue

            context[model] = _Context(
                price_as_category=price_as_category,
                price_as_resource=price_as_resource,
                resource_scope=resource_scope,
            )
        return context

    def _write_offline_ingest_packets(self) -> None:
        if not self._offline_instrumentation_file_name or not self._offline_ingest_packets:
            return
            
        try:
            # Convert datetime objects to ISO strings for JSON serialization
            serializable_packets: list[IngestUnitsParams] = []
            for packet in self._offline_ingest_packets:
                serializable_packet = packet.copy()
                
                # Convert datetime fields to ISO format strings
                if 'event_timestamp' in serializable_packet and isinstance(serializable_packet['event_timestamp'], datetime):
                    serializable_packet['event_timestamp'] = serializable_packet['event_timestamp'].isoformat()
                    
                serializable_packets.append(serializable_packet)
            
            with open(self._offline_instrumentation_file_name, 'w', encoding='utf-8') as f:
                json.dump(serializable_packets, f)
                
            self._logger.debug(f"Written {len(self._offline_ingest_packets)} ingest packets to {self._offline_instrumentation_file_name}")
            
        except Exception as e:
            self._logger.error(f"Error writing offline ingest packets to {self._offline_instrumentation_file_name}: {e}")

    @staticmethod
    def _create_logged_context(
            context: _Context
    ) -> dict[str, Any]:
        return {k: v for k, v in context.items() if v is not None}

    @staticmethod
    def _create_logged_ingest_units(
        ingest_units: IngestUnitsParams,
    ) -> IngestUnitsParams:
        # remove large and potentially sensitive data from the log
        log_ingest_units: IngestUnitsParams = ingest_units.copy()
        
        log_ingest_units.pop('provider_request_json', None)
        log_ingest_units.pop('provider_response_json', None)

        # Pop system.stack_trace from properties if it exists
        if 'properties' in log_ingest_units and isinstance(log_ingest_units['properties'], dict):
            log_ingest_units['properties'].pop('system.stack_trace', None)

        return log_ingest_units
        
    def _after_invoke_update_request(
        self,
        request: _ProviderRequest,
        extra_headers: 'dict[str, str]') -> None:
        ingest_units = request._ingest

        if request._module_version:
            extra_headers[_PayiInstrumentor._instrumented_module_header_name] = f'{request._module_name}/{request._module_version}'

        if request._function_call_builder:
            # convert the function call builder to a list of function calls
            ingest_units["provider_response_function_calls"] = list(request._function_call_builder.values())

        if "provider_response_id" not in ingest_units or not ingest_units["provider_response_id"]:
            ingest_units["provider_response_id"] = f"payi_{uuid.uuid4()}"

        if 'resource' not in ingest_units or ingest_units['resource'] == '':
            ingest_units['resource'] = "system.unknown_model"

        request.merge_internal_request_properties()

        request_json = ingest_units.get('provider_request_json', "")
        if request_json and self._instrument_inline_data is False:
            try:
                prompt_dict = json.loads(request_json)
                if request.remove_inline_data(prompt_dict):
                    self._logger.debug(f"Removed inline data from provider_request_json")
                    # store the modified dict back as JSON string
                    ingest_units['provider_request_json'] = _compact_json(prompt_dict)

            except Exception as e:
                self._logger.error(f"Error serializing provider_request_json: {e}")

        if int(ingest_units.get("http_status_code") or 0) < 400:
            units = ingest_units.get("units", {})
            if not units or all(unit.get("input", 0) == 0 and unit.get("output", 0) == 0 for unit in units.values()):
                self._logger.info('ingesting with no token counts')

    def _process_ingest_units_response(self, ingest_response: IngestResponse) -> None:
        if ingest_response.xproxy_result and ingest_response.xproxy_result.warnings and self._logger.isEnabledFor(logging.WARNING):
            warning_message = "\n".join(ingest_response.xproxy_result.warnings)
            self._logger.warning(f"Pay-i ingest result warnings:\n{warning_message}")

        if ingest_response.xproxy_result.limits:
            for limit_id, state in ingest_response.xproxy_result.limits.items():
                removeBlockedId: bool = False

                if state.state == "blocked":
                    self._blocked_limits.add(limit_id)
                elif state.state == "exceeded":
                    self._exceeded_limits.add(limit_id)
                    removeBlockedId = True
                elif state.state == "ok":
                    removeBlockedId = True

                # opportunistically remove blocked limits
                if removeBlockedId:
                    self._blocked_limits.discard(limit_id)

    def _process_ingest_connection_error(self, e: APIConnectionError, ingest_units: IngestUnitsParams) -> XproxyError:
        now = time.time()

        if (now - self._api_connection_error_last_log_time) > self._api_connection_error_window:
            # If previous window had suppressed errors, log the count
            append = ""
            if self._api_connection_error_count > 0:
                append = f", {self._api_connection_error_count} APIConnectionError exceptions in the last {self._api_connection_error_window} seconds"

            # Log the current error
            self._logger.error(f"Error Pay-i ingesting: connection exception {e}, request {ingest_units}{append}")
            self._api_connection_error_last_log_time = now
            self._api_connection_error_count = 0
        else:
            # Suppress and count
            self._api_connection_error_count += 1

        return XproxyError(code="api_connection_error", message=str(e))

    async def _aingest_units_worker(self, request: _ProviderRequest) -> Optional[Union[XproxyResult, XproxyError]]:
        ingest_response: Optional[IngestResponse] = None
        ingest_units = request._ingest

        self._logger.debug(f"_aingest_units")

        extra_headers: 'dict[str, str]' = {}
        self._after_invoke_update_request(request, extra_headers=extra_headers)

        try:
            if self._logger.isEnabledFor(logging.DEBUG):
                self._logger.debug(f"_aingest_units: sending ({self._create_logged_ingest_units(ingest_units)})")

            if self._apayi:    
                ingest_response = await self._apayi.ingest.units(**ingest_units, extra_headers=extra_headers)
            elif self._payi:
                ingest_response = self._payi.ingest.units(**ingest_units, extra_headers=extra_headers)
            elif self._offline_instrumentation is not None:
                self._offline_ingest_packets.append(ingest_units.copy())

                # simulate a successful ingest for local instrumentation
                now=datetime.now(timezone.utc)
                ingest_response = IngestResponse(
                    event_timestamp=now,
                    ingest_timestamp=now,
                    request_id="local_instrumentation",
                    xproxy_result=XproxyResult(request_id="local_instrumentation"))
                pass
                
            else:
                self._logger.error("No payi instance to ingest units")
                return XproxyError(code="configuration_error", message="No Payi or AsyncPayi instance configured for ingesting units")

            self._logger.debug(f"_aingest_units: success ({ingest_response})")

            if ingest_response:
                self._process_ingest_units_response(ingest_response)

            return ingest_response.xproxy_result

        except APIConnectionError as api_ex:
            return self._process_ingest_connection_error(api_ex, ingest_units)

        except APIStatusError as api_status_ex:
            return self._process_api_status_error(api_status_ex)      

        except Exception as ex:
            self._logger.error(f"Error Pay-i async ingesting: exception {ex}, request {ingest_units}")
            return XproxyError(code="unknown_error", message=str(ex))
    
    async def _aingest_units(self, request: _ProviderRequest) -> Optional[Union[XproxyResult, XproxyError]]:
        return self.set_xproxy_result(await self._aingest_units_worker(request))

    def _call_async_use_case_definition_create(self, use_case_name: str, use_case_description: str) -> None:
        if not self._apayi:
            return

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        
        try:
            if loop and loop.is_running():
                nest_asyncio.apply(loop) # type: ignore
                asyncio.run(self._apayi.use_cases.definitions.create(name=use_case_name, description=use_case_description))                
            else:
                # When there's no running loop, create a new one
                asyncio.run(self._apayi.use_cases.definitions.create(name=use_case_name, description=use_case_description))
        except Exception as e:
            self._logger.error(f"Error calling async use_cases.definitions.create synchronously: {e}")

    def _call_aingest_sync(self, request: _ProviderRequest) -> Optional[Union[XproxyResult, XproxyError]]:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        
        try:
            if loop and loop.is_running():
                nest_asyncio.apply(loop) # type: ignore
                return asyncio.run(self._aingest_units(request))
            else:
                # When there's no running loop, create a new one
                return asyncio.run(self._aingest_units(request))
        except Exception as e:
            self._logger.error(f"Error calling aingest_units synchronously: {e}")
        return None
        
    def _process_api_status_error(self, e: APIStatusError) -> Optional[XproxyError]:
        try:
            body_dict: dict[str, Any] = {}

            # Try to get the response body as JSON
            body = e.body
            if body is None:
                self._logger.warning(f"Pay-i ingest exception {e}, status {e.status_code} has no body")
                return XproxyError(code="unknown_error", message=str(e))

            # If body is bytes, decode to string
            if isinstance(body, bytes):
                body = body.decode("utf-8")
            if isinstance(body, dict):
                body_dict = body # type: ignore
            else:
                body = str(body)

            if not body_dict:
                try:
                    body_dict = json.loads(body)  # type: ignore
                except Exception:
                    body_type = type(body).__name__ # type: ignore
                    self._logger.warning(f"Pay-i ingest exception {e}, status {e.status_code} cannot parse response JSON body for body type {body_type}")
                    return XproxyError(code="invalid_json", message=str(e))

            xproxy_error = body_dict.get("xproxy_error", {})
            code = xproxy_error.get("code", "unknown_error")
            message = xproxy_error.get("message", str(e))
            return XproxyError(code=code, message=message)

        except Exception as ex:
            self._logger.warning(f"Pay-i ingest exception {e}, status {e.status_code} processing handled exception {ex}")
            return XproxyError(code="exception", message=str(ex))

    def _ingest_units_worker(self, request: _ProviderRequest) -> Optional[Union[XproxyResult, XproxyError]]:
        ingest_response: Optional[IngestResponse] = None
        ingest_units = request._ingest

        self._logger.debug(f"_ingest_units")

        extra_headers: 'dict[str, str]' = {}
        self._after_invoke_update_request(request, extra_headers=extra_headers)

        try:
            if self._payi:
                if self._logger.isEnabledFor(logging.DEBUG):
                    self._logger.debug(f"_ingest_units: sending ({self._create_logged_ingest_units(ingest_units)})")

                ingest_response = self._payi.ingest.units(**ingest_units, extra_headers=extra_headers)
                self._logger.debug(f"_ingest_units: success ({ingest_response})")

                self._process_ingest_units_response(ingest_response)

                return ingest_response.xproxy_result
            elif self._apayi:
                # task runs async. aingest_units will invoke the callback and post process
                sync_response = self._call_aingest_sync(request)
                self._logger.debug(f"_ingest_units: apayi success ({sync_response})")
                return sync_response
            elif self._offline_instrumentation is not None:
                self._offline_ingest_packets.append(ingest_units.copy())

                # simulate a successful ingest for local instrumentation
                return XproxyResult(request_id="local_instrumentation")

            else:
                self._logger.error("No payi instance to ingest units")
                return XproxyError(code="configuration_error", message="No Payi or AsyncPayi instance configured for ingesting units")

        except APIConnectionError as api_ex:
            return self._process_ingest_connection_error(api_ex, ingest_units)

        except APIStatusError as api_status_ex:
            return self._process_api_status_error(api_status_ex)      

        except Exception as ex:
            self._logger.error(f"Error Pay-i async ingesting: exception {ex}, request {ingest_units}")
            return XproxyError(code="unknown_error", message=str(ex))
        
    def _ingest_units(self, request: _ProviderRequest) -> Optional[Union[XproxyResult, XproxyError]]:
        return self.set_xproxy_result(self._ingest_units_worker(request))

    @property
    def _context_stack(self) -> "list[_Context]":
        """
        Get the thread-local context stack. On first access per thread, 
        initializes with the current state of the main thread's context stack.
        """
        # Lazy-initialize the context_stack for this thread if it doesn't exist
        if not hasattr(self._thread_local_storage, 'context_stack'):
            self._thread_local_storage.context_stack = []
        
        stack = self._thread_local_storage.context_stack

        
        return stack

    def _setup_call_func(
        self
        ) -> _Context:

        if len(self._context_stack) > 0:
            # copy current context into the upcoming context
            return self._context_stack[-1].copy()

        return {}

    @staticmethod
    def _valid_str_or_none(value: Optional[str], default: Optional[str] = None) -> Optional[str]:
        if value is None:
            return default
        elif len(value) == 0:
            # an empty string explicitly blocks the default value
            return None
        else:
            return value
        
    @staticmethod
    def _valid_properties_or_none(value: Optional["dict[str, Optional[str]]"], default: Optional["dict[str, Optional[str]]"] = None) -> Optional["dict[str, Optional[str]]"]:
        if value is None:
            return default.copy() if default else None
        elif len(value) == 0:
            # an empty dictionary explicitly blocks the default value
            return None
        elif default:
            # merge dictionaries, child overrides parent keys
            merged = default.copy()
            merged.update(value)
            return merged
        else:
            return value.copy()

    def _init_current_context(
        self,
        proxy: Optional[bool] = None,
        limit_ids: Optional["list[str]"] = None,
        use_case_name: Optional[str]= None,
        use_case_id: Optional[str]= None,
        use_case_version: Optional[int]= None,
        use_case_step: Optional[str]= None,
        user_id: Optional[str]= None,
        account_name: Optional[str]= None,
        log_prompt_and_response: Optional[bool] = None,
        request_properties: Optional["dict[str, Optional[str]]"] = None,
        use_case_properties: Optional["dict[str, Optional[str]]"] = None,
        price_as_category: Optional[str] = None,
        price_as_resource: Optional[str] = None,
        resource_scope: Optional[str] = None,
        ) -> None:

        # there will always be a current context
        context: _Context = self._context # type: ignore
        parent_context: _Context = self._context_stack[-2] if len(self._context_stack) > 1 else {}

        parent_proxy = parent_context.get("proxy", self._proxy_default)
        context["proxy"] = proxy if proxy is not None else parent_proxy

        parent_log_prompt_and_response = parent_context.get("log_prompt_and_response", None)
        context["log_prompt_and_response"] = log_prompt_and_response if log_prompt_and_response is not None else parent_log_prompt_and_response

        parent_use_case_name = parent_context.get("use_case_name", None)
        parent_use_case_id = parent_context.get("use_case_id", None)
        parent_use_case_version = parent_context.get("use_case_version", None)
        parent_use_case_step = parent_context.get("use_case_step", None)

        assign_use_case_values = False

        if use_case_name is None:
            if parent_use_case_name:
                # If no use_case_name specified, use previous values
                context["use_case_name"] = parent_use_case_name
                assign_use_case_values = True
        elif len(use_case_name) == 0:
            # Empty string explicitly blocks inheriting from the parent state
            context["use_case_name"] = None
            context["use_case_id"] = None
            context["use_case_version"] = None
            context["use_case_step"] = None
            context["use_case_properties"] = None
        else:
            if use_case_name == parent_use_case_name:
                # Same use case name, use previous ID unless new one specified
                context["use_case_name"] = use_case_name
            else:
                context["use_case_name"] = use_case_name

                # Different use case name, use specified ID or generate one. 
                # By assigning to a new value to parent_use_case_id we keep the assignment logic below simple and consistent with
                # assign the caller's use_case_id if specified or the newly generated one. 
                # The use case id stored in the parent context is not mutated.
                parent_use_case_id = str(uuid.uuid4())

            assign_use_case_values = True

        if assign_use_case_values:
            context["use_case_version"] = use_case_version if use_case_version is not None else parent_use_case_version
            context["use_case_id"] =  self._valid_str_or_none(use_case_id, parent_use_case_id)
            context["use_case_step"] = self._valid_str_or_none(use_case_step, parent_use_case_step)

            parent_use_case_properties = parent_context.get("use_case_properties", None)
            context["use_case_properties"] = self._valid_properties_or_none(use_case_properties, parent_use_case_properties)

        parent_limit_ids = parent_context.get("limit_ids", None)
        if limit_ids is None:
            # use the parent limit_ids if it exists
            context["limit_ids"] = parent_limit_ids
        elif len(limit_ids) == 0:
            # caller passing an empty array explicitly blocks inheriting from the parent state
            context["limit_ids"] = None
        else:
            # union of new and parent lists if the parent context contains limit ids
            context["limit_ids"] = list(set(limit_ids) | set(parent_limit_ids)) if parent_limit_ids else limit_ids.copy()

        parent_user_id = parent_context.get("user_id", None)
        context["user_id"] = self._valid_str_or_none(user_id, parent_user_id)

        parent_account_name = parent_context.get("account_name", None)
        context["account_name"] = self._valid_str_or_none(account_name, parent_account_name)

        parent_request_properties = parent_context.get("request_properties", None)
        context["request_properties"] = self._valid_properties_or_none(request_properties, parent_request_properties)

        if price_as_category:
            context["price_as_category"] = price_as_category
        if price_as_resource:
            context["price_as_resource"] = price_as_resource
        if resource_scope:
            context["resource_scope"] = resource_scope
        
    async def _acall_func(
        self,
        func: Any,
        proxy: Optional[bool],
        limit_ids: Optional["list[str]"],
        use_case_name: Optional[str],
        use_case_id: Optional[str],
        use_case_version: Optional[int],        
        user_id: Optional[str],
        account_name: Optional[str],
        request_properties: Optional["dict[str, Optional[str]]"] = None,
        use_case_properties: Optional["dict[str, Optional[str]]"] = None,
        log_prompt_and_response: Optional[bool] = None,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        with self:
            self._init_current_context(
                proxy=proxy,
                limit_ids=limit_ids,
                use_case_name=use_case_name,
                use_case_id=use_case_id,
                use_case_version=use_case_version,
                user_id=user_id,
                account_name=account_name,
                request_properties=request_properties,
                use_case_properties=use_case_properties,
                log_prompt_and_response=log_prompt_and_response,
            )
            return await func(*args, **kwargs)

    def _call_func(
        self,
        func: Any,
        proxy: Optional[bool],
        limit_ids: Optional["list[str]"],
        use_case_name: Optional[str],
        use_case_id: Optional[str],
        use_case_version: Optional[int],        
        user_id: Optional[str],
        account_name: Optional[str],
        request_properties: Optional["dict[str, Optional[str]]"] = None,
        use_case_properties: Optional["dict[str, Optional[str]]"] = None,
        log_prompt_and_response: Optional[bool] = None,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        with self:
            self._init_current_context(
                proxy=proxy,
                limit_ids=limit_ids,
                use_case_name=use_case_name,
                use_case_id=use_case_id,
                use_case_version=use_case_version,
                user_id=user_id,
                account_name=account_name,
                request_properties=request_properties,
                use_case_properties=use_case_properties,
                log_prompt_and_response=log_prompt_and_response,)
            return func(*args, **kwargs)

    def __enter__(self) -> Any:
        # Push a new context dictionary onto the thread-local stack
        self._context_stack.append({})
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        # Pop the current context off the thread-local stack
        if self._context_stack:
            self._context_stack.pop()

    @property
    def _context(self) -> Optional[_Context]:
        # Return the current top of the stack
        return self._context_stack[-1] if self._context_stack else None

    @property
    def _context_safe(self) -> _Context:
        # Return the current top of the stack
        return self._context or {}

    def _extract_price_as(self, extra_headers: "dict[str, str]") -> PriceAs:
        context = self._context_safe

        return PriceAs(
            category=extra_headers.pop(PayiHeaderNames.price_as_category, None) or context.get("price_as_category", None),
            resource=extra_headers.pop(PayiHeaderNames.price_as_resource, None) or context.get("price_as_resource", None),
            resource_scope=extra_headers.pop(PayiHeaderNames.resource_scope, None) or context.get("resource_scope", None),
        )

    def _before_invoke_update_request(
        self,
        request: _ProviderRequest,
        ingest_extra_headers: "dict[str, str]", # do not conflict with potential kwargs["extra_headers"]
        args: Sequence[Any],
        kwargs: 'dict[str, Any]',
    ) -> None:

        # pop and ignore the request tags header since it is no longer processed
        ingest_extra_headers.pop(PayiHeaderNames.request_tags, None)

        limit_ids = ingest_extra_headers.pop(PayiHeaderNames.limit_ids, None)

        use_case_name = ingest_extra_headers.pop(PayiHeaderNames.use_case_name, None)
        use_case_id = ingest_extra_headers.pop(PayiHeaderNames.use_case_id, None)
        use_case_version = ingest_extra_headers.pop(PayiHeaderNames.use_case_version, None)
        use_case_step = ingest_extra_headers.pop(PayiHeaderNames.use_case_step, None)

        user_id = ingest_extra_headers.pop(PayiHeaderNames.user_id, None)
        account_name = ingest_extra_headers.pop(PayiHeaderNames.account_name, None)

        request_properties = ingest_extra_headers.pop(PayiHeaderNames.request_properties, "")
        use_case_properties = ingest_extra_headers.pop(PayiHeaderNames.use_case_properties, "")

        # the presence of the value indicates disabled logging
        logging_disable = ingest_extra_headers.pop(PayiHeaderNames.logging_disable, None)

        request._log_prompt_and_response = logging_disable is None and self._log_prompt_and_response

        if limit_ids:
            request._ingest["limit_ids"] = limit_ids.split(",")
        if use_case_name:
            request._ingest["use_case_name"] = use_case_name
        if use_case_id:
            request._ingest["use_case_id"] = use_case_id
        if use_case_version:
            request._ingest["use_case_version"] = int(use_case_version)
        if use_case_step:
            request._ingest["use_case_step"] = use_case_step
        if user_id:
            request._ingest["user_id"] = user_id
        if account_name:
            request._ingest["account_name"] = account_name
        if request_properties:
            request._ingest["properties"] = json.loads(request_properties)
        if use_case_properties:
            request._ingest["use_case_properties"] = json.loads(use_case_properties)

        if len(ingest_extra_headers) > 0:
            request._ingest["provider_request_headers"] = [PayICommonModelsAPIRouterHeaderInfoParam(name=k, value=v) for k, v in ingest_extra_headers.items()]

        provider_prompt: "dict[str, Any]" = {}
        for k, v in kwargs.items():
            if k == "messages":
                provider_prompt[k] = [m.model_dump() if hasattr(m, "model_dump") else m for m in v]
            elif k in ["extra_headers", "extra_query"]:
                pass
            else:
                try:
                    if hasattr(v, "to_dict"):
                        provider_prompt[k] = v.to_dict()
                    else:
                        json.dumps(v)
                        provider_prompt[k] = v
                except Exception as _e:
                    pass

        request.process_request_prompt(provider_prompt, args, kwargs)

        if request._log_prompt_and_response:
            request._ingest["provider_request_json"] = _compact_json(provider_prompt)

        request._ingest["event_timestamp"] = datetime.now(timezone.utc)

    async def async_invoke_wrapper(
        self,
        request: _ProviderRequest,
        is_streaming: _IsStreaming,
        wrapped: Any,
        instance: Any,
        args: Sequence[Any],
        kwargs: 'dict[str, Any]',
    ) -> Any:
        self._logger.debug(f"async_invoke_wrapper: instance {instance}, category {request._category}")

        context = self._context

        # Bedrock client does not have an async method

        if not context:   
            self._logger.debug(f"async_invoke_wrapper: no instrumentation context, exit early")

            # wrapped function invoked outside of decorator scope
            return await wrapped(*args, **kwargs)

        # after _udpate_headers, all metadata to add to ingest is in extra_headers, keyed by the xproxy-xxx header name
        extra_headers: Optional[dict[str, str]] = kwargs.get("extra_headers")
        extra_headers = (extra_headers or {}).copy()
        self._update_extra_headers(context, extra_headers)

        if context.get("proxy", self._proxy_default):
            if not request.supports_extra_headers:
                kwargs.pop("extra_headers", None)
            elif extra_headers:
                # Pass the copy to the wrapped function. Assumes anthropic and openai clients
                kwargs["extra_headers"] = extra_headers

            self._logger.debug(f"async_invoke_wrapper: sending proxy request")

            return await wrapped(*args, **kwargs)
        
        request._price_as = self._extract_price_as(extra_headers)
        if not request.supports_extra_headers and "extra_headers" in kwargs:
            kwargs.pop("extra_headers", None)

        current_frame = inspect.currentframe()
        # f_back excludes the current frame, strip() cleans up whitespace and newlines
        stack = [frame.strip() for frame in traceback.format_stack(current_frame.f_back)]  # type: ignore

        request._ingest['properties'] = { 'system.stack_trace': _compact_json(stack) }

        if request.process_request(instance, extra_headers, args, kwargs) is False:
            self._logger.debug(f"async_invoke_wrapper: calling wrapped instance")
            return await wrapped(*args, **kwargs)

        sw = Stopwatch()
        stream: bool = False
        
        if is_streaming == _IsStreaming.kwargs:
            stream = kwargs.get("stream", False)
        elif is_streaming == _IsStreaming.true:
            stream = True
        else:
            stream = False

        try:
            self._before_invoke_update_request(request, extra_headers, args, kwargs)
            self._logger.debug(f"async_invoke_wrapper: calling wrapped instance (stream={stream})")

            if "extra_headers" in kwargs:
                # replace the original extra_headers with the updated copy which has all of the Pay-i headers removed
                kwargs["extra_headers"] = extra_headers

            sw.start()
            response = await wrapped(*args, **kwargs)

        except Exception as e:  # pylint: disable=broad-except
            sw.stop()
            duration = sw.elapsed_ms_int()

            self._logger.debug(f"invoke_wrapper: calling wrapped instance exception {e}")

            if request.process_exception(e, kwargs):
                request._ingest["end_to_end_latency_ms"] = duration
                await self._aingest_units(request)

            raise e

        if stream:
            if request.streaming_type == _StreamingType.generator:
                return _GeneratorWrapper(
                    generator=response,
                    instance=instance,
                    instrumentor=self,
                    stopwatch=sw,
                    request=request,
                    )
            elif request.streaming_type == _StreamingType.stream_manager:
                return _StreamManagerWrapper(
                    stream_manager=response,
                    instance=instance,
                    instrumentor=self,
                    stopwatch=sw,
                    request=request,
                )
            else:
                return _StreamIteratorWrapper(
                    response=response,
                    instance=instance,
                    instrumentor=self,
                    stopwatch=sw,
                    request=request,
                )

        sw.stop()
        duration = sw.elapsed_ms_int()
        request._ingest["end_to_end_latency_ms"] = duration
        request._ingest["http_status_code"] = 200

        request.add_instrumented_response_headers(response)

        return_result: Any = request.process_synchronous_response(response=response, kwargs=kwargs)

        if return_result:
            self._logger.debug(f"async_invoke_wrapper: process sync response return")
            return return_result

        xproxy_result = await self._aingest_units(request)
        request.assign_xproxy_result(response, xproxy_result)

        self._logger.debug(f"async_invoke_wrapper: finished")
        return response

    def invoke_wrapper(
        self,
        request: _ProviderRequest,
        is_streaming: _IsStreaming,
        wrapped: Any,
        instance: Any,
        args: Sequence[Any],
        kwargs: 'dict[str, Any]',
    ) -> Any:
        self._logger.debug(f"invoke_wrapper: instance {instance}, category {request._category}")

        context = self._context

        if not context:
            if not request.supports_extra_headers:
                kwargs.pop("extra_headers", None)

            self._logger.debug(f"invoke_wrapper: no instrumentation context, exit early")

            # wrapped function invoked outside of decorator scope
            return wrapped(*args, **kwargs)

        # after _udpate_headers, all metadata to add to ingest is in extra_headers, keyed by the xproxy-xxx header name
        extra_headers: Optional[dict[str, str]] = kwargs.get("extra_headers")
        extra_headers = (extra_headers or {}).copy()
        self._update_extra_headers(context, extra_headers)

        if context.get("proxy", self._proxy_default):
            if not request.supports_extra_headers:
                kwargs.pop("extra_headers", None)
            elif extra_headers:
                # Pass the copy to the wrapped function. Assumes anthropic and openai clients
                kwargs["extra_headers"] = extra_headers

            self._logger.debug(f"invoke_wrapper: sending proxy request")

            return wrapped(*args, **kwargs)

        request._price_as = self._extract_price_as(extra_headers)
        if not request.supports_extra_headers and "extra_headers" in kwargs:
            kwargs.pop("extra_headers", None)
        
        current_frame = inspect.currentframe()
        # f_back excludes the current frame, strip() cleans up whitespace and newlines
        stack = [frame.strip() for frame in traceback.format_stack(current_frame.f_back)]  # type: ignore

        request._ingest['properties'] = { 'system.stack_trace': _compact_json(stack) }

        if request.process_request(instance, extra_headers, args, kwargs) is False:
            self._logger.debug(f"invoke_wrapper: calling wrapped instance")
            return wrapped(*args, **kwargs)

        sw = Stopwatch()
        stream: bool = False
        
        if is_streaming == _IsStreaming.kwargs:
            stream = kwargs.get("stream", False)
        elif is_streaming == _IsStreaming.true:
            stream = True
        else:
            stream = False

        try:
            self._before_invoke_update_request(request, extra_headers, args, kwargs)
            self._logger.debug(f"invoke_wrapper: calling wrapped instance (stream={stream})")

            if "extra_headers" in kwargs:
                # replace the original extra_headers with the updated copy which has all of the Pay-i headers removed
                kwargs["extra_headers"] = extra_headers

            sw.start()
            response = wrapped(*args, **kwargs)
            
        except Exception as e:  # pylint: disable=broad-except
            sw.stop()
            duration = sw.elapsed_ms_int()

            self._logger.debug(f"invoke_wrapper: calling wrapped instance exception {e}")

            if request.process_exception(e, kwargs):
                request._ingest["end_to_end_latency_ms"] = duration
                self._ingest_units(request)

            raise e

        if stream:
            if request.streaming_type == _StreamingType.generator:
                return _GeneratorWrapper(
                    generator=response,
                    instance=instance,
                    instrumentor=self,
                    stopwatch=sw,
                    request=request,
                )
            elif request.streaming_type == _StreamingType.stream_manager:
                return _StreamManagerWrapper(
                    stream_manager=response,
                    instance=instance,
                    instrumentor=self,
                    stopwatch=sw,
                    request=request,
                )
            else:
                # request.streaming_type == _StreamingType.iterator
                stream_result = _StreamIteratorWrapper(
                    response=response,
                    instance=instance,
                    instrumentor=self,
                    stopwatch=sw,
                    request=request,
                )

                if request.is_aws_client:
                    if "body" in response:
                        response["body"] = stream_result
                    else:
                        response["stream"] = stream_result
                    return response
                
                return stream_result

        sw.stop()
        duration = sw.elapsed_ms_int()
        request._ingest["end_to_end_latency_ms"] = duration
        request._ingest["http_status_code"] = 200

        request.add_instrumented_response_headers(response)

        return_result: Any = request.process_synchronous_response(response=response, kwargs=kwargs)

        if return_result:
            self._logger.debug(f"invoke_wrapper: process sync response return")
            return return_result

        xproxy_result = self._ingest_units(request)
        request.assign_xproxy_result(response, xproxy_result)

        self._logger.debug(f"invoke_wrapper: finished")
        return response

    def _create_extra_headers(
        self
    ) -> 'dict[str, str]':
        extra_headers: dict[str, str] = {}
        context = self._context
        if context:
            self._update_extra_headers(context, extra_headers)

        return extra_headers

    def set_xproxy_result(self, response: Optional[Union[XproxyResult, XproxyError]]) -> Optional[Union[XproxyResult, XproxyError]]:
        self._last_result = response
        return response

    def _update_extra_headers(
        self,
        context: _Context,
        extra_headers: "dict[str, str]",
    ) -> None:
        context_limit_ids: Optional[list[str]] = context.get("limit_ids")

        context_use_case_name: Optional[str] = context.get("use_case_name")
        context_use_case_id: Optional[str] = context.get("use_case_id")
        context_use_case_version: Optional[int] = context.get("use_case_version")
        context_use_case_step: Optional[str] = context.get("use_case_step")

        context_user_id: Optional[str] = context.get("user_id")
        context_account_name: Optional[str] = context.get("account_name")

        context_price_as_category: Optional[str] = context.get("price_as_category")
        context_price_as_resource: Optional[str] = context.get("price_as_resource")
        context_resource_scope: Optional[str] = context.get("resource_scope")

        context_request_properties: Optional[dict[str, Optional[str]]] = context.get("request_properties")
        context_use_case_properties: Optional[dict[str, Optional[str]]] = context.get("use_case_properties")

        context_log_prompt_and_response: Optional[bool] = context.get("log_prompt_and_response")

        if PayiHeaderNames.request_properties in extra_headers:
            headers_request_properties = extra_headers.get(PayiHeaderNames.request_properties, None)

            if not headers_request_properties:
                # headers_request_properties is empty, remove it from extra_headers
                extra_headers.pop(PayiHeaderNames.request_properties, None)
            else:
                # leave the value in extra_headers
                ...
        elif context_request_properties:
            extra_headers[PayiHeaderNames.request_properties] = _compact_json(context_request_properties)

        if PayiHeaderNames.use_case_properties in extra_headers:
            headers_use_case_properties = extra_headers.get(PayiHeaderNames.use_case_properties, None)

            if not headers_use_case_properties:
                # headers_use_case_properties is empty, remove it from extra_headers
                extra_headers.pop(PayiHeaderNames.use_case_properties, None)
            else:
                # leave the value in extra_headers
                ...
        elif context_use_case_properties:
            extra_headers[PayiHeaderNames.use_case_properties] = _compact_json(context_use_case_properties)

        # If the caller specifies limit_ids in extra_headers, it takes precedence over the decorator
        if PayiHeaderNames.limit_ids in extra_headers:
            headers_limit_ids = extra_headers.get(PayiHeaderNames.limit_ids)

            if not headers_limit_ids:
                # headers_limit_ids is empty, remove it from extra_headers
                extra_headers.pop(PayiHeaderNames.limit_ids, None)
            else:   
                # leave the value in extra_headers
                ...
        elif context_limit_ids:
            extra_headers[PayiHeaderNames.limit_ids] = ",".join(context_limit_ids)

        if PayiHeaderNames.user_id in extra_headers:
            headers_user_id = extra_headers.get(PayiHeaderNames.user_id, None)
            if not headers_user_id:
                # headers_user_id is empty, remove it from extra_headers
                extra_headers.pop(PayiHeaderNames.user_id, None)
            else:
                # leave the value in extra_headers
                ...
        elif context_user_id:
            extra_headers[PayiHeaderNames.user_id] = context_user_id

        if PayiHeaderNames.account_name in extra_headers:
            headers_account_name = extra_headers.get(PayiHeaderNames.account_name, None)
            if not headers_account_name:
                # headers_account_name is empty, remove it from extra_headers
                extra_headers.pop(PayiHeaderNames.account_name, None)
            else:
                # leave the value in extra_headers
                ...
        elif context_account_name:
            extra_headers[PayiHeaderNames.account_name] = context_account_name

        if PayiHeaderNames.use_case_name in extra_headers:
            headers_use_case_name = extra_headers.get(PayiHeaderNames.use_case_name, None)
            if not headers_use_case_name:
                # headers_use_case_name is empty, remove all use case related headers
                extra_headers.pop(PayiHeaderNames.use_case_name, None)
                extra_headers.pop(PayiHeaderNames.use_case_id, None)
                extra_headers.pop(PayiHeaderNames.use_case_version, None)
                extra_headers.pop(PayiHeaderNames.use_case_step, None)
            else:
                # leave the value in extra_headers
                ...
        elif context_use_case_name:
            extra_headers[PayiHeaderNames.use_case_name] = context_use_case_name
            if context_use_case_id is not None:
                extra_headers[PayiHeaderNames.use_case_id] = context_use_case_id
            if context_use_case_version is not None:
                extra_headers[PayiHeaderNames.use_case_version] = str(context_use_case_version)
            if context_use_case_step is not None:
                extra_headers[PayiHeaderNames.use_case_step] = context_use_case_step

        if PayiHeaderNames.price_as_category not in extra_headers and context_price_as_category:
            extra_headers[PayiHeaderNames.price_as_category] = context_price_as_category

        if PayiHeaderNames.price_as_resource not in extra_headers and context_price_as_resource:
            extra_headers[PayiHeaderNames.price_as_resource] = context_price_as_resource

        if PayiHeaderNames.resource_scope not in extra_headers and context_resource_scope:
            extra_headers[PayiHeaderNames.resource_scope] = context_resource_scope

        if PayiHeaderNames.logging_disable not in extra_headers and context_log_prompt_and_response is not None and context_log_prompt_and_response is False:
            extra_headers[PayiHeaderNames.logging_disable] = "True"

    @staticmethod
    def payi_wrapper(func: Any) -> Any:
        def _payi_wrapper(o: Any) -> Any:
            def wrapper(wrapped: Any, instance: Any, args: Any, kwargs: Any) -> Any:
                return func(
                    o,
                    wrapped,
                    instance,
                    *args,
                    **kwargs,
                )

            return wrapper

        return _payi_wrapper

    @staticmethod
    def payi_awrapper(func: Any) -> Any:
        def _payi_awrapper(o: Any) -> Any:
            async def wrapper(wrapped: Any, instance: Any, args: Any, kwargs: Any) -> Any:
                return await func(
                    o,
                    wrapped,
                    instance,
                    *args,
                    **kwargs,
                )

            return wrapper

        return _payi_awrapper

global _instrumentor
_instrumentor: Optional[_PayiInstrumentor] = None

def payi_instrument(
    *,
    payi: Optional[Union[Payi, AsyncPayi, 'list[Union[Payi, AsyncPayi]]']] = None,
    instruments: Optional[Set[str]] = None,
    log_prompt_and_response: bool = True,
    config: Optional[PayiInstrumentConfig] = None,
    logger: Optional[logging.Logger] = None,
) -> None:
    global _instrumentor

    logger = logger or _g_logger

    frameinfo = inspect.stack()[1]
    caller_filename = os.path.basename(frameinfo.filename).replace(' ', '_').lower()
    if caller_filename.endswith('.py'):
        caller_filename = caller_filename[:-3]

    if (_instrumentor):
        logger.debug(f"payi_instrument() previously called, (current caller {caller_filename}.py)")
        return
    
    payi_param: Optional[Payi] = None
    apayi_param: Optional[AsyncPayi] = None

    if isinstance(payi, Payi):
        payi_param = payi
    elif isinstance(payi, AsyncPayi):
        apayi_param = payi
    elif isinstance(payi, list):
        for p in payi:
            if isinstance(p, Payi):
                payi_param = p
            elif isinstance(p, AsyncPayi): # type: ignore
                apayi_param = p

    # allow for both payi and apayi to be None for the @proxy case
    _instrumentor = _PayiInstrumentor(
        payi=payi_param,
        apayi=apayi_param,
        instruments=instruments,
        log_prompt_and_response=log_prompt_and_response,
        logger=logger,
        global_config=config if config else PayiInstrumentConfig(),
        caller_filename=caller_filename
    )

def track(
    *,
    limit_ids: Optional["list[str]"] = None,
    use_case_name: Optional[str] = None,
    use_case_id: Optional[str] = None,
    use_case_version: Optional[int] = None,
    user_id: Optional[str] = None,
    account_name: Optional[str] = None,
    request_tags: Optional["list[str]"] = None,
    request_properties: Optional["dict[str, str]"] = None,
    use_case_properties: Optional["dict[str, str]"] = None,
    log_prompt_and_response: Optional[bool] = None,
    proxy: Optional[bool] = None,
) -> Any:
    _ = request_tags

    def _track(func: Any) -> Any:
        if asyncio.iscoroutinefunction(func):
            async def awrapper(*args: Any, **kwargs: Any) -> Any:
                if not _instrumentor:
                    _g_logger.debug(f"track: no instrumentor!")
                    return await func(*args, **kwargs)

                _instrumentor._logger.debug(f"track: call async function (proxy={proxy}, limit_ids={limit_ids}, use_case_name={use_case_name}, use_case_id={use_case_id}, use_case_version={use_case_version}, user_id={user_id})")
                # Call the instrumentor's _call_func for async functions
                return await _instrumentor._acall_func(
                    func,
                    proxy,
                    limit_ids,
                    use_case_name,
                    use_case_id,
                    use_case_version,
                    user_id,
                    account_name,
                    cast(Optional['dict[str, Optional[str]]'], request_properties),
                    cast(Optional['dict[str, Optional[str]]'], use_case_properties),
                    log_prompt_and_response,
                    *args,
                    **kwargs,
                )
            return awrapper
        else:
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                if not _instrumentor:
                    _g_logger.debug(f"track: no instrumentor!")
                    return func(*args, **kwargs)

                _instrumentor._logger.debug(f"track: call sync function (proxy={proxy}, limit_ids={limit_ids}, use_case_name={use_case_name}, use_case_id={use_case_id}, use_case_version={use_case_version}, user_id={user_id}, account_name={account_name})")

                return _instrumentor._call_func(
                    func,
                    proxy,
                    limit_ids,
                    use_case_name,
                    use_case_id,
                    use_case_version,
                    user_id,
                    account_name,
                    cast(Optional['dict[str, Optional[str]]'], request_properties),
                    cast(Optional['dict[str, Optional[str]]'], use_case_properties),
                    log_prompt_and_response,
                    *args,
                    **kwargs,
                )
            return wrapper
    return _track

def track_context(
    *,
    limit_ids: Optional["list[str]"] = None,
    use_case_name: Optional[str] = None,
    use_case_id: Optional[str] = None,
    use_case_version: Optional[int] = None,
    use_case_step: Optional[str] = None,
    user_id: Optional[str] = None,
    account_name: Optional[str] = None,
    request_tags: Optional["list[str]"] = None,
    request_properties: Optional["dict[str, str]"] = None,
    use_case_properties: Optional["dict[str, str]"] = None,
    price_as_category: Optional[str] = None,
    price_as_resource: Optional[str] = None,
    resource_scope: Optional[str] = None,
    proxy: Optional[bool] = None,
    log_prompt_and_response: Optional[bool] = None,
) -> _InternalTrackContext:
    # Create a new context for tracking
    context: _Context = {}

    context["proxy"] = proxy
    context["log_prompt_and_response"] = log_prompt_and_response

    context["limit_ids"] = limit_ids

    context["use_case_name"] = use_case_name
    context["use_case_id"] = use_case_id
    context["use_case_version"] = use_case_version
    context["use_case_step"] = use_case_step

    context["user_id"] = user_id
    context["account_name"] = account_name

    context["price_as_category"] = price_as_category
    context["price_as_resource"] = price_as_resource
    context["resource_scope"] = resource_scope

    context["request_properties"] = cast(Optional['dict[str, Optional[str]]'], request_properties)
    context["use_case_properties"] = cast(Optional['dict[str, Optional[str]]'], use_case_properties)

    _ = request_tags

    return _InternalTrackContext(context)

def get_context() -> PayiContext:
    """
    Returns the current tracking context from calls to @track and with track_context().
    If no context is active, returns an empty context.
    """
    if not _instrumentor:
        return PayiContext()
    internal_context = _instrumentor._context_safe

    context_dict = {
        key: value
        for key, value in internal_context.items()
        if key in PayiContext.__annotations__ and value is not None
    }
    if _instrumentor._last_result:
        context_dict["last_result"] = _instrumentor._last_result
    return PayiContext(**dict(context_dict))  # type: ignore