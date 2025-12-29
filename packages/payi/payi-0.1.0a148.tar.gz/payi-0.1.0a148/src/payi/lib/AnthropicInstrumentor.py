from __future__ import annotations

import json
from typing import Any, Dict, Union, Optional, Sequence
from typing_extensions import override

import tiktoken
from wrapt import wrap_function_wrapper  # type: ignore

from payi.lib.helpers import PayiCategories
from payi.types.ingest_units_params import Units

from .instrument import PayiInstrumentAnthropicConfig, _Context, _IsStreaming, _PayiInstrumentor
from .version_helper import get_version_helper
from .ProviderRequest import _ChunkResult, _StreamingType, _ProviderRequest


class AnthropicInstrumentor:
    _module_name: str = "anthropic"
    _module_version: str = ""

    _azure_deployments: Dict[str, _Context] = {}
    _azure_foundry_clients_supported: bool = True

    @staticmethod
    def is_vertex(instance: Any) -> bool:
        from anthropic import AnthropicVertex, AsyncAnthropicVertex  # type: ignore # noqa: I001

        return isinstance(instance._client, (AsyncAnthropicVertex, AnthropicVertex))

    @staticmethod
    def is_bedrock(instance: Any) -> bool:
        from anthropic import AnthropicBedrock, AsyncAnthropicBedrock  # type: ignore # noqa: I001

        return isinstance(instance._client, (AsyncAnthropicBedrock, AnthropicBedrock))

    @staticmethod
    def is_azure(instance: Any) -> bool:
        if not AnthropicInstrumentor._azure_foundry_clients_supported:
            return False

        try:
            from anthropic import AnthropicFoundry, AsyncAnthropicFoundry  # type: ignore # noqa: I001
            return isinstance(instance._client, (AsyncAnthropicFoundry, AnthropicFoundry))
        except Exception:
            AnthropicInstrumentor._azure_foundry_clients_supported = False
            return False

    @staticmethod
    def configure(anthropic_config: PayiInstrumentAnthropicConfig) -> None:
        azure_config = anthropic_config.get("azure", {})
        if azure_config:
            model_mappings = azure_config.get("model_mappings", [])
            AnthropicInstrumentor._azure_deployments = _PayiInstrumentor._model_mapping_to_context_dict(model_mappings)

    @staticmethod
    def instrument(instrumentor: _PayiInstrumentor) -> None:
        AnthropicInstrumentor._module_version = get_version_helper(AnthropicInstrumentor._module_name)

        wrappers = [
            ("anthropic._base_client", "AsyncAPIClient._process_response", _ProviderRequest.aprocess_response_wrapper),
            ("anthropic._base_client", "SyncAPIClient._process_response", _ProviderRequest.process_response_wrapper),
            ("anthropic.resources.messages", "Messages.create", messages_wrapper(instrumentor)),
            ("anthropic.resources.messages", "Messages.stream", stream_messages_wrapper(instrumentor)),
            ("anthropic.resources.beta.messages", "Messages.create", messages_wrapper(instrumentor)),
            ("anthropic.resources.beta.messages", "Messages.stream", stream_messages_wrapper(instrumentor)),
            ("anthropic.resources.messages", "AsyncMessages.create", amessages_wrapper(instrumentor)),
            ("anthropic.resources.messages", "AsyncMessages.stream", astream_messages_wrapper(instrumentor)),
            ("anthropic.resources.beta.messages", "AsyncMessages.create", amessages_wrapper(instrumentor)),
            ("anthropic.resources.beta.messages", "AsyncMessages.stream", astream_messages_wrapper(instrumentor)),
        ]

        for module, method, wrapper in wrappers:
            try:
                wrap_function_wrapper(module, method, wrapper)
            except Exception as e:
                instrumentor._logger.debug(f"Failed to wrap {module}.{method}: {e}")

@_PayiInstrumentor.payi_wrapper
def messages_wrapper(
    instrumentor: _PayiInstrumentor,
    wrapped: Any,
    instance: Any,
    *args: Any,
    **kwargs: Any,
) -> Any:
    instrumentor._logger.debug("Anthropic messages wrapper")
    return instrumentor.invoke_wrapper(
        _AnthropicProviderRequest(instrumentor=instrumentor, streaming_type=_StreamingType.iterator, instance=instance),
        _IsStreaming.kwargs,
        wrapped,
        instance,
        args,
        kwargs,
    )

