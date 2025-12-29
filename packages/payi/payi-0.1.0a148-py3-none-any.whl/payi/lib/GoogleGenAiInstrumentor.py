from __future__ import annotations

from typing import Any, List, Union, Sequence
from typing_extensions import override

from wrapt import wrap_function_wrapper  # type: ignore

from .instrument import _IsStreaming, _PayiInstrumentor
from .VertexRequest import _VertexRequest
from .version_helper import get_version_helper
from .ProviderRequest import _ChunkResult


class GoogleGenAiInstrumentor:
    _module_name: str = "google-genai"
    _module_version: str = ""

    @staticmethod
    def instrument(instrumentor: _PayiInstrumentor) -> None:
        GoogleGenAiInstrumentor._module_version = get_version_helper(GoogleGenAiInstrumentor._module_name)

        wrappers = [
            ("google.genai.models", "Models.generate_content", generate_wrapper(instrumentor)),
            ("google.genai.models", "Models.generate_content_stream", generate_stream_wrapper(instrumentor)),
            ("google.genai.models", "AsyncModels.generate_content", agenerate_wrapper(instrumentor)),
            ("google.genai.models", "AsyncModels.generate_content_stream", agenerate_stream_wrapper(instrumentor)),
        ]

        for module, method, wrapper in wrappers:
            try:
                wrap_function_wrapper(module, method, wrapper)
            except Exception as e:
                instrumentor._logger.debug(f"Failed to wrap {module}.{method}: {e}")

@_PayiInstrumentor.payi_wrapper
def generate_wrapper(
    instrumentor: _PayiInstrumentor,
    wrapped: Any,
    instance: Any,
    *args: Any,
    **kwargs: Any,
) -> Any:
    instrumentor._logger.debug("genai generate_content wrapper")
    return instrumentor.invoke_wrapper(
        _GoogleGenAiRequest(instrumentor),
        _IsStreaming.false,
        wrapped,
        instance,
        args,
        kwargs,
    )

@_PayiInstrumentor.payi_wrapper
def generate_stream_wrapper(
    instrumentor: _PayiInstrumentor,
    wrapped: Any,
    instance: Any,
    *args: Any,
    **kwargs: Any,
) -> Any:
    instrumentor._logger.debug("genai generate_content_stream wrapper")
    return instrumentor.invoke_wrapper(
        _GoogleGenAiRequest(instrumentor),
        _IsStreaming.true,
        wrapped,
        instance,
        args,
        kwargs,
    )

@_PayiInstrumentor.payi_awrapper
async def agenerate_wrapper(
    instrumentor: _PayiInstrumentor,
    wrapped: Any,
    instance: Any,
    *args: Any,
    **kwargs: Any,
) -> Any:
    instrumentor._logger.debug("async genai generate_content wrapper")
    return await instrumentor.async_invoke_wrapper(
        _GoogleGenAiRequest(instrumentor),
        _IsStreaming.false,
        wrapped,
        instance,
        args,
        kwargs,
    )

@_PayiInstrumentor.payi_wrapper
async def agenerate_stream_wrapper(
    instrumentor: _PayiInstrumentor,
    wrapped: Any,
    instance: Any,
    *args: Any,
    **kwargs: Any,
) -> Any:
    instrumentor._logger.debug("async genai generate_content_stream wrapper")
    return await instrumentor.async_invoke_wrapper(
        _GoogleGenAiRequest(instrumentor),
        _IsStreaming.true,
        wrapped,
        instance,
        args,
        kwargs,
    )

