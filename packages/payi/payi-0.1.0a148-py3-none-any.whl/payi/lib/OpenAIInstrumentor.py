from __future__ import annotations

import json
from typing import Any, Dict, Union, Optional, Sequence
from typing_extensions import override
from importlib.metadata import version

import tiktoken  # type: ignore
from wrapt import wrap_function_wrapper  # type: ignore

from payi.lib.helpers import PayiCategories
from payi.types.ingest_units_params import Units

from .instrument import (
    PayiInstrumentOpenAiAzureConfig,
    _Context,
    _IsStreaming,
    _PayiInstrumentor,
)
from .version_helper import get_version_helper
from .ProviderRequest import _ChunkResult, _StreamingType, _ProviderRequest


class OpenAiInstrumentor:
    _module_name: str = "openai"
    _module_version: str = ""

    _azure_openai_deployments: Dict[str, _Context] = {}

    @staticmethod
    def is_azure(instance: Any) -> bool:
        from openai import AzureOpenAI, AsyncAzureOpenAI # type: ignore # noqa: I001

        return isinstance(instance._client, (AsyncAzureOpenAI, AzureOpenAI))

    @staticmethod
    def configure(azure_openai_config: Optional[PayiInstrumentOpenAiAzureConfig]) -> None:
        if azure_openai_config:
            model_mappings = azure_openai_config.get("model_mappings", [])
            OpenAiInstrumentor._azure_openai_deployments = _PayiInstrumentor._model_mapping_to_context_dict(model_mappings)

    @staticmethod
    def instrument(instrumentor: _PayiInstrumentor) -> None:
        OpenAiInstrumentor._module_version = get_version_helper(OpenAiInstrumentor._module_name)

        wrappers = [
            ("openai._base_client", "AsyncAPIClient._process_response", _ProviderRequest.aprocess_response_wrapper),
            ("openai._base_client", "SyncAPIClient._process_response", _ProviderRequest.process_response_wrapper),
            ("openai.resources.chat.completions", "Completions.create", chat_wrapper(instrumentor)),
            ("openai.resources.chat.completions", "Completions.parse", chat_wrapper(instrumentor)),
            ("openai.resources.chat.completions", "AsyncCompletions.create", achat_wrapper(instrumentor)),
            ("openai.resources.chat.completions", "AsyncCompletions.parse", achat_wrapper(instrumentor)),
            ("openai.resources.embeddings", "Embeddings.create", embeddings_wrapper(instrumentor)),
            ("openai.resources.embeddings", "AsyncEmbeddings.create", aembeddings_wrapper(instrumentor)),
            ("openai.resources.responses", "Responses.create", responses_wrapper(instrumentor)),
            ("openai.resources.responses", "Responses.parse", responses_wrapper(instrumentor)),
            ("openai.resources.responses", "AsyncResponses.create", aresponses_wrapper(instrumentor)),
            ("openai.resources.responses", "AsyncResponses.parse", aresponses_wrapper(instrumentor)),

            # In post beta openai moddule releases wrapping these will fail and gracefully handled
            ("openai.resources.beta.chat.completions", "Completions.create", chat_wrapper(instrumentor)),
            ("openai.resources.beta.chat.completions", "Completions.parse", chat_wrapper(instrumentor)),
            ("openai.resources.beta.chat.completions", "AsyncCompletions.create", achat_wrapper(instrumentor)),
            ("openai.resources.beta.chat.completions", "AsyncCompletions.parse", achat_wrapper(instrumentor)),
        ]

        for module, method, wrapper in wrappers:
            try:
                wrap_function_wrapper(module, method, wrapper)
            except Exception as e:
                instrumentor._logger.debug(f"Failed to wrap {module}.{method}: {e}")

@_PayiInstrumentor.payi_wrapper
def embeddings_wrapper(
    instrumentor: _PayiInstrumentor,
    wrapped: Any,
    instance: Any,
    *args: Any,
    **kwargs: Any,
) -> Any:
    instrumentor._logger.debug("OpenAI Embeddings wrapper")
    return instrumentor.invoke_wrapper(
        _OpenAiEmbeddingsProviderRequest(instrumentor, instance),
        _IsStreaming.false,
        wrapped,
        instance,
        args,
        kwargs,
    )