@_PayiInstrumentor.payi_wrapper
def stream_messages_wrapper(
    instrumentor: _PayiInstrumentor,
    wrapped: Any,
    instance: Any,
    *args: Any,
    **kwargs: Any,
) -> Any:
    instrumentor._logger.debug("Anthropic stream wrapper")
    return instrumentor.invoke_wrapper(
        _AnthropicProviderRequest(instrumentor=instrumentor, streaming_type=_StreamingType.stream_manager, instance=instance),
        _IsStreaming.true,
        wrapped,
        instance,
        args,
        kwargs,
    )

@_PayiInstrumentor.payi_awrapper
async def amessages_wrapper(
    instrumentor: _PayiInstrumentor,
    wrapped: Any,
    instance: Any,
    *args: Any,
    **kwargs: Any,
) -> Any:
    instrumentor._logger.debug("aync Anthropic messages wrapper")
    return await instrumentor.async_invoke_wrapper(
        _AnthropicProviderRequest(instrumentor=instrumentor, streaming_type=_StreamingType.iterator, instance=instance),
        _IsStreaming.kwargs,
        wrapped,
        instance,
        args,
        kwargs,
    )

@_PayiInstrumentor.payi_awrapper
async def astream_messages_wrapper(
    instrumentor: _PayiInstrumentor,
    wrapped: Any,
    instance: Any,
    *args: Any,
    **kwargs: Any,
) -> Any:
    instrumentor._logger.debug("aync Anthropic stream wrapper")
    return await instrumentor.async_invoke_wrapper(
        _AnthropicProviderRequest(instrumentor=instrumentor, streaming_type=_StreamingType.stream_manager, instance=instance),
        _IsStreaming.true,
        wrapped,
        instance,
        args,
        kwargs,
    )

class _AnthropicProviderRequest(_ProviderRequest):
    def __init__(self, instrumentor: _PayiInstrumentor, streaming_type: _StreamingType, instance: Any = None) -> None:
        self._is_vertex: bool = AnthropicInstrumentor.is_vertex(instance)
        self._is_bedrock: bool = AnthropicInstrumentor.is_bedrock(instance)
        self._is_azure: bool = AnthropicInstrumentor.is_azure(instance)
    
        category: str = ""
        if self._is_vertex:
            category = PayiCategories.google_vertex
        elif self._is_bedrock:
            category = PayiCategories.aws_bedrock
        elif self._is_azure:
            category = PayiCategories.azure
        else:
            category = PayiCategories.anthropic

        instrumentor._logger.debug(f"Anthropic messages instrumenting category {category}")

        super().__init__(
            instrumentor=instrumentor,
            category=category,
            streaming_type=streaming_type,
            module_name=AnthropicInstrumentor._module_name,
            module_version=AnthropicInstrumentor._module_version,
            )

    @override
    def process_chunk(self, chunk: Any) -> _ChunkResult:
        return anthropic_process_chunk(self, chunk.to_dict(), assign_id=True)

    @override
    def process_synchronous_response(self, response: Any, kwargs: Any) -> Any:
        anthropic_process_synchronous_response(
            request=self,
            response=response.to_dict(),
            log_prompt_and_response=self._log_prompt_and_response,
            assign_id=True)

        return None

    def _update_resource_name(self, model: str) -> str:
        return ("anthropic." if self._is_vertex else "") + model

    @override
    def process_request(self, instance: Any, extra_headers: 'dict[str, str]',  args: Sequence[Any], kwargs: Any) -> bool:
        model = self._update_resource_name(kwargs.get("model", ""))
        self._ingest["resource"] = model

        if not self._price_as.resource and not self._price_as.category and AnthropicInstrumentor._azure_deployments:
            deployment = AnthropicInstrumentor._azure_deployments.get(model, {})
            self._price_as.category = deployment.get("price_as_category", None)
            self._price_as.resource = deployment.get("price_as_resource", None)
            self._price_as.resource_scope = deployment.get("resource_scope", None)

        if self._is_azure and not self._price_as.resource and not self._price_as.category:
            self._instrumentor._logger.debug(f"Azure Anthropic model {model}, available mappings: {list(AnthropicInstrumentor._azure_deployments.keys())}")
            self._instrumentor._logger.warning("Azure Anthropic requires price as resource and/or category to be specified unless mapped in the Pay-i service")

        if self._price_as.resource_scope:
            self._ingest["resource_scope"] = self._price_as.resource_scope
        
        # override defaults
        if self._price_as.category:
            self._ingest["category"] = self._price_as.category
        if self._price_as.resource:
            self._ingest["resource"] = self._update_resource_name(self._price_as.resource)

        self._instrumentor._logger.debug(f"Processing anthropic request: model {self._ingest['resource']}, category {self._category}")

        messages = kwargs.get("messages")
        if messages:
            anthropic_has_image_and_get_texts(self, messages)

        # provider uri is only interesting for hosted providers
        if (self._is_azure or self._is_vertex or self._is_bedrock) and hasattr(instance._client, "_base_url"):
           self._ingest["provider_uri"] = str(instance._client._base_url)

        return True

    @override
    def remove_inline_data(self, prompt: 'dict[str, Any]') -> bool:
        return anthropic_remove_inline_data(prompt)

    @override
    def process_exception(self, exception: Exception, kwargs: Any, ) -> bool:
        try:
            status_code: Optional[int] = None

            if hasattr(exception, "status_code"):
                status_code = getattr(exception, "status_code", None)
                if isinstance(status_code, int):
                    self._ingest["http_status_code"] = status_code

            if not status_code:
                self.exception_to_semantic_failure(exception,)
                return True

            if hasattr(exception, "request_id"):
                request_id = getattr(exception, "request_id", None)
                if isinstance(request_id, str):
                    self._ingest["provider_response_id"] = request_id

            if hasattr(exception, "response"):
                response = getattr(exception, "response", None)
                if hasattr(response, "text"):
                    text = getattr(response, "text", None)
                    if isinstance(text, str):
                        self._ingest["provider_response_json"] = text

        except Exception as e:
            self._instrumentor._logger.debug(f"Error processing exception: {e}")
            return False

        return True

