"""
Anthropic 스트리밍 응답 처리
"""

import time
from typing import Any, Dict
from .utils import format_prompt
from .types import RequestParams


def wrap_streaming_response(
    response: Any,
    client: Any,
    request_params: RequestParams,
    start_time: float,
    is_async: bool,
) -> Any:
    """
    스트리밍 응답을 래핑하여 완료 시 trace를 기록합니다.

    Args:
        response: Anthropic 스트리밍 응답
        client: Nora client 인스턴스
        request_params: 요청 파라미터
        start_time: 시작 시간
        is_async: 비동기 여부

    Returns:
        래핑된 스트리밍 응답
    """
    collected_data: Dict[str, Any] = {
        "text": "",
        "stop_reason": None,
        "usage": None,
    }

    def process_event(event: Any) -> Any:
        """이벤트를 처리하고 데이터를 수집합니다."""
        try:
            # 이벤트 타입에 따른 처리
            event_type = getattr(event, "type", None)

            if event_type == "content_block_delta":
                # 텍스트 델타
                delta = getattr(event, "delta", None)
                if delta:
                    delta_type = getattr(delta, "type", None)
                    if delta_type == "text_delta":
                        text = getattr(delta, "text", "")
                        if text:
                            collected_data["text"] += text

            elif event_type == "message_delta":
                # Stop reason 추출
                delta = getattr(event, "delta", None)
                if delta:
                    stop_reason = getattr(delta, "stop_reason", None)
                    if stop_reason:
                        collected_data["stop_reason"] = stop_reason

                # Usage 정보 추출
                usage = getattr(event, "usage", None)
                if usage:
                    collected_data["usage"] = {
                        "input_tokens": getattr(usage, "input_tokens", 0),
                        "output_tokens": getattr(usage, "output_tokens", 0),
                    }

        except Exception:
            pass

        return event

    def finalize_trace() -> None:
        """스트리밍 완료 후 trace를 기록합니다."""
        end_time = time.time()

        # Usage 정보 처리
        tokens_used = None
        if collected_data["usage"]:
            usage_data = collected_data["usage"]
            tokens_used = usage_data.get("input_tokens", 0) + usage_data.get("output_tokens", 0)

        trace_data = {
            "provider": "anthropic",
            "model": request_params.model,
            "prompt": format_prompt(request_params),
            "response": collected_data["text"],
            "start_time": start_time,
            "end_time": end_time,
            "stop_reason": collected_data["stop_reason"],
            "tokens_used": tokens_used,
            "metadata": {
                "temperature": request_params.temperature,
                "max_tokens": request_params.max_tokens,
                "top_p": request_params.top_p,
                "top_k": request_params.top_k,
                "system": request_params.system,
                "messages_count": len(request_params.messages),
                "is_streaming": True,
                "usage": collected_data["usage"],
            },
        }

        client.trace(**trace_data)

    if is_async:
        return _wrap_async_streaming(response, process_event, finalize_trace)
    else:
        return _wrap_sync_streaming(response, process_event, finalize_trace)


def _wrap_sync_streaming(response: Any, process_event, finalize_trace) -> Any:
    """
    동기 스트리밍 응답을 래핑합니다.

    Args:
        response: Anthropic 스트리밍 응답
        process_event: 이벤트 처리 함수
        finalize_trace: Trace 최종화 함수

    Returns:
        래핑된 스트리밍 응답 이터레이터
    """

    class WrappedStreamingResponse:
        def __init__(self, stream):
            self.stream = stream
            self._closed = False

        def __iter__(self):
            try:
                for event in self.stream:
                    yield process_event(event)
            finally:
                if not self._closed:
                    finalize_trace()
                    self._closed = True

        def __enter__(self):
            return self

        def __exit__(self, *args):
            if not self._closed:
                finalize_trace()
                self._closed = True

    return WrappedStreamingResponse(response)


async def _wrap_async_streaming(response: Any, process_event, finalize_trace) -> Any:
    """
    비동기 스트리밍 응답을 래핑합니다.

    Args:
        response: Anthropic 비동기 스트리밍 응답
        process_event: 이벤트 처리 함수
        finalize_trace: Trace 최종화 함수

    Returns:
        래핑된 비동기 스트리밍 응답 이터레이터
    """

    class WrappedAsyncStreamingResponse:
        def __init__(self, stream):
            self.stream = stream
            self._closed = False

        async def __aiter__(self):
            try:
                async for event in self.stream:
                    yield process_event(event)
            finally:
                if not self._closed:
                    finalize_trace()
                    self._closed = True

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            if not self._closed:
                finalize_trace()
                self._closed = True

    return WrappedAsyncStreamingResponse(response)