@_PayiInstrumentor.payi_wrapper
async def aembeddings_wrapper(
    instrumentor: _PayiInstrumentor,
    wrapped: Any,
    instance: Any,
    *args: Any,
    **kwargs: Any,
) -> Any:
    instrumentor._logger.debug("async OpenAI Embeddings wrapper")
    return await instrumentor.async_invoke_wrapper(
        _OpenAiEmbeddingsProviderRequest(instrumentor, instance),
        _IsStreaming.false,
        wrapped,
        instance,
        args,
        kwargs,
    )

@_PayiInstrumentor.payi_wrapper
def chat_wrapper(
    instrumentor: _PayiInstrumentor,
    wrapped: Any,
    instance: Any,
    *args: Any,
    **kwargs: Any,
) -> Any:
    instrumentor._logger.debug("OpenAI completions wrapper")
    return instrumentor.invoke_wrapper(
        _OpenAiChatProviderRequest(instrumentor, instance),
        _IsStreaming.kwargs,
        wrapped,
        instance,
        args,
        kwargs,
    )

@_PayiInstrumentor.payi_awrapper
async def achat_wrapper(
    instrumentor: _PayiInstrumentor,
    wrapped: Any,
    instance: Any,
    *args: Any,
    **kwargs: Any,
) -> Any:
    instrumentor._logger.debug("async OpenAI completions wrapper")
    return await instrumentor.async_invoke_wrapper(
        _OpenAiChatProviderRequest(instrumentor, instance),
        _IsStreaming.kwargs,
        wrapped,
        instance,
        args,
        kwargs,
    )
    
@_PayiInstrumentor.payi_wrapper
def responses_wrapper(
    instrumentor: _PayiInstrumentor,
    wrapped: Any,
    instance: Any,
    *args: Any,
    **kwargs: Any,
) -> Any:
    instrumentor._logger.debug("OpenAI responses wrapper")
    return instrumentor.invoke_wrapper(
        _OpenAiResponsesProviderRequest(instrumentor, instance),
        _IsStreaming.kwargs,
        wrapped,
        instance,
        args,
        kwargs,
    )

@_PayiInstrumentor.payi_awrapper
async def aresponses_wrapper(
    instrumentor: _PayiInstrumentor,
    wrapped: Any,
    instance: Any,
    *args: Any,
    **kwargs: Any,
) -> Any:
    instrumentor._logger.debug("async OpenAI responses wrapper")
    return await instrumentor.async_invoke_wrapper(
        _OpenAiResponsesProviderRequest(instrumentor, instance),
        _IsStreaming.kwargs,
        wrapped,
        instance,
        args,
        kwargs,
    )

