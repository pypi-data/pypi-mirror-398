from __future__ import annotations

import os
import json
from typing import TYPE_CHECKING, Any, Dict, Optional, Sequence
from functools import wraps
from typing_extensions import override

from wrapt import ObjectProxy, wrap_function_wrapper  # type: ignore

from payi.lib.helpers import PayiCategories, PayiHeaderNames, PayiPropertyNames, payi_aws_bedrock_url
from payi.types.ingest_units_params import Units

from .instrument import (
    PayiInstrumentAwsBedrockConfig,
    _Context,
    _IsStreaming,
    _PayiInstrumentor,
)
from .version_helper import get_version_helper
from .ProviderRequest import _ChunkResult, _StreamingType, _ProviderRequest

if TYPE_CHECKING:
    from tokenizers import Tokenizer  # type: ignore
else:
    Tokenizer = None  

GUARDRAIL_SEMANTIC_FAILURE_DESCRIPTION = "Bedrock Guardrails intervened"

class BedrockInstrumentor:
    _module_name: str = "boto3"
    _module_version: str = ""

    _instrumentor: _PayiInstrumentor

    _guardrail_trace: bool = True

    _model_mapping: Dict[str, _Context] = {}

    _add_streaming_xproxy_result: bool = False

    @staticmethod
    def get_mapping(model_id: Optional[str]) -> _Context:
        if not model_id:
            return  {}

        return BedrockInstrumentor._model_mapping.get(model_id, {})

    @staticmethod
    def configure(aws_config: Optional[PayiInstrumentAwsBedrockConfig]) -> None:
        if not aws_config:
            return
        
        trace = aws_config.get("guardrail_trace", True)
        if trace is None:
            trace = True
        BedrockInstrumentor._guardrail_trace = trace

        add_streaming_xproxy_result = aws_config.get("add_streaming_xproxy_result", False)
        if add_streaming_xproxy_result:
            BedrockInstrumentor._add_streaming_xproxy_result = add_streaming_xproxy_result

        model_mappings = aws_config.get("model_mappings", [])
        if model_mappings:
            BedrockInstrumentor._model_mapping = _PayiInstrumentor._model_mapping_to_context_dict(model_mappings)

    @staticmethod
    def instrument(instrumentor: _PayiInstrumentor) -> None:
        BedrockInstrumentor._instrumentor = instrumentor

        BedrockInstrumentor._module_version = get_version_helper(BedrockInstrumentor._module_name)

        try:
            wrap_function_wrapper(
                "botocore.client",
                "ClientCreator.create_client",
                create_client_wrapper(instrumentor),
            )

            wrap_function_wrapper(
                "botocore.session",
                "Session.create_client",
                create_client_wrapper(instrumentor),
            )

        except Exception as e:
            instrumentor._logger.debug(f"Error instrumenting bedrock: {e}")
            return

@_PayiInstrumentor.payi_wrapper
def create_client_wrapper(instrumentor: _PayiInstrumentor, wrapped: Any, instance: Any, *args: Any, **kwargs: Any) -> Any: #  noqa: ARG001
    if kwargs.get("service_name") != "bedrock-runtime":
        # instrumentor._logger.debug(f"skipping client wrapper creation for {kwargs.get('service_name', '')} service")
        return wrapped(*args, **kwargs)

    try:
        client: Any = wrapped(*args, **kwargs)
        client.invoke_model = wrap_invoke(instrumentor, client.invoke_model, client)
        client.invoke_model_with_response_stream = wrap_invoke_stream(instrumentor, client.invoke_model_with_response_stream, client)
        client.converse = wrap_converse(instrumentor, client.converse, client)
        client.converse_stream = wrap_converse_stream(instrumentor, client.converse_stream, client)

        instrumentor._logger.debug(f"Instrumented bedrock client")

        if BedrockInstrumentor._instrumentor._proxy_default:
            # Register client callbacks to handle the Pay-i extra_headers parameter in the inference calls and redirect the request to the Pay-i endpoint
            _register_bedrock_client_callbacks(client)
            instrumentor._logger.debug(f"Registered bedrock client callbaks for proxy")

        return client
    except Exception as e:
        instrumentor._logger.debug(f"Error instrumenting bedrock client: {e}")
    
    return wrapped(*args, **kwargs)

