"""
Anthropic 라이브러리 자동 패치
Anthropic API 호출을 자동으로 trace합니다.
동기/비동기/스트리밍 모두 지원합니다.
"""

import time
from typing import Any, Callable, Dict

from ...client import _get_active_client as get_active_client
from ..._internal.anthropic import (
    extract_request_params,
    build_trace_data,
    wrap_streaming_response,
)


def patch_anthropic() -> None:
    """Anthropic 라이브러리를 패치하여 자동 trace를 활성화합니다."""
    try:
        import anthropic
        from anthropic.resources.messages import Messages, AsyncMessages
    except ImportError:
        return  # Anthropic이 설치되지 않은 경우 무시

    # 이미 패치되었는지 확인
    if hasattr(anthropic, "_nora_patched"):
        return

    # 원본 메서드 저장
    original_sync_create = Messages.create
    original_async_create = AsyncMessages.create

    # 동기 버전 패치
    Messages.create = _create_patched_function(original_sync_create, is_async=False)

    # 비동기 버전 패치
    AsyncMessages.create = _create_patched_function(original_async_create, is_async=True)

    # 패치 완료 표시
    anthropic._nora_patched = True


def _create_patched_function(original_func: Callable, is_async: bool) -> Callable:
    """
    패치된 함수를 생성합니다.

    Args:
        original_func: 원본 함수
        is_async: 비동기 함수 여부

    Returns:
        패치된 함수
    """
    if is_async:

        async def patched_async(self, *args, **kwargs):
            return await _execute_with_trace_async(original_func, self, args, kwargs)

        return patched_async
    else:

        def patched_sync(self, *args, **kwargs):
            return _execute_with_trace_sync(original_func, self, args, kwargs)

        return patched_sync


def _execute_with_trace_sync(
    original_func: Callable, self: Any, args: tuple, kwargs: Dict[str, Any]
) -> Any:
    """
    동기 함수에서 Trace를 포함하여 원본 함수를 실행합니다.

    Args:
        original_func: 원본 함수
        self: 함수의 self 인자
        args: 위치 인자
        kwargs: 키워드 인자

    Returns:
        함수 실행 결과
    """
    client = get_active_client()
    if not client or not client.enabled:
        return original_func(self, *args, **kwargs)

    start_time = time.time()
    request_params = extract_request_params(kwargs)

    try:
        response = original_func(self, *args, **kwargs)
        end_time = time.time()

        # 스트리밍 처리
        if kwargs.get("stream", False):
            return wrap_streaming_response(
                response, client, request_params, start_time, is_async=False
            )

        # 일반 응답 처리
        from ..._internal.anthropic import extract_response_content

        response_content = extract_response_content(response)
        trace_data = build_trace_data(request_params, response_content, start_time, end_time)
        client._trace_method(**trace_data)
        return response

    except Exception as e:
        end_time = time.time()
        trace_data = build_trace_data(request_params, None, start_time, end_time, error=str(e))
        client._trace_method(**trace_data)
        raise


async def _execute_with_trace_async(
    original_func: Callable, self: Any, args: tuple, kwargs: Dict[str, Any]
) -> Any:
    """
    비동기 함수에서 Trace를 포함하여 원본 함수를 실행합니다.

    Args:
        original_func: 원본 함수
        self: 함수의 self 인자
        args: 위치 인자
        kwargs: 키워드 인자

    Returns:
        함수 실행 결과
    """
    client = get_active_client()
    if not client or not client.enabled:
        return await original_func(self, *args, **kwargs)

    start_time = time.time()
    request_params = extract_request_params(kwargs)

    try:
        response = await original_func(self, *args, **kwargs)
        end_time = time.time()

        # 스트리밍 처리
        if kwargs.get("stream", False):
            return await wrap_streaming_response(
                response, client, request_params, start_time, is_async=True
            )

        # 일반 응답 처리
        from ..._internal.anthropic import extract_response_content

        response_content = extract_response_content(response)
        trace_data = build_trace_data(request_params, response_content, start_time, end_time)
        client._trace_method(**trace_data)
        return response

    except Exception as e:
        end_time = time.time()
        trace_data = build_trace_data(request_params, None, start_time, end_time, error=str(e))
        client._trace_method(**trace_data)
        raise
