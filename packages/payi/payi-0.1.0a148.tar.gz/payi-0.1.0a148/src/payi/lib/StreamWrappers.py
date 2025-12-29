from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union, Optional

from wrapt import ObjectProxy  # type: ignore

from payi.lib.helpers import _compact_json
from payi.lib.Stopwatch import Stopwatch
from payi.types.shared.xproxy_error import XproxyError
from payi.types.shared.xproxy_result import XproxyResult

from .ProviderRequest import _ChunkResult, _ProviderRequest

if TYPE_CHECKING:
    from .instrument import _PayiInstrumentor

__all__ = [
    "_StreamIteratorWrapper",
    "_StreamManagerWrapper",
    "_GeneratorWrapper",
]

class _StreamIteratorWrapper(ObjectProxy):  # type: ignore
    def __init__(
        self,
        response: Any,
        instance: Any,
        instrumentor: '_PayiInstrumentor',
        stopwatch: Stopwatch,
        request: _ProviderRequest,
    ) -> None:

        instrumentor._logger.debug(f"StreamIteratorWrapper: instance {instance}, category {request._category}")

        request.process_initial_stream_response(response)

        bedrock_from_stream: bool = False
        if request.is_aws_client:
            stream = response.get("stream", None)

            if stream:
                response = stream
                bedrock_from_stream = True
            else:
                response = response.get("body")
                bedrock_from_stream = False

        super().__init__(response)  # type: ignore

        self._response = response
        self._instance = instance

        self._instrumentor = instrumentor
        self._stopwatch: Stopwatch = stopwatch
        self._responses: list[str] = []

        self._request: _ProviderRequest = request

        self._first_token: bool = True
        self._bedrock_from_stream: bool = bedrock_from_stream
        self._ingested: bool = False
        self._iter_started: bool = False
        self._log_prompt_and_response: bool = request._log_prompt_and_response

    def __enter__(self) -> Any:
        self._instrumentor._logger.debug(f"StreamIteratorWrapper: __enter__")
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None: 
        self._instrumentor._logger.debug(f"StreamIteratorWrapper: __exit__")
        self.__wrapped__.__exit__(exc_type, exc_val, exc_tb)  # type: ignore

    async def __aenter__(self) -> Any:
        self._instrumentor._logger.debug(f"StreamIteratorWrapper: __aenter__")
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self._instrumentor._logger.debug(f"StreamIteratorWrapper: __aexit__")
        await self.__wrapped__.__aexit__(exc_type, exc_val, exc_tb)  # type: ignore

    def __iter__(self) -> Any:  
        self._iter_started = True
        if self._request.is_aws_client:
            # MUST reside in a separate function so that the yield statement (e.g. the generator) doesn't implicitly return its own iterator and overriding self
            self._instrumentor._logger.debug(f"StreamIteratorWrapper: bedrock __iter__")
            return self._iter_bedrock()

        self._instrumentor._logger.debug(f"StreamIteratorWrapper: __iter__")
        return self

    def _iter_bedrock(self) -> Any:
        # botocore EventStream doesn't have a __next__ method so iterate over the wrapped object in place
        for event in self.__wrapped__: # type: ignore
            result: Optional[_ChunkResult] = None

            if (self._bedrock_from_stream):
                result = self._evaluate_chunk(event)
            else:
                chunk = event.get('chunk') # type: ignore
                if chunk:
                    decode = chunk.get('bytes').decode() # type: ignore
                    result = self._evaluate_chunk(decode)

            if result and result.ingest:
                from .BedrockInstrumentor import BedrockInstrumentor

                xproxy_result = self._stop_iteration()

                # the xproxy_result is not json serializable by default so adding the object is opt in by the client
                if BedrockInstrumentor._add_streaming_xproxy_result:
                    self._request.assign_xproxy_result(event, xproxy_result)
            yield event

        self._instrumentor._logger.debug(f"StreamIteratorWrapper: bedrock iter finished")

        self._stop_iteration()

    def __aiter__(self) -> Any:
        self._iter_started = True
        self._instrumentor._logger.debug(f"StreamIteratorWrapper: __aiter__")
        return self

    def __next__(self) -> object:
        try:
            chunk: object = self.__wrapped__.__next__()  # type: ignore

            if self._ingested:
                self._instrumentor._logger.debug(f"StreamIteratorWrapper: __next__ already ingested, not processing chunk {chunk}")
                return chunk # type: ignore

            result = self._evaluate_chunk(chunk)

            if result.ingest:
                xproxy_result = self._stop_iteration()
                self._request.assign_xproxy_result(chunk, xproxy_result)

            if result.send_chunk_to_caller:
                return chunk # type: ignore
            else:
                return self.__next__()
        except Exception as e:
            if isinstance(e, StopIteration):
                self._stop_iteration()
            else:
                self._instrumentor._logger.debug(f"StreamIteratorWrapper: __next__ exception {e}")
            raise e

    async def __anext__(self) -> object:
        try:
            chunk: object = await self.__wrapped__.__anext__()  # type: ignore

            if self._ingested:
                self._instrumentor._logger.debug(f"StreamIteratorWrapper: __next__ already ingested, not processing chunk {chunk}")
                return chunk # type: ignore

            result = self._evaluate_chunk(chunk)

            if result.ingest:
                xproxy_result = await self._astop_iteration()
                self._request.assign_xproxy_result(chunk, xproxy_result)

            if  result.send_chunk_to_caller:
                return chunk # type: ignore
            else:
                return await self.__anext__()

        except Exception as e:
            if isinstance(e, StopAsyncIteration):
                await self._astop_iteration()
            else:
                self._instrumentor._logger.debug(f"StreamIteratorWrapper: __anext__ exception {e}")
            raise e

    def _evaluate_chunk(self, chunk: Any) -> _ChunkResult:
        if self._first_token:
            self._request._ingest["time_to_first_token_ms"] = self._stopwatch.elapsed_ms_int()
            self._first_token = False

        if self._log_prompt_and_response:
            self._responses.append(self.chunk_to_json(chunk))

        return self._request.process_chunk(chunk)

    def _process_stop_iteration(self) -> None:
        self._instrumentor._logger.debug(f"StreamIteratorWrapper: process stop iteration")

        self._stopwatch.stop()
        self._request._ingest["end_to_end_latency_ms"] = self._stopwatch.elapsed_ms_int()
        self._request._ingest["http_status_code"] = 200

        if self._log_prompt_and_response:
            self._request._ingest["provider_response_json"] = self._responses

    async def _astop_iteration(self) -> Optional[Union[XproxyResult, XproxyError]]:
        if self._ingested:
            self._instrumentor._logger.debug(f"StreamIteratorWrapper: astop iteration already ingested, skipping")
            return None

        self._process_stop_iteration()
        xproxy_result = await self._instrumentor._aingest_units(self._request)
        self._ingested = True

        return xproxy_result

    def _stop_iteration(self) -> Optional[Union[XproxyResult, XproxyError]]:
        if self._ingested:
            self._instrumentor._logger.debug(f"StreamIteratorWrapper: stop iteration already ingested, skipping")
            return None

        self._process_stop_iteration()
        xproxy_result = self._instrumentor._ingest_units(self._request)
        self._ingested = True

        return xproxy_result

    @staticmethod
    def chunk_to_json(chunk: Any) -> str:
        if hasattr(chunk, "to_json"):
            return str(chunk.to_json())
        elif isinstance(chunk, bytes):
            return chunk.decode()
        elif isinstance(chunk, str):
            return chunk
        else:
            # assume dict
            return _compact_json(chunk)