BEDROCK_REQUEST_NAMES = [
    'request-created.bedrock-runtime.Converse',
    'request-created.bedrock-runtime.ConverseStream',
    'request-created.bedrock-runtime.InvokeModel',
    'request-created.bedrock-runtime.InvokeModelWithResponseStream',
]

def _register_bedrock_client_callbacks(client: Any) -> None:
    # Pass a unqiue_id to avoid registering the same callback multiple times in case this cell executed more than once
    # Redirect the request to the Pay-i endpoint after the request has been signed. 
    client.meta.events.register_last('request-created', _redirect_to_payi, unique_id=_redirect_to_payi)

def _redirect_to_payi(request: Any, event_name: str, **_: 'dict[str, Any]') -> None:
    from urllib3.util import parse_url
    from urllib3.util.url import Url

    if not event_name in BEDROCK_REQUEST_NAMES:
        return
    
    parsed_url: Url = parse_url(request.url)
    route_path = parsed_url.path
    request.url = f"{payi_aws_bedrock_url()}{route_path}"

    request.headers[PayiHeaderNames.api_key] = os.environ.get("PAYI_API_KEY", "")
    request.headers[PayiHeaderNames.provider_base_uri] = parsed_url.scheme + "://" + parsed_url.host # type: ignore
    
    extra_headers = BedrockInstrumentor._instrumentor._create_extra_headers()

    for key, value in extra_headers.items():
        request.headers[key] = value

class InvokeResponseWrapper(ObjectProxy): # type: ignore
    _cohere_embed_english_v3_tokenizer: Optional['Tokenizer'] = None

    def __init__(
        self,
        response: 'dict[str, Any]',
        body: Any,
        request: '_BedrockInvokeProviderRequest',
        ) -> None:

        super().__init__(body) # type: ignore
        self._response = response
        self._body = body
        self._request = request
        self._log_prompt_and_response = request._log_prompt_and_response

    def read(self, amt: Any =None) -> Any: # type: ignore
        # data is array of bytes
        data: bytes = self.__wrapped__.read(amt) # type: ignore
        response = json.loads(data) # type: ignore

        ingest = self._request._ingest

        # resource = ingest["resource"]
        # if not resource:
        #     return
        
        input: int = 0
        output: int = 0
        units: dict[str, Units] = ingest["units"]

        if self._request._is_anthropic:
            from .AnthropicInstrumentor import anthropic_process_synchronous_response

            anthropic_process_synchronous_response(
                request=self._request, 
                response=response,
                log_prompt_and_response=False, # will evaluate logging later
                assign_id=False)

        elif self._request._is_meta:
            input = response.get('prompt_token_count', 0)
            output = response.get('generation_token_count', 0)
            units["text"] = Units(input=input, output=output)

        elif self._request._is_nova:
            usage = response.get("usage", {})

            input = usage.get("inputTokens", 0)
            output = usage.get("outputTokens", 0)
            units["text"] = Units(input=input, output=output)

            text_cache_read = usage.get("cacheReadInputTokenCount", None)
            if text_cache_read:
                units["text_cache_read"] = text_cache_read

            text_cache_write = usage.get("cacheWriteInputTokenCount", None)
            if text_cache_write:
                units["text_cache_write"] = text_cache_write

            bedrock_converse_process_synchronous_function_call(self._request, response)

        elif self._request._is_amazon_titan_embed_text_v1:
            input = response.get('inputTextTokenCount', 0)
            units["text"] = Units(input=input, output=0)

        elif self._request._is_cohere_embed_english_v3:
            texts: list[str] = response.get("texts", [])
            if texts and len(texts) > 0:
                text = " ".join(texts)

                try:
                    from tokenizers import Tokenizer  # type: ignore

                    if self._cohere_embed_english_v3_tokenizer is None: # type: ignore
                        current_dir = os.path.dirname(os.path.abspath(__file__))
                        tokenizer_path = os.path.join(current_dir, "data", "cohere_embed_english_v3.json")
                        self._cohere_embed_english_v3_tokenizer = Tokenizer.from_file(tokenizer_path) # type: ignore

                    if self._cohere_embed_english_v3_tokenizer is not None and isinstance(self._cohere_embed_english_v3_tokenizer, Tokenizer): # type: ignore
                        tokens: list = self._cohere_embed_english_v3_tokenizer.encode(text, add_special_tokens=False).tokens # type: ignore

                        if tokens and isinstance(tokens, list):
                            units["text"] = Units(input=len(tokens), output=0) # type: ignore

                except ImportError:
                    self._request._instrumentor._logger.warning("tokenizers module not found, caller must install the tokenizers module. Cannot record text tokens for Cohere embed english v3")
                    pass
                except Exception as e:
                    self._request._instrumentor._logger.warning(f"Error processing Cohere embed english v3 response: {e}")
                    pass

        if self._log_prompt_and_response:
            ingest["provider_response_json"] = data.decode('utf-8') # type: ignore

        guardrails = response.get("amazon-bedrock-trace", {}).get("guardrail", {}).get("input", {})
        self._request.process_guardrails(guardrails)

        self._request.process_stop_action(response.get("amazon-bedrock-guardrailAction", ""))

        xproxy_result = self._request._instrumentor._ingest_units(self._request)
        self._request.assign_xproxy_result(self._response, xproxy_result)

        return data # type: ignore

