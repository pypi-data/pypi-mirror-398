"""Gemini API 스트리밍 응답 처리"""

from typing import Any, Iterator, AsyncIterator
from ...client import NoraClient
from .types import RequestParams
from .metadata_builder import build_trace_data


class GeminiStreamWrapper:
    """
    Gemini 스트리밍 응답을 래핑하여 자동으로 trace를 생성합니다.
    """

    def __init__(
        self,
        stream: Any,
        client: NoraClient,
        request_params: RequestParams,
        start_time: float,
        is_async: bool = False,
    ):
        self.stream = stream
        self.client = client
        self.request_params = request_params
        self.start_time = start_time
        self.is_async = is_async
        self.accumulated_text = ""
        self.total_tokens = 0
        self.finish_reason = None

    def __iter__(self) -> Iterator[Any]:
        """동기 스트리밍 이터레이터"""
        import time

        try:
            for chunk in self.stream:
                # 청크에서 텍스트 추출
                if hasattr(chunk, "text"):
                    self.accumulated_text += chunk.text

                # 토큰 사용량 누적
                if hasattr(chunk, "usage_metadata"):
                    metadata = chunk.usage_metadata
                    if hasattr(metadata, "total_token_count"):
                        self.total_tokens = metadata.total_token_count

                # finish_reason 추출
                if hasattr(chunk, "candidates") and chunk.candidates:
                    candidate = chunk.candidates[0]
                    if hasattr(candidate, "finish_reason"):
                        finish_reason = candidate.finish_reason
                        if hasattr(finish_reason, "name"):
                            self.finish_reason = finish_reason.name

                yield chunk

        finally:
            # 스트리밍 종료 시 trace 생성
            end_time = time.time()

            # Mock response 객체 생성
            mock_response = type(
                "MockResponse",
                (),
                {
                    "text": self.accumulated_text,
                    "usage_metadata": type(
                        "UsageMetadata", (), {"total_token_count": self.total_tokens}
                    )(),
                    "candidates": [
                        type(
                            "Candidate",
                            (),
                            {
                                "finish_reason": type(
                                    "FinishReason", (), {"name": self.finish_reason or "STOP"}
                                )()
                            },
                        )()
                    ],
                },
            )()

            trace_data = build_trace_data(
                self.request_params,
                mock_response,
                self.start_time,
                end_time,
                error=None,
            )
            self.client.trace(**trace_data)

    async def __aiter__(self) -> AsyncIterator[Any]:
        """비동기 스트리밍 이터레이터"""
        import time

        try:
            async for chunk in self.stream:
                # 청크에서 텍스트 추출
                if hasattr(chunk, "text"):
                    self.accumulated_text += chunk.text

                # 토큰 사용량 누적
                if hasattr(chunk, "usage_metadata"):
                    metadata = chunk.usage_metadata
                    if hasattr(metadata, "total_token_count"):
                        self.total_tokens = metadata.total_token_count

                # finish_reason 추출
                if hasattr(chunk, "candidates") and chunk.candidates:
                    candidate = chunk.candidates[0]
                    if hasattr(candidate, "finish_reason"):
                        finish_reason = candidate.finish_reason
                        if hasattr(finish_reason, "name"):
                            self.finish_reason = finish_reason.name

                yield chunk

        finally:
            # 스트리밍 종료 시 trace 생성
            end_time = time.time()

            # Mock response 객체 생성
            mock_response = type(
                "MockResponse",
                (),
                {
                    "text": self.accumulated_text,
                    "usage_metadata": type(
                        "UsageMetadata", (), {"total_token_count": self.total_tokens}
                    )(),
                    "candidates": [
                        type(
                            "Candidate",
                            (),
                            {
                                "finish_reason": type(
                                    "FinishReason", (), {"name": self.finish_reason or "STOP"}
                                )()
                            },
                        )()
                    ],
                },
            )()

            trace_data = build_trace_data(
                self.request_params,
                mock_response,
                self.start_time,
                end_time,
                error=None,
            )
            self.client.trace(**trace_data)


def wrap_streaming_response(
    stream: Any,
    client: NoraClient,
    request_params: RequestParams,
    start_time: float,
    is_async: bool = False,
) -> GeminiStreamWrapper:
    """
    스트리밍 응답을 래핑합니다.

    Args:
        stream: 원본 스트리밍 응답
        client: Nora 클라이언트
        request_params: 요청 파라미터
        start_time: 요청 시작 시간
        is_async: 비동기 스트림 여부

    Returns:
        래핑된 스트리밍 응답
    """
    return GeminiStreamWrapper(stream, client, request_params, start_time, is_async)