class _StreamManagerWrapper(ObjectProxy):  # type: ignore
    def __init__(
        self,
        stream_manager: Any,  # type: ignore
        instance: Any,
        instrumentor: _PayiInstrumentor, 
        stopwatch: Stopwatch,
        request: _ProviderRequest,
    ) -> None:
        instrumentor._logger.debug(f"StreamManagerWrapper: instance {instance}, category {request._category}")

        super().__init__(stream_manager)  # type: ignore

        self._stream_manager = stream_manager  
        self._instance = instance
        self._instrumentor = instrumentor
        self._stopwatch: Stopwatch = stopwatch
        self._responses: list[str] = []
        self._request: _ProviderRequest = request
        self._first_token: bool = True

    def __enter__(self) -> _StreamIteratorWrapper:
        self._instrumentor._logger.debug(f"_StreamManagerWrapper: __enter__")

        return _StreamIteratorWrapper(
            response=self.__wrapped__.__enter__(),  # type: ignore
            instance=self._instance,
            instrumentor=self._instrumentor,
            stopwatch=self._stopwatch,
            request=self._request,
        )

class _GeneratorWrapper:  # type: ignore
    def __init__(
        self,
        generator: Any,
        instance: Any,
        instrumentor: _PayiInstrumentor, 
        stopwatch: Stopwatch,
        request: _ProviderRequest,
    ) -> None:
        instrumentor._logger.debug(f"GeneratorWrapper: instance {instance}, category {request._category}")

        super().__init__()  # type: ignore
        
        self._generator = generator
        self._instance = instance
        self._instrumentor = instrumentor
        self._stopwatch: Stopwatch = stopwatch
        self._log_prompt_and_response: bool = request._log_prompt_and_response
        self._responses: list[str] = []
        self._request: _ProviderRequest = request
        self._first_token: bool = True
        self._ingested: bool = False
        self._iter_started: bool = False

    def __iter__(self) -> Any:
        self._iter_started = True
        self._instrumentor._logger.debug(f"GeneratorWrapper: __iter__")
        return self
        
    def __aiter__(self) -> Any:
        self._instrumentor._logger.debug(f"GeneratorWrapper: __aiter__")
        return self

    def _process_chunk(self, chunk: Any) -> _ChunkResult:
        if self._first_token:
            self._request._ingest["time_to_first_token_ms"] = self._stopwatch.elapsed_ms_int()
            self._first_token = False
            
        if self._log_prompt_and_response:
            dict = self._chunk_to_dict(chunk) 
            self._responses.append(_compact_json(dict))
                
        return self._request.process_chunk(chunk)
    
    def __next__(self) -> Any:
        try:
            chunk = next(self._generator)
            result = self._process_chunk(chunk)

            if result.ingest:
                xproxy_result = self._stop_iteration()
                self._request.assign_xproxy_result(chunk, xproxy_result)

            # ignore result.send_chunk_to_caller:
            return chunk

        except Exception as e:
            if isinstance(e, StopIteration):
                self._stop_iteration()
            else:
                self._instrumentor._logger.debug(f"GeneratorWrapper: __next__ exception {e}")            
            raise e

    async def __anext__(self) -> Any:
        try:
            chunk = await anext(self._generator) # type: ignore
            result = self._process_chunk(chunk)

            if result.ingest:
                xproxy_result = await self._astop_iteration()
                self._request.assign_xproxy_result(chunk, xproxy_result)

            # ignore result.send_chunk_to_caller:
            return chunk # type: ignore

        except Exception as e:
            if isinstance(e, StopAsyncIteration):
                await self._astop_iteration()
            else:
                self._instrumentor._logger.debug(f"GeneratorWrapper: __anext__ exception {e}")
            raise e

    @staticmethod
    def _chunk_to_dict(chunk: Any) -> 'dict[str, object]':
        if hasattr(chunk, "to_dict"):
            return chunk.to_dict() # type: ignore
        elif hasattr(chunk, "to_json_dict"):  
            return chunk.to_json_dict() # type: ignore
        else:
            return {}

    def _stop_iteration(self) -> Optional[Union[XproxyResult, XproxyError]]:
        if self._ingested:
            self._instrumentor._logger.debug(f"GeneratorWrapper: stop iteration already ingested, skipping")
            return None

        self._process_stop_iteration()
        xproxy_result = self._instrumentor._ingest_units(self._request)
        self._ingested = True
        return xproxy_result

    async def _astop_iteration(self) -> Optional[Union[XproxyResult, XproxyError]]:
        if self._ingested:
            self._instrumentor._logger.debug(f"GeneratorWrapper: astop iteration already ingested, skipping")
            return None

        self._process_stop_iteration()
        xproxy_result = await self._instrumentor._aingest_units(self._request)
        self._ingested = True
        return xproxy_result

    def _process_stop_iteration(self) -> None:
        self._instrumentor._logger.debug(f"GeneratorWrapper: stop iteration")

        self._stopwatch.stop()
        self._request._ingest["end_to_end_latency_ms"] = self._stopwatch.elapsed_ms_int()
        self._request._ingest["http_status_code"] = 200
            
        if self._log_prompt_and_response:
            self._request._ingest["provider_response_json"] = self._responses