def wrap_invoke(instrumentor: _PayiInstrumentor, wrapped: Any, instance: Any) -> Any:
    @wraps(wrapped)
    def invoke_wrapper(*args: Any, **kwargs: 'dict[str, Any]') -> Any:
        modelId:str = kwargs.get("modelId", "") # type: ignore

        return instrumentor.invoke_wrapper(
            _BedrockInvokeProviderRequest(instrumentor=instrumentor, model_id=modelId),
            _IsStreaming.false,
            wrapped,
            instance,
            args,
            kwargs,
        )   
    
    return invoke_wrapper

def wrap_invoke_stream(instrumentor: _PayiInstrumentor, wrapped: Any, instance: Any) -> Any:
    @wraps(wrapped)
    def invoke_wrapper(*args: Any, **kwargs: Any) -> Any:
        modelId: str = kwargs.get("modelId", "") # type: ignore

        instrumentor._logger.debug(f"bedrock invoke stream wrapper, modelId: {modelId}")
        return instrumentor.invoke_wrapper(
            _BedrockInvokeProviderRequest(instrumentor=instrumentor, model_id=modelId),
            _IsStreaming.true,
            wrapped,
            instance,
            args,
            kwargs,
        )

    return invoke_wrapper

def wrap_converse(instrumentor: _PayiInstrumentor, wrapped: Any, instance: Any) -> Any:
    @wraps(wrapped)
    def invoke_wrapper(*args: Any, **kwargs: 'dict[str, Any]') -> Any:
        modelId:str = kwargs.get("modelId", "") # type: ignore

        instrumentor._logger.debug(f"bedrock converse wrapper, modelId: {modelId}")
        return instrumentor.invoke_wrapper(
            _BedrockConverseProviderRequest(instrumentor=instrumentor),
            _IsStreaming.false,
            wrapped,
            instance,
            args,
            kwargs,
        )
    
    return invoke_wrapper

def wrap_converse_stream(instrumentor: _PayiInstrumentor, wrapped: Any, instance: Any) -> Any:
    @wraps(wrapped)
    def invoke_wrapper(*args: Any, **kwargs: Any) -> Any:
        modelId: str = kwargs.get("modelId", "") # type: ignore

        instrumentor._logger.debug(f"bedrock converse stream wrapper, modelId: {modelId}")
        return instrumentor.invoke_wrapper(
            _BedrockConverseProviderRequest(instrumentor=instrumentor),
            _IsStreaming.true,
            wrapped,
            instance,
            args,
            kwargs,
        )

    return invoke_wrapper