class _GoogleGenAiRequest(_VertexRequest):
    def __init__(self, instrumentor: _PayiInstrumentor):
        super().__init__(
            instrumentor=instrumentor,
            module_name=GoogleGenAiInstrumentor._module_name,
            module_version=GoogleGenAiInstrumentor._module_version,
            )
        self._prompt_character_count = 0
        self._candidates_character_count = 0

    @override
    def process_request(self, instance: Any, extra_headers: 'dict[str, str]', args: Sequence[Any], kwargs: Any) -> bool:
        from google.genai.types import Content, PIL_Image, Part # type: ignore #  noqa: F401  I001

        if not kwargs:
            return True

        model: str = kwargs.get("model", "")
        self._ingest["resource"] = "google." + model

        value: Union[ # type: ignore
            Content,
            str,
            PIL_Image,
            Part,
            List[Union[str, PIL_Image, Part]],
        ] = kwargs.get("contents", None)  # type: ignore 

        items: List[Union[str, Image, Part]] = [] # type: ignore #  noqa: F401  I001

        if not value:
            raise TypeError("value must not be empty")

        if isinstance(value, Content):
            items = value.parts # type: ignore
        if isinstance(value, (str, PIL_Image, Part)):
            items = [value] # type: ignore
        if isinstance(value, list):
            items = value # type: ignore

        for item in items: # type: ignore
            text = ""
            if isinstance(item, Part):
                d = item.to_json_dict() # type: ignore
                if "text" in d:
                    text = d["text"] # type: ignore
            elif isinstance(item, str):
                text = item

            if text != "":
                self._prompt_character_count += self.count_chars_skip_spaces(text) # type: ignore

        return True

    @override
    def process_request_prompt(self, prompt: 'dict[str, Any]', args: Sequence[Any], kwargs: 'dict[str, Any]') -> None:
        from google.genai.types import Content, PIL_Image, Part, Tool, GenerateContentConfig, GenerateContentConfigDict, ToolConfig  # type: ignore #  noqa: F401  I001

        key = "contents"

        if not kwargs:
            return
        
        value: Union[ # type: ignore
            Content,
            str,
            PIL_Image,
            Part,
            List[Union[str, PIL_Image, Part]],
        ] = kwargs.get("contents", None)  # type: ignore

        items: List[Union[str, Image, Part]] = [] # type: ignore #  noqa: F401  I001

        if not value:
            return

        if isinstance(value, str):
            prompt[key] = Content(parts=[Part.from_text(text=value)]).to_json_dict() # type: ignore
        elif isinstance(value, (PIL_Image, Part)):
            prompt[key] = Content(parts=[value]).to_json_dict() # type: ignore
        elif isinstance(value, Content):
            prompt[key] = value.to_json_dict() # type: ignore
        elif isinstance(value, list):
            items = value # type: ignore
            parts = []

            for item in items: # type: ignore
                if isinstance(item, str):
                    parts.append(Part.from_text(text=item)) # type: ignore
                elif isinstance(item, Part):
                    parts.append(item) # type: ignore
                # elif isinstance(item, PIL_Image): TODO
                #     parts.append(Part.from_image(item)) # type: ignore
                        
            prompt[key] = Content(parts=parts).to_json_dict() # type: ignore

        # tools: Optional[list[Tool]] = kwargs.get("tools", None)  # type: ignore
        # if tools:
        #     t: list[dict[Any, Any]] = []
        #     for tool in tools: # type: ignore
        #         if isinstance(tool, Tool):
        #             t.append(tool.text=())  # type: ignore
        #     if t:
        #         prompt["tools"] = t
        config_kwarg = kwargs.get("config", None)  # type: ignore
        if config_kwarg is None:
            return
        
        config: GenerateContentConfigDict = {}
        if isinstance(config_kwarg, GenerateContentConfig):
            config = config_kwarg.to_json_dict()  # type: ignore
        else:
            config = config_kwarg
        
        tools = config.get("tools", None)  # type: ignore
        if isinstance(tools, list):
            t: list[dict[str, object]] = []
            for tool in tools: # type: ignore
                if isinstance(tool, Tool):
                    t.append(tool.to_json_dict())  # type: ignore
            if t:
                prompt["tools"] = t

        tool_config = config.get("tool_config", None)  # type: ignore
        if isinstance(tool_config, ToolConfig):
            prompt["tool_config"] = tool_config.to_json_dict()  # type: ignore
        elif isinstance(tool_config, dict):
            prompt["tool_config"] = tool_config

    @override
    def process_chunk(self, chunk: Any) -> _ChunkResult:
        response_dict: dict[str, Any] = chunk.to_json_dict()

        model: str = response_dict.get("model_version", "")
        self._ingest["resource"] = "google." + model

        return self.process_chunk_dict(response_dict=response_dict)

    @override
    def process_synchronous_response(
        self,
        response: Any,
        kwargs: Any) -> Any:

        return self.vertex_process_synchronous_response(response_dict=response.to_json_dict())