class _OpenAiProviderRequest(_ProviderRequest):
    chat_input_tokens_key: str = "prompt_tokens"
    chat_output_tokens_key: str = "completion_tokens"
    chat_input_tokens_details_key: str = "prompt_tokens_details"

    responses_input_tokens_key: str = "input_tokens"
    responses_output_tokens_key: str = "output_tokens"
    responses_input_tokens_details_key: str = "input_tokens_details"

    def __init__(self, instrumentor: _PayiInstrumentor, instance: Any, input_tokens_key: str, output_tokens_key: str, input_tokens_details_key: str) -> None:
        super().__init__(
            instrumentor=instrumentor,
            category=PayiCategories.openai,
            streaming_type=_StreamingType.iterator,
            module_name=OpenAiInstrumentor._module_name,
            module_version=OpenAiInstrumentor._module_version,
            )
        self._input_tokens_key = input_tokens_key
        self._output_tokens_key = output_tokens_key
        self._input_tokens_details_key = input_tokens_details_key
        self._is_azure = instance and hasattr(instance, "_client") and OpenAiInstrumentor.is_azure(instance)

    @override
    def process_request(self, instance: Any, extra_headers: 'dict[str, str]',  args: Sequence[Any], kwargs: Any) -> bool: # type: ignore
        model = kwargs.get("model", "")

        if self._is_azure:
            if hasattr(instance._client, "_base_url"):
               self._ingest["provider_uri"] = str(instance._client._base_url)

            self._category = PayiCategories.azure_openai

            # model is technically optional as it is part of the URL path
            if not model and hasattr(instance._client, "_azure_deployment"):
                model = instance._client._azure_deployment

            self.map_deployment(model)

        self.apply_price_as(model)

        return True

    def apply_price_as(self, model: str) -> None:
        if self._price_as.resource_scope:
            self._ingest["resource_scope"] = self._price_as.resource_scope

        if self._price_as.category:
            self._category = self._price_as.category

        self._ingest["category"] = self._category
        self._ingest["resource"] = self._price_as.resource if self._price_as.resource else model

    def map_deployment(self, model:Optional[str]) -> None:
        self._instrumentor._logger.debug(f"Azure OpenAI model {model}, available mappings: {list(OpenAiInstrumentor._azure_openai_deployments.keys())}, price as before final mapping: resource={self._price_as.resource}, category={self._price_as.category}, resource_scope={self._price_as.resource_scope}")

        if model and not self._price_as.resource and not self._price_as.category and model in OpenAiInstrumentor._azure_openai_deployments:
            deployment = OpenAiInstrumentor._azure_openai_deployments.get(model, {})
            self._price_as.category = deployment.get("price_as_category", None)
            self._price_as.resource = deployment.get("price_as_resource", None)
            self._price_as.resource_scope = deployment.get("resource_scope", None)

        if not self._price_as.resource and not self._price_as.category:
            self._instrumentor._logger.warning("Azure OpenAI requires price as resource and/or category to be specified unless mapped in the Pay-i service")

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

    def update_deployment_name(self) -> None:
        if self._ingest.get("resource", None):
            return

        deployment_name = self.find_response_header_value("x-ms-deployment-name")
        if deployment_name:
            self.map_deployment(deployment_name)
            self.apply_price_as(deployment_name)

    def process_synchronous_response_worker(
        self,
        response: str,
        ) -> Any:
        response_dict = model_to_dict(response)

        self.update_deployment_name()
        
        self.add_usage_units(response_dict.get("usage", {}))

        if self._log_prompt_and_response:
            self._ingest["provider_response_json"] = [json.dumps(response_dict)]

        if "id" in response_dict:
            self._ingest["provider_response_id"] = response_dict["id"]

        return None

    def add_usage_units(self, usage: "dict[str, Any]",) -> None:
        units = self._ingest["units"]

        input = usage[self._input_tokens_key] if self._input_tokens_key in usage else 0
        output = usage[self._output_tokens_key] if self._output_tokens_key in usage else 0
        input_cache = 0

        prompt_tokens_details = usage.get(self._input_tokens_details_key)
        if prompt_tokens_details:
            input_cache = prompt_tokens_details.get("cached_tokens", 0)
            if input_cache != 0:
                units["text_cache_read"] = Units(input=input_cache, output=0)

        input = self.update_for_vision(input - input_cache)

        units["text"] = Units(input=input, output=output)

    @staticmethod
    def has_image_and_get_texts(encoding: tiktoken.Encoding, content: Union[str, 'list[Any]'], image_type: str, text_type: str) -> 'tuple[bool, int]':
        if isinstance(content, list): # type: ignore
            has_image = any(item.get("type", "") == image_type for item in content)
            if has_image is False:
                return has_image, 0
            
            token_count = sum(len(encoding.encode(item.get("text", ""))) for item in content if item.get("type") == text_type)
            return has_image, token_count
        return False, 0

    @staticmethod
    def post_process_request_prompt(content: Union[str, 'list[Any]'], image_type: str, url_subkey: bool) -> bool:
        modified = False
        if isinstance(content, list): # type: ignore
            for item in content:
                type = item.get("type", "")
                if type != image_type:
                    continue

                if url_subkey:
                    url = item.get("image_url", {}).get("url", "")
                    if url.startswith("data:"):
                        item["image_url"]["url"] = _PayiInstrumentor._not_instrumented
                        modified = True
                else:
                    url = item.get("image_url", "")
                    if url.startswith("data:"):
                        item["image_url"] = _PayiInstrumentor._not_instrumented
                        modified = True

        return modified

class _OpenAiEmbeddingsProviderRequest(_OpenAiProviderRequest):
    def __init__(self, instrumentor: _PayiInstrumentor, instance: Any):
        super().__init__(
            instrumentor=instrumentor,
            instance=instance,
            input_tokens_key=_OpenAiProviderRequest.chat_input_tokens_key,
            output_tokens_key=_OpenAiProviderRequest.chat_output_tokens_key,
            input_tokens_details_key=_OpenAiProviderRequest.chat_input_tokens_details_key)

    @override
    def process_synchronous_response(
        self,
        response: Any,
        kwargs: Any) -> Any:
        return self.process_synchronous_response_worker(response)

