from __future__ import annotations

from typing import Any, List, Union, Optional, Sequence
from typing_extensions import override

from wrapt import wrap_function_wrapper  # type: ignore

from .instrument import _IsStreaming, _PayiInstrumentor
from .VertexRequest import _VertexRequest
from .version_helper import get_version_helper
from .ProviderRequest import _ChunkResult


class VertexInstrumentor:
    _module_name: str = "google-cloud-aiplatform"
    _module_version: str = ""

    @staticmethod
    def instrument(instrumentor: _PayiInstrumentor) -> None:
        VertexInstrumentor._module_version = get_version_helper(VertexInstrumentor._module_name)

        wrappers = [
            ("vertexai.generative_models", "GenerativeModel.generate_content", generate_wrapper(instrumentor)),
            ("vertexai.generative_models", "GenerativeModel.generate_content_async", agenerate_wrapper(instrumentor)),
            ("vertexai.preview.generative_models", "GenerativeModel.generate_content", generate_wrapper(instrumentor)),
            ("vertexai.preview.generative_models", "GenerativeModel.generate_content_async", agenerate_wrapper(instrumentor)),
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
    instrumentor._logger.debug("vertexai generate_content wrapper")
    return instrumentor.invoke_wrapper(
        _GoogleVertexRequest(instrumentor),
        _IsStreaming.kwargs,
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
    instrumentor._logger.debug("async vertexai generate_content wrapper")
    return await instrumentor.async_invoke_wrapper(
        _GoogleVertexRequest(instrumentor),
        _IsStreaming.kwargs,
        wrapped,
        instance,
        args,
        kwargs,
    )

class _GoogleVertexRequest(_VertexRequest):
    def __init__(self, instrumentor: _PayiInstrumentor):
        super().__init__(
            instrumentor=instrumentor,
            module_name=VertexInstrumentor._module_name,
            module_version=VertexInstrumentor._module_version,
            )
        self._prompt_character_count = 0
        self._candidates_character_count = 0

    @override
    def process_request(self, instance: Any, extra_headers: 'dict[str, str]', args: Sequence[Any], kwargs: Any) -> bool:
        from vertexai.generative_models import Content, Image, Part # type: ignore #  noqa: F401  I001

        # Try to extra the model name as a backup if the response does not provide it (older vertexai versions do not)
        if instance and hasattr(instance, "_model_name"):
            model = instance._model_name
            if model and isinstance(model, str):
                # Extract the model name after the last slash
                self._model_name = model.split('/')[-1]

        if not args:
            return True
        
        value: Union[ # type: ignore
            Content,
            str,
            Image,
            Part,
            List[Union[str, Image, Part]],
        ] = args[0] # type: ignore

        items: List[Union[str, Image, Part]] = [] # type: ignore #  noqa: F401  I001

        if not value:
            raise TypeError("value must not be empty")

        if isinstance(value, Content):
            items = value.parts # type: ignore
        if isinstance(value, (str, Image, Part)):
            items = [value] # type: ignore
        if isinstance(value, list):
            items = value # type: ignore

        for item in items: # type: ignore
            text = ""
            if isinstance(item, Part):
                d = item.to_dict() # type: ignore
                if "text" in d:
                    text = d["text"] # type: ignore
            elif isinstance(item, str):
                text = item

            if text != "":
                self._prompt_character_count += self.count_chars_skip_spaces(text) # type: ignore
             
        return True

    @override
    def process_request_prompt(self, prompt: 'dict[str, Any]', args: Sequence[Any], kwargs: 'dict[str, Any]') -> None:
        from vertexai.generative_models import Content, Image, Part, Tool # type: ignore #  noqa: F401  I001

        key = "contents"

        if not args:
            return
        
        value: Union[ # type: ignore
            Content,
            str,
            Image,
            Part,
            List[Union[str, Image, Part]],
        ] = args[0] # type: ignore

        items: List[Union[str, Image, Part]] = [] # type: ignore #  noqa: F401  I001

        if not value:
            return

        if isinstance(value, str):
            prompt[key] = Content(parts=[Part.from_text(value)]).to_dict() # type: ignore
        elif isinstance(value, (Image, Part)):
            prompt[key] = Content(parts=[value]).to_dict() # type: ignore
        elif isinstance(value, Content):
            prompt[key] = value.to_dict() # type: ignore
        elif isinstance(value, list):
            items = value # type: ignore
            parts = []

            for item in items: # type: ignore
                if isinstance(item, str):
                    parts.append(Part.from_text(item)) # type: ignore
                elif isinstance(item, Part):
                    parts.append(item) # type: ignore
                elif isinstance(item, Image):
                    parts.append(Part.from_image(item)) # type: ignore
                        
            prompt[key] = Content(parts=parts).to_dict() # type: ignore

        tools: Optional[list[Tool]] = kwargs.get("tools", None)  # type: ignore
        if tools:
            t: list[dict[Any, Any]] = []
            for tool in tools: # type: ignore
                if isinstance(tool, Tool):
                    t.append(tool.to_dict())  # type: ignore
            if t:
                prompt["tools"] = t

        tool_config = kwargs.get("tool_config", None)  # type: ignore
        if tool_config:
            # tool_config does not have to_dict or any other serializable object
            prompt["tool_config"] = str(tool_config)  # type: ignore

    @override
    def process_chunk(self, chunk: Any) -> _ChunkResult:
        return self.process_chunk_dict(response_dict=chunk.to_dict())
    
    @override
    def process_synchronous_response(
        self,
        response: Any,
        kwargs: Any) -> Any:
        return self.vertex_process_synchronous_response(response_dict=response.to_dict())
      