class _BedrockProviderRequest(_ProviderRequest):

    def __init__(self, instrumentor: _PayiInstrumentor):
        super().__init__(
            instrumentor=instrumentor,
            category=PayiCategories.aws_bedrock,
            streaming_type=_StreamingType.iterator,
            module_name=BedrockInstrumentor._module_name,
            module_version=BedrockInstrumentor._module_version,
            is_aws_client=True,
            )

    @override
    def process_request(self, instance: Any, extra_headers: 'dict[str, str]',  args: Sequence[Any], kwargs: Any) -> bool:
        modelId =  kwargs.get("modelId", "")
        self._ingest["resource"] = modelId

        if not self._price_as.resource and not self._price_as.category and modelId in BedrockInstrumentor._model_mapping:
            deployment = BedrockInstrumentor._model_mapping.get(modelId, {})
            self._price_as.category = deployment.get("price_as_category", "")
            self._price_as.resource = deployment.get("price_as_resource", "")
            self._price_as.resource_scope = deployment.get("resource_scope", None)

        if self._price_as.resource_scope:
            self._ingest["resource_scope"] = self._price_as.resource_scope
        
        # override defaults
        if self._price_as.category:
            self._ingest["category"] = self._price_as.category
        if self._price_as.resource:
            self._ingest["resource"] = self._price_as.resource

        return True

    def process_response_metadata(self, metadata: 'dict[str, Any]') -> None:
        request_id = metadata.get("RequestId", "")
        if request_id:
            self._ingest["provider_response_id"] = request_id

        response_headers = metadata.get("HTTPHeaders", {})
        if response_headers:
            self.add_response_headers(response_headers)

    @override
    def process_initial_stream_response(self, response: Any) -> None:
        super().process_initial_stream_response(response)
        self.process_response_metadata(response.get("ResponseMetadata", {}))

    @override
    def process_exception(self, exception: Exception, kwargs: Any, ) -> bool:
        try:
            if hasattr(exception, "response"):
                response: dict[str, Any] = getattr(exception, "response", {})
                status_code: int = response.get('ResponseMetadata', {}).get('HTTPStatusCode', 0)
                if status_code == 0:
                    return False

                self._ingest["http_status_code"] = status_code
                
                request_id = response.get('ResponseMetadata', {}).get('RequestId', "")
                if request_id:
                    self._ingest["provider_response_id"] = request_id

                error = response.get('Error', "")
                if error:
                    self._ingest["provider_response_json"] = json.dumps(error)

            return True

        except Exception as e:
            self._instrumentor._logger.debug(f"Error processing exception: {e}")
            return False

    def process_guardrails(self, guardrails: 'dict[str, Any]') -> None:
        units = self._ingest["units"]

        # while we iterate over the entire dict, only one guardrail is expected and supported
        for _, value in guardrails.items():
            # _ (key) is the guardrail id
            if not isinstance(value, dict):
                continue

            usage: dict[str, int] = value.get("invocationMetrics", {}).get("usage", {}) # type: ignore
            if not usage:
                continue

            topicPolicyUnits: int  = usage.get("topicPolicyUnits", 0) # type: ignore
            if topicPolicyUnits > 0:
                units["guardrail_topic"] = Units(input=topicPolicyUnits, output=0) # type: ignore

            contentPolicyUnits = usage.get("contentPolicyUnits", 0) # type: ignore
            if contentPolicyUnits > 0:
                units["guardrail_content"] = Units(input=contentPolicyUnits, output=0) # type: ignore

            wordPolicyUnits = usage.get("wordPolicyUnits", 0) # type: ignore    
            if wordPolicyUnits > 0:
                units["guardrail_word_free"] = Units(input=wordPolicyUnits, output=0) # type: ignore

            automatedReasoningPolicyUnits = usage.get("automatedReasoningPolicyUnits", 0) # type: ignore
            if automatedReasoningPolicyUnits > 0:
                units["guardrail_automated_reasoning"] = Units(input=automatedReasoningPolicyUnits, output=0) # type: ignore

            sensitiveInformationPolicyUnits = usage.get("sensitiveInformationPolicyUnits", 0) # type: ignore
            if sensitiveInformationPolicyUnits > 0:
                units["guardrail_sensitive_information"] = Units(input=sensitiveInformationPolicyUnits, output=0) # type: ignore

            sensitiveInformationPolicyFreeUnits = usage.get("sensitiveInformationPolicyFreeUnits", 0) # type: ignore
            if sensitiveInformationPolicyFreeUnits > 0:
                units["guardrail_sensitive_information_free"] = Units(input=sensitiveInformationPolicyFreeUnits, output=0) # type: ignore

            contextualGroundingPolicyUnits = usage.get("contextualGroundingPolicyUnits", 0) # type: ignore
            if contextualGroundingPolicyUnits > 0:
                units["guardrail_contextual_grounding"] = Units(input=contextualGroundingPolicyUnits, output=0) # type: ignore

            contentPolicyImageUnits = usage.get("contentPolicyImageUnits", 0) # type: ignore
            if contentPolicyImageUnits > 0:
                units["guardrail_content_image"] = Units(input=contentPolicyImageUnits, output=0) # type: ignore