class _OpenAiChatProviderRequest(_OpenAiProviderRequest):
    def __init__(self, instrumentor: _PayiInstrumentor, instance: Any):
        super().__init__(
            instrumentor=instrumentor,
            instance=instance,
            input_tokens_key=_OpenAiProviderRequest.chat_input_tokens_key,
            output_tokens_key=_OpenAiProviderRequest.chat_output_tokens_key,
            input_tokens_details_key=_OpenAiProviderRequest.chat_input_tokens_details_key)

        self._include_usage_added = False

    @override
    def process_chunk(self, chunk: Any) -> _ChunkResult:
        ingest = False
        model = model_to_dict(chunk)
        
        if "provider_response_id" not in self._ingest:
            response_id = model.get("id", None)
            if response_id:
                self._ingest["provider_response_id"] = response_id

        send_chunk_to_client = True

        choices = model.get("choices", [])
        if choices:
            for choice in choices:
                function = choice.get("delta", {}).get("function_call", {})
                index = choice.get("index", None)

                if function and index is not None:
                    name = function.get("name", None)
                    arguments = function.get("arguments", None)

                    if name or arguments:
                        self.add_streaming_function_call(index=index, name=name, arguments=arguments)

        usage = model.get("usage")
        if usage:
            self.update_deployment_name()
            self.add_usage_units(usage)

            # If we added "include_usage" in the request on behalf of the client, do not return the extra 
            # packet which contains the usage to the client as they are not expecting the data
            if self._include_usage_added:
                send_chunk_to_client = False
            ingest = True

        return _ChunkResult(send_chunk_to_caller=send_chunk_to_client, ingest=ingest)

    @override
    def process_request(self, instance: Any, extra_headers: 'dict[str, str]', args: Sequence[Any], kwargs: Any) -> bool:
        result = super().process_request(instance, extra_headers, args, kwargs)
        if result is False:
            return result
        
        messages = kwargs.get("messages", None)
        if messages:
            estimated_token_count = 0 
            has_image = False
            enc: Optional[tiktoken.Encoding] = None

            try: 
                enc = tiktoken.encoding_for_model(kwargs.get("model")) # type: ignore
            except Exception:
                try:
                    enc = tiktoken.get_encoding("o200k_base") # type: ignore
                except Exception:
                    self._instrumentor._logger.info("OpenAI skipping vision token calc, could not load o200k_base")
                    enc = None
            
            if enc:
                for message in messages:
                    msg_has_image, msg_prompt_tokens = self.has_image_and_get_texts(enc, message.get('content', ''), image_type="image_url", text_type="text")
                    if msg_has_image:
                        has_image = True
                        estimated_token_count += msg_prompt_tokens
            
                if has_image and estimated_token_count > 0:
                    self._estimated_prompt_tokens = estimated_token_count

            stream: bool = kwargs.get("stream", False)
            if stream:
                add_include_usage = True

                stream_options: dict[str, Any] = kwargs.get("stream_options", None)
                if stream_options and "include_usage" in stream_options:
                    add_include_usage = stream_options["include_usage"] == False

                if add_include_usage:
                    kwargs['stream_options'] = {"include_usage": True}
                    self._include_usage_added = True
        return True

    @override
    def remove_inline_data(self, prompt: 'dict[str, Any]') -> bool:
        messages = prompt.get("messages", None)
        if not messages:
            return False
        return self.post_process_request_prompt(messages, image_type="image_url", url_subkey=True)

    @override
    def process_synchronous_response(
        self,
        response: Any,
        kwargs: Any) -> Any:

        response_dict = model_to_dict(response)
        choices = response_dict.get("choices", [])
        if choices:
            for choice in choices:
                function = choice.get("message", {}).get("function_call", {})

                if not function:
                    continue

                name = function.get("name", None)
                arguments = function.get("arguments", None)

                if name:
                    self.add_synchronous_function_call(name=name, arguments=arguments)

        return self.process_synchronous_response_worker(response)

class _OpenAiResponsesProviderRequest(_OpenAiProviderRequest):
    def __init__(self, instrumentor: _PayiInstrumentor, instance: Any):
        super().__init__(
            instrumentor=instrumentor,
            instance=instance,
            input_tokens_key=_OpenAiProviderRequest.responses_input_tokens_key,
            output_tokens_key=_OpenAiProviderRequest.responses_output_tokens_key,
            input_tokens_details_key=_OpenAiProviderRequest.responses_input_tokens_details_key)

    @override
    def process_chunk(self, chunk: Any) -> _ChunkResult:
        ingest = False
        model = model_to_dict(chunk)
        response: dict[str, Any] = model.get("response", {})

        if "provider_response_id" not in self._ingest:
            response_id = response.get("id", None)
            if response_id:
                self._ingest["provider_response_id"] = response_id

        type = model.get("type", "")
        if type and type == "response.output_item.done":
            item = model.get("item", {})
            if item and item.get("type", "") == "function_call":
                name = item.get("name", None)
                arguments = item.get("arguments", None)

                if name:
                    self.add_synchronous_function_call(name=name, arguments=arguments)

        usage = response.get("usage")
        if usage:
            self.update_deployment_name()
            self.add_usage_units(usage)
            ingest = True

        return _ChunkResult(send_chunk_to_caller=True, ingest=ingest)

    @override
    def process_request(self, instance: Any, extra_headers: 'dict[str, str]', args: Sequence[Any], kwargs: Any) -> bool:
        result = super().process_request(instance, extra_headers, args, kwargs)
        if result is False:
            return result
        
        input: ResponseInputParam  = kwargs.get("input", None) # type: ignore
        if not input or isinstance(input, str) or not isinstance(input, list):
            return True
        
        estimated_token_count = 0 
        has_image = False
        enc: Optional[tiktoken.Encoding] = None

        try: 
            enc = tiktoken.encoding_for_model(kwargs.get("model")) # type: ignore
        except Exception:
            try:
                enc = tiktoken.get_encoding("o200k_base") # type: ignore
            except Exception:
                self._instrumentor._logger.info("OpenAI skipping vision token calc, could not load o200k_base")
                enc = None
        
        # find each content..type="input_text" and count tokens
        # input=[{
        #     "role": "user",
        #     "content": [
        #         {
        #             "type": "input_text",
        #             "text": "what's in this image?"
        #         },
        #         {
        #             "type": "input_image",
        #             "image_url": ... 
        #         },
        #     ],
        # }]
        if enc:
            for item in input: # type: ignore
                if isinstance(item, dict):
                    for key, value in item.items(): # type: ignore
                        if key == "content":
                            if isinstance(value, list):
                                msg_has_image, msg_prompt_tokens = self.has_image_and_get_texts(enc, value, image_type="input_image", text_type="input_text") # type: ignore 
                                if msg_has_image:
                                    has_image = True
                                    estimated_token_count += msg_prompt_tokens

            if has_image and estimated_token_count > 0:
                self._estimated_prompt_tokens = estimated_token_count

        return True

    @override
    def remove_inline_data(self, prompt: 'dict[str, Any]') -> bool:
        modified = False
        input = prompt.get("input", [])
        for item in input:
            if not isinstance(item, dict):
                continue

            for key, value in item.items(): # type: ignore
                if key == "content":
                    if isinstance(value, list):
                        modified = self.post_process_request_prompt(value, image_type="input_image", url_subkey=False) | modified # type: ignore

        return modified

    @override
    def process_synchronous_response(
        self,
        response: Any,
        kwargs: Any) -> Any:

        response_dict = model_to_dict(response)
        output = response_dict.get("output", [])
        if output:
            for o in output:
                type = o.get("type", "")
                if type != "function_call":
                    continue

                name = o.get("name", None)
                arguments = o.get("arguments", None)

                if name:
                    self.add_synchronous_function_call(name=name, arguments=arguments)

        return self.process_synchronous_response_worker(response)

def model_to_dict(model: Any) -> Any:
    if version("pydantic") < "2.0.0":
        return model.dict()
    if hasattr(model, "model_dump"):
        return model.model_dump()
    elif hasattr(model, "parse"):  # Raw API response
        return model_to_dict(model.parse())
    else:
        return model