def anthropic_process_compute_input_cost(request: _ProviderRequest, usage: 'dict[str, Any]') -> int:
    input = usage.get('input_tokens', 0)
    units: dict[str, Units] = request._ingest["units"]

    cache_creation_input_tokens = usage.get("cache_creation_input_tokens", 0)
    cache_read_input_tokens = usage.get("cache_read_input_tokens", 0)

    total_input_tokens = input + cache_creation_input_tokens + cache_read_input_tokens

    request._is_large_context = total_input_tokens >= 200000
    large_context = "_large_context" if request._is_large_context else ""

    cache_creation: dict[str, int] = usage.get("cache_creation", {})
    ephemeral_5m_input_tokens: Optional[int] = None
    ephemeral_1h_input_tokens: Optional[int] = None
    textCacheWriteAdded = False

    if cache_creation:
        ephemeral_5m_input_tokens = cache_creation.get("ephemeral_5m_input_tokens", 0)
        if ephemeral_5m_input_tokens > 0:
            textCacheWriteAdded = True
            units["text_cache_write"+large_context] = Units(input=ephemeral_5m_input_tokens, output=0)

        ephemeral_1h_input_tokens = cache_creation.get("ephemeral_1h_input_tokens", 0)
        if ephemeral_1h_input_tokens > 0:
            textCacheWriteAdded = True
            units["text_cache_write_1h"+large_context] = Units(input=ephemeral_1h_input_tokens, output=0)

    if textCacheWriteAdded is False and cache_creation_input_tokens > 0:
        units["text_cache_write"+large_context] = Units(input=cache_creation_input_tokens, output=0)

    cache_read_input_tokens = usage.get("cache_read_input_tokens", 0)
    if cache_read_input_tokens > 0:
        units["text_cache_read"+large_context] = Units(input=cache_read_input_tokens, output=0)

    return request.update_for_vision(input)

def anthropic_process_synchronous_response(request: _ProviderRequest, response: 'dict[str, Any]', log_prompt_and_response: bool, assign_id: bool) -> Any:
    usage = response.get('usage', {})
    units: dict[str, Units] = request._ingest["units"]

    input_tokens = anthropic_process_compute_input_cost(request, usage)
    output = usage.get('output_tokens', 0)

    large_context = "_large_context" if request._is_large_context else ""
    units["text"+large_context] = Units(input=input_tokens, output=output)

    content = response.get('content', [])
    if content:
        for c in content:
            if c.get("type", "") != "tool_use":
                continue
            name = c.get("name", "")
            input = c.get("input", "")
            arguments: Optional[str] = None
            if input and isinstance(input, dict):
                arguments = json.dumps(input, ensure_ascii=False)
            
            if name and arguments:
                request.add_synchronous_function_call(name=name, arguments=arguments)

    if log_prompt_and_response:
        request._ingest["provider_response_json"] = json.dumps(response)
    
    if assign_id:
        request._ingest["provider_response_id"] = response.get('id', None)
    
    return None