class _BedrockInvokeProviderRequest(_BedrockProviderRequest):
    def __init__(self, instrumentor: _PayiInstrumentor, model_id: str):
        super().__init__(instrumentor=instrumentor)

        price_as_resource = BedrockInstrumentor._model_mapping.get(model_id, {}).get("price_as_resource", None)
        if price_as_resource:
            model_id = price_as_resource

        self._is_anthropic: bool = False
        self._is_nova: bool = False
        self._is_meta: bool = False
        self._is_amazon_titan_embed_text_v1: bool = False
        self._is_cohere_embed_english_v3: bool = False

        self._assign_model_state(model_id=model_id)

    def _assign_model_state(self, model_id: str) -> None:
        self._is_anthropic = 'anthropic' in model_id
        self._is_nova = 'nova' in model_id
        self._is_meta = 'meta' in model_id
        self._is_amazon_titan_embed_text_v1 = 'amazon.titan-embed-text-v1' == model_id
        self._is_cohere_embed_english_v3 = 'cohere.embed-english-v3' == model_id

    @override
    def process_request(self, instance: Any, extra_headers: 'dict[str, str]', args: Sequence[Any], kwargs: Any) -> bool:
        from .AnthropicInstrumentor import anthropic_has_image_and_get_texts

        super().process_request(instance, extra_headers, args, kwargs)
    
        # super().process_request will assign price_as mapping from global state, so evaluate afterwards
        if self._price_as.resource:
            self._assign_model_state(model_id=self._price_as.resource)

        guardrail_id = kwargs.get("guardrailIdentifier", "")
        if guardrail_id:
            self.add_internal_request_property(PayiPropertyNames.aws_bedrock_guardrail_id, guardrail_id)

        guardrail_version = kwargs.get("guardrailVersion", "")
        if guardrail_version:
            self.add_internal_request_property(PayiPropertyNames.aws_bedrock_guardrail_version, guardrail_version)

        if guardrail_id and guardrail_version and BedrockInstrumentor._guardrail_trace:
            trace = kwargs.get("trace", None)
            if not trace:
                kwargs["trace"] = "ENABLED"

        if self._is_anthropic:
            try:
                body = json.loads(kwargs.get("body", ""))
                messages = body.get("messages", {})
                if messages:
                    anthropic_has_image_and_get_texts(self, messages)
            except Exception as e:
                self._instrumentor._logger.debug(f"Bedrock invoke error processing request body: {e}")
        elif self._is_cohere_embed_english_v3:
            try:
                body = json.loads(kwargs.get("body", ""))
                input_type = body.get("input_type", "")
                if input_type == 'image':
                    images = body.get("images", [])
                    if (len(images) > 0):
                        # only supports one image according to docs
                        self._ingest["units"]["vision"] = Units(input=1, output=0)
            except Exception as e:
                self._instrumentor._logger.debug(f"Bedrock invoke error processing request body: {e}")
        return True

    @override
    def process_chunk(self, chunk: Any) -> _ChunkResult:
        chunk_dict = json.loads(chunk)

        guardrails = chunk_dict.get("amazon-bedrock-trace", {}).get("guardrail", {}).get("input", {})
        if guardrails:
            self.process_guardrails(guardrails)
    
        self.process_stop_action(chunk_dict.get("amazon-bedrock-guardrailAction", ""))

        if self._is_anthropic:
            from .AnthropicInstrumentor import anthropic_process_chunk
            return anthropic_process_chunk(self, chunk_dict, assign_id=False)
        
        if self._is_nova:
            bedrock_converse_process_streaming_for_function_call(self, chunk_dict)

        # meta and nova
        return self.process_invoke_other_provider_chunk(chunk_dict)

    def process_invoke_other_provider_chunk(self, chunk_dict: 'dict[str, Any]') -> _ChunkResult:
        ingest = False

        metrics = chunk_dict.get("amazon-bedrock-invocationMetrics", {})
        if metrics:
            input = metrics.get("inputTokenCount", 0)
            output = metrics.get("outputTokenCount", 0)
            self._ingest["units"]["text"] = Units(input=input, output=output)

            text_cache_read = metrics.get("cacheReadInputTokenCount", None)
            if text_cache_read:
                self._ingest["units"]["text_cache_read"] = text_cache_read

            text_cache_write = metrics.get("cacheWriteInputTokenCount", None)
            if text_cache_write:
                self._ingest["units"]["text_cache_write"] = text_cache_write

            ingest = True

        return _ChunkResult(send_chunk_to_caller=True, ingest=ingest)    

    @override
    def process_synchronous_response(
        self,
        response: Any,
        kwargs: Any) -> Any:

        self.process_response_metadata(response.get("ResponseMetadata", {}))

        response["body"] = InvokeResponseWrapper(
            response=response,
            body=response["body"],
            request=self)

        return response

    def process_stop_action(self, action: str) -> None:
        # record both as a semantic failure and guardrail action so it is discoverable through both properties
        if action == "INTERVENED":
            self.add_internal_request_property(PayiPropertyNames.failure, action)
            self.add_internal_request_property(PayiPropertyNames.failure_description, GUARDRAIL_SEMANTIC_FAILURE_DESCRIPTION)
            self.add_internal_request_property(PayiPropertyNames.aws_bedrock_guardrail_action, action)

    @override
    def remove_inline_data(self, prompt: 'dict[str, Any]') -> bool:# noqa: ARG002
        if not self._is_anthropic:
            return False

        from .AnthropicInstrumentor import anthropic_remove_inline_data
        body = prompt.get("body", "")
        if not body:
            return False
        
        body_json = json.loads(body)
        
        if anthropic_remove_inline_data(body_json):
            prompt["body"] = json.dumps(body_json)
            return True

        return False

