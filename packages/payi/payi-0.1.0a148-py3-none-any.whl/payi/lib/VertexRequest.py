from __future__ import annotations

import json
import math
from typing import Any, Optional
from typing_extensions import override

from payi.lib.helpers import PayiCategories
from payi.types.ingest_units_params import Units

from .instrument import _PayiInstrumentor
from .ProviderRequest import _ChunkResult, _StreamingType, _ProviderRequest


class _VertexRequest(_ProviderRequest): # type: ignore
    KNOWN_MODALITIES = ("VIDEO", "AUDIO", "TEXT", "VISION", "IMAGE")

    def __init__(
            self,
            instrumentor: _PayiInstrumentor,
            module_name: str,
            module_version: str
            ) -> None:
        super().__init__(
            instrumentor=instrumentor,
            category=PayiCategories.google_vertex,
            streaming_type=_StreamingType.generator,
            module_name=module_name,
            module_version=module_version,
            is_google_vertex_or_genai_client=True,
            )
        self._prompt_character_count = 0
        self._streaming_candidates_character_count: Optional[int] = None
        self._model_name: Optional[str] = None

    def _get_model_name(self, response: 'dict[str, Any]') -> Optional[str]:
        model: Optional[str] = response.get("model_version", None)
        if model:
            return model

        return self._model_name

    def process_chunk_dict(self,  response_dict: 'dict[str, Any]') -> _ChunkResult:
        ingest = False
        if "provider_response_id" not in self._ingest:
            id = response_dict.get("response_id", None)
            if id:
                self._ingest["provider_response_id"] = id

        if "provider_response_headers" not in self._ingest:
            response_headers = response_dict.get('sdk_http_response', {}).get('headers', {})
            if response_headers:
                self.add_response_headers(response_headers)

        if "resource" not in self._ingest: 
            model: Optional[str] = self._get_model_name(response_dict)  # type: ignore[unreachable]
            if model:
                self._ingest["resource"] = "google." + model

        for candidate in response_dict.get("candidates", []):
            parts = candidate.get("content", {}).get("parts", [])
            for part in parts:

                count = self.count_chars_skip_spaces(part.get("text", ""))
                if count > 0:
                    if self._streaming_candidates_character_count is None:
                        self._streaming_candidates_character_count = 0
                    self._streaming_candidates_character_count += count

                self.process_response_part_for_function_call(part)

        usage = response_dict.get("usage_metadata", {})
        if usage and "prompt_token_count" in usage and "candidates_token_count" in usage:
            self.compute_usage(
                model=self._get_model_name(response_dict),
                response_dict=response_dict,
                prompt_character_count=self._prompt_character_count,
                streaming_candidates_characters=self._streaming_candidates_character_count,
            )
            ingest = True

        return _ChunkResult(send_chunk_to_caller=True, ingest=ingest)

    @override
    def remove_inline_data(self, prompt: 'dict[str, Any]') -> bool:
        modified = False

        parts: list[dict[str, Any]] = prompt["contents"].get("parts", []) 
        for part in parts:
            inline_data = part.get("inline_data", {})
            if not isinstance(inline_data, dict):
                continue
            if "data" in inline_data:
                inline_data["data"] = _PayiInstrumentor._not_instrumented
                modified = True

        return modified

    def process_response_part_for_function_call(self, part: 'dict[str, Any]') -> None:
        function = part.get("function_call", {})
        if not function:
            return

        name = function.get("name", "")
        args = function.get("args", {})
        arguments: Optional[str] = None
        if args and isinstance(args, dict):
            arguments = json.dumps(args)

        if name:
            self.add_synchronous_function_call(name=name, arguments=arguments)

    @staticmethod
    def count_chars_skip_spaces(text: str) -> int:
        return sum(1 for c in text if not c.isspace())

    def vertex_process_synchronous_response(
        self,
        response_dict: 'dict[str, Any]',
        ) -> Any:

        response_headers = response_dict.get('sdk_http_response', {}).get('headers', {})
        if response_headers:
            self.add_response_headers(response_headers)

        id: Optional[str] = response_dict.get("response_id", None)
        if id:
            self._ingest["provider_response_id"] = id
        
        model: Optional[str] = self._get_model_name(response_dict)
        if model:
            self._ingest["resource"] = "google." + model

        candidates = response_dict.get("candidates", [])
        for candidate in candidates:
            parts = candidate.get("content", {}).get("parts", [])
            for part in parts:
                self.process_response_part_for_function_call(part)

        self.compute_usage(
            model=model,
            response_dict=response_dict,
            prompt_character_count=self._prompt_character_count,
            streaming_candidates_characters=self._streaming_candidates_character_count
            )
        
        if self._log_prompt_and_response:
            self._ingest["provider_response_json"] = [json.dumps(response_dict)]

        return None

    def compute_usage(
        self,
        model: Optional[str],
        response_dict: 'dict[str, Any]',
        prompt_character_count: int,
        streaming_candidates_characters: Optional[int]) -> None:

        def is_character_billing_model(model: str) -> bool:
            return model.startswith("gemini-1.")

        def is_large_context_token_model(model: str, input_tokens: int) -> bool:
            return model.startswith("gemini-2.5-pro") and input_tokens > 200000

        def add_units(request: _ProviderRequest, key: str, input: Optional[int] = None, output: Optional[int] = None) -> None:
            if key not in request._ingest["units"]:
                request._ingest["units"][key] = {}
            if input is not None:
                request._ingest["units"][key]["input"] = input
            if output is not None:
                request._ingest["units"][key]["output"] = output

        usage = response_dict.get("usage_metadata", {})
        input = usage.get("prompt_token_count", 0)

        prompt_tokens_details: list[dict[str, Any]] = usage.get("prompt_tokens_details", [])
        candidates_tokens_details: list[dict[str, Any]] = usage.get("candidates_tokens_details", [])
        cache_tokens_details: list[dict[str, Any]] = usage.get("cache_tokens_details", [])

        if not model:
            model = ""
        
        large_context = ""

        if is_character_billing_model(model):
            if input > 128000: 
                self._is_large_context = True
                large_context = "_large_context"

            # gemini 1.0 and 1.5 units are reported in characters, per second, per image, etc...
            for details in prompt_tokens_details:
                modality = details.get("modality", "")
                if not modality:
                    continue

                modality_token_count = details.get("token_count", 0)
                if modality == "TEXT":
                    input = prompt_character_count
                    if input == 0:
                        # back up calc if nothing was calculated from the prompt
                        input = response_dict["usage_metadata"]["prompt_token_count"] * 4

                    output = 0
                    if streaming_candidates_characters is None:
                        for candidate in response_dict.get("candidates", []):
                            parts = candidate.get("content", {}).get("parts", [])
                            for part in parts:
                                output += self.count_chars_skip_spaces(part.get("text", ""))

                        if output == 0:
                            # back up calc if no parts
                            output = response_dict["usage_metadata"]["candidates_token_count"] * 4
                    else:
                        output = streaming_candidates_characters

                    self._ingest["units"]["text"+large_context] = Units(input=input, output=output)

                elif modality == "IMAGE":
                    num_images = math.ceil(modality_token_count / 258)
                    add_units(self, "vision"+large_context, input=num_images)

                elif modality == "VIDEO":
                    video_seconds = math.ceil(modality_token_count / 285)
                    add_units(self, "video"+large_context, input=video_seconds)

                elif modality == "AUDIO":
                    audio_seconds = math.ceil(modality_token_count / 25)
                    add_units(self, "audio"+large_context, input=audio_seconds)

            # No need to gover the candidates_tokens_details as all the character based 1.x models only output TEXT
            # for details in candidates_tokens_details:

        else:
            # thinking tokens introduced in 2.5 after the transition to token based billing
            thinking_token_count = usage.get("thoughts_token_count", 0)

            if is_large_context_token_model(model, input):
                self._is_large_context = True
                large_context = "_large_context"

            cache_details: dict[str, int] = {}

            for details in cache_tokens_details:
                modality = details.get("modality", "")
                if not modality:
                    continue

                modality_token_count = details.get("token_count", 0)
                
                if modality == "IMAGE":
                    modality = "VISION"

                if modality in _VertexRequest.KNOWN_MODALITIES:
                    cache_details[modality] = modality_token_count
                    add_units(self, modality.lower() + "_cache_read" + large_context, input=modality_token_count)

            for details in prompt_tokens_details:
                modality = details.get("modality", "")
                if not modality:
                    continue

                modality_token_count = details.get("token_count", 0)

                if modality == "IMAGE":
                    modality = "VISION"

                if modality in _VertexRequest.KNOWN_MODALITIES:
                    # Subtract cache_details value if modality is present, floor at zero
                    if modality in cache_details:
                        modality_token_count = max(0, modality_token_count - cache_details[modality])

                    add_units(self, modality.lower() + large_context, input=modality_token_count)

            for details in candidates_tokens_details:
                modality = details.get("modality", "")
                if not modality:
                    continue

                modality_token_count = details.get("token_count", 0)
                if modality in _VertexRequest.KNOWN_MODALITIES:
                    add_units(self, modality.lower() + large_context, output=modality_token_count)

            if thinking_token_count > 0:
                add_units(self, "reasoning" + large_context, output=thinking_token_count)

        if not self._ingest["units"]:
            input = usage.get("prompt_token_count", 0)
            output = usage.get("candidates_token_count", 0) * 4
            
            if is_character_billing_model(model):
                if prompt_character_count > 0:
                    input = prompt_character_count
                else:
                    input *= 4

                # if no units were added, add a default unit and assume 4 characters per token
                self._ingest["units"]["text"+large_context] = Units(input=input, output=output)
            else:
                # if no units were added, add a default unit
                self._ingest["units"]["text"] = Units(input=input, output=output)