def anthropic_process_chunk(request: _ProviderRequest, chunk: 'dict[str, Any]', assign_id: bool) -> _ChunkResult:    
    ingest = False
    type = chunk.get('type', "")

    if type == "message_start":
        message = chunk['message']

        if assign_id:
            request._ingest["provider_response_id"] = message.get('id', None)

        model = message.get('model', None)
        if model and 'resource' in request._ingest:
            request._instrumentor._logger.debug(f"Anthropic streaming, reported model: {model}, instrumented model {request._ingest['resource']}")

        usage = message.get('usage', {})
        units = request._ingest["units"]

        input = anthropic_process_compute_input_cost(request, usage)

        large_context = "_large_context" if request._is_large_context else ""
        units["text"+large_context] = Units(input=input, output=0)

        request._instrumentor._logger.debug(f"Anthropic streaming captured {input} input tokens, ")

    elif type == "message_delta":
        usage = chunk.get('usage', {})
        ingest = True
        large_context = "_large_context" if request._is_large_context else ""

        # Web search will return an updated input tokens value at the end of streaming
        input_tokens = usage.get('input_tokens', None)
        if input_tokens is not None:
            request._instrumentor._logger.debug(f"Anthropic streaming finished, updated input tokens: {input_tokens}")
            request._ingest["units"]["text"+large_context]["input"] = input_tokens

        request._ingest["units"]["text"+large_context]["output"] = usage.get('output_tokens', 0)

        request._instrumentor._logger.debug(f"Anthropic streaming finished: output tokens {usage.get('output_tokens', 0)} ")

    elif type == "content_block_start":
        request._building_function_response = False

        content_block = chunk.get('content_block', {})
        if content_block and content_block.get('type', "") == "tool_use":
            index = chunk.get('index', None)
            name = content_block.get('name', "")

            if index and isinstance(index, int) and name:
                request._building_function_response = True
                request.add_streaming_function_call(index=index, name=name, arguments=None)

    elif type == "content_block_delta":
        if request._building_function_response:
            delta = chunk.get("delta", {})
            type = delta.get("type", "")
            partial_json = delta.get("partial_json", "")
            index = chunk.get('index', None)

            if index and isinstance(index, int) and type == "input_json_delta" and partial_json:
                request.add_streaming_function_call(index=index, name=None, arguments=partial_json)

    elif type == "content_block_stop":
        request._building_function_response = False

    else:
        request._instrumentor._logger.debug(f"Anthropic streaming chunk: {type}")
        
    return _ChunkResult(send_chunk_to_caller=True, ingest=ingest)

def anthropic_has_image_and_get_texts(request: _ProviderRequest, messages: Any) -> None:
    estimated_token_count = 0 
    has_image = False

    try:
        enc = tiktoken.get_encoding("cl100k_base")
        for message in messages:
            msg_has_image, msg_prompt_tokens = has_image_and_get_texts(enc, message.get('content', ''))
            if msg_has_image:
                has_image = True
                estimated_token_count += msg_prompt_tokens
        
        if has_image and estimated_token_count > 0:
            request._estimated_prompt_tokens = estimated_token_count

    except Exception:
        request._instrumentor._logger.info("Anthropic skipping vision token calc, could not load cl100k_base")

def has_image_and_get_texts(encoding: tiktoken.Encoding, content: Union[str, 'list[Any]']) -> 'tuple[bool, int]':
    if isinstance(content, list): # type: ignore
        has_image = any(item.get("type") == "image" for item in content)
        if has_image is False:
            return has_image, 0
        
        token_count = sum(len(encoding.encode(item.get("text", ""))) for item in content if item.get("type") == "text")
        return has_image, token_count
    
    return False, 0

def anthropic_remove_inline_data(prompt: 'dict[str, Any]') -> bool:# noqa: ARG002
    messages = prompt.get("messages", [])
    if not messages:
        return False

    modified = False
    for message in messages:
        content = message.get('content', Any)
        if not content or not isinstance(content, list):
            continue

        for item in content: # type: ignore
            if not isinstance(item, dict):
                continue
            # item: dict[str, Any]
            type = item.get("type", "") # type: ignore
            if type != "image":
                continue

            source = item.get("source", {}) # type: ignore
            if source.get("type", "") == "base64": # type: ignore
                source["data"] = _PayiInstrumentor._not_instrumented
                modified = True

    return modified