class _BedrockConverseProviderRequest(_BedrockProviderRequest):
    @override
    def process_request(self, instance: Any, extra_headers: 'dict[str, str]', args: Sequence[Any], kwargs: Any) -> bool:
        super().process_request(instance, extra_headers, args, kwargs)

        guardrail_config = kwargs.get("guardrailConfig", {})
        if guardrail_config:
            guardrailIdentifier = guardrail_config.get("guardrailIdentifier", "")
            if guardrailIdentifier:
                self.add_internal_request_property(PayiPropertyNames.aws_bedrock_guardrail_id, guardrailIdentifier)

            guardrailVersion = guardrail_config.get("guardrailVersion", "")
            if guardrailVersion:
                self.add_internal_request_property(PayiPropertyNames.aws_bedrock_guardrail_version, guardrailVersion)

            if guardrailIdentifier and guardrailVersion and BedrockInstrumentor._guardrail_trace:
                trace = guardrail_config.get("trace", None)
                if not trace:
                    guardrail_config["trace"] = "enabled"

        return True

    @override
    def process_synchronous_response(
        self,
        response: 'dict[str, Any]',
        kwargs: Any) -> Any:

        usage = response.get("usage", {})
        input = usage.get("inputTokens", 0)
        output = usage.get("outputTokens", 0)

        units: dict[str, Units] = self._ingest["units"]
        units["text"] = Units(input=input, output=output)

        self.process_response_metadata(response.get("ResponseMetadata", {}))

        if self._log_prompt_and_response:
            response_without_metadata = response.copy()
            response_without_metadata.pop("ResponseMetadata", None)
            self._ingest["provider_response_json"] = json.dumps(response_without_metadata)

        bedrock_converse_process_synchronous_function_call(self, response)

        guardrails = response.get("trace", {}).get("guardrail", {}).get("inputAssessment", {})
        if guardrails:
            self.process_guardrails(guardrails)

        self.process_stop_reason(response.get("stopReason", ""))

        return None

    @override
    def process_chunk(self, chunk: 'dict[str, Any]') -> _ChunkResult:
        ingest = False
        metadata = chunk.get("metadata", {})

        if metadata:
            usage = metadata.get('usage', {})
            input = usage.get("inputTokens", 0)
            output = usage.get("outputTokens", 0)
            self._ingest["units"]["text"] = Units(input=input, output=output)

            guardrail = metadata.get("trace", {}).get("guardrail", {}).get("inputAssessment", {})
            if guardrail:
                self.process_guardrails(guardrail)

            ingest = True

        self.process_stop_reason(chunk.get("messageStop", {}).get("stopReason", ""))

        bedrock_converse_process_streaming_for_function_call(self, chunk)

        return _ChunkResult(send_chunk_to_caller=True, ingest=ingest)

    def process_stop_reason(self, reason: str) -> None:
        if reason == "guardrail_intervened":
            # record both as a semantic failure and guardrail action so it is discoverable through both properties
            self.add_internal_request_property(PayiPropertyNames.failure, reason)
            self.add_internal_request_property(PayiPropertyNames.failure_description, GUARDRAIL_SEMANTIC_FAILURE_DESCRIPTION)
            self.add_internal_request_property(PayiPropertyNames.aws_bedrock_guardrail_action, reason)

def bedrock_converse_process_streaming_for_function_call(request: _ProviderRequest, chunk: 'dict[str, Any]') -> None:  
    contentBlockStart = chunk.get("contentBlockStart", {})
    tool_use = contentBlockStart.get("start", {}).get("toolUse", {})
    if tool_use:
        index = contentBlockStart.get("contentBlockIndex", None)
        name = tool_use.get("name", "")

        if name and index is not None:
            request.add_streaming_function_call(index=index, name=name, arguments=None)
        
        return

    contentBlockDelta = chunk.get("contentBlockDelta", {})
    tool_use = contentBlockDelta.get("delta", {}).get("toolUse", {})
    if tool_use:
        index = contentBlockDelta.get("contentBlockIndex", None)
        input = tool_use.get("input", "")

        if input and index is not None:
            request.add_streaming_function_call(index=index, name=None, arguments=input)

        return

def bedrock_converse_process_synchronous_function_call(request: _ProviderRequest, response: 'dict[str, Any]') -> None:
    content = response.get("output", {}).get("message", {}).get("content", [])
    if content:
        for item in content:
            tool_use = item.get("toolUse", {})
            if tool_use:
                name = tool_use.get("name", "")
                input = tool_use.get("input", {})
                arguments: Optional[str] = None

                if input and isinstance(input, dict):
                    arguments = json.dumps(input)
                
                if name:
                    request.add_synchronous_function_call(name=name, arguments=arguments)

