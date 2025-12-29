"""
Google Gemini 라이브러리 자동 패치
Gemini API 호출을 자동으로 trace합니다.
동기/비동기/스트리밍 모두 지원합니다.
"""

import time
from typing import Any, Callable, Dict

from ...client import _get_active_client as get_active_client
from ..._internal.gemini import extract_request_params, build_trace_data, wrap_streaming_response


def patch_gemini() -> None:
    """Google Gemini 라이브러리를 패치하여 자동 trace를 활성화합니다."""
    try:
        from google import genai
    except ImportError:
        return  # Gemini SDK가 설치되지 않은 경우 무시

    # 이미 패치되었는지 확인
    if hasattr(genai, "_nora_patched"):
        return

    # 원본 메서드 저장
    # Client.models.generate_content를 패치
    original_client_init = genai.Client.__init__

    def patched_client_init(self, *args, **kwargs):
        original_client_init(self, *args, **kwargs)

        # models.generate_content 메서드 패치
        if hasattr(self, "models") and hasattr(self.models, "generate_content"):
            original_generate = self.models.generate_content
            self.models.generate_content = _create_patched_function(
                original_generate, is_async=False
            )

        # models.generate_content_async가 있다면 패치
        if hasattr(self, "models") and hasattr(self.models, "generate_content_async"):
            original_generate_async = self.models.generate_content_async
            self.models.generate_content_async = _create_patched_function(
                original_generate_async, is_async=True
            )

    genai.Client.__init__ = patched_client_init

    # 패치 완료 표시
    genai._nora_patched = True


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

        async def patched_async(*args, **kwargs):
            return await _execute_with_trace_async(original_func, args, kwargs)

        return patched_async
    else:

        def patched_sync(*args, **kwargs):
            return _execute_with_trace_sync(original_func, args, kwargs)

        return patched_sync


def _execute_with_trace_sync(original_func: Callable, args: tuple, kwargs: Dict[str, Any]) -> Any:
    """
    동기 함수에서 Trace를 포함하여 원본 함수를 실행합니다.

    Args:
        original_func: 원본 함수
        args: 위치 인자
        kwargs: 키워드 인자

    Returns:
        함수 실행 결과
    """
    client = get_active_client()
    if not client or not client.enabled:
        return original_func(*args, **kwargs)

    start_time = time.time()
    request_params = extract_request_params(kwargs)

    try:
        response = original_func(*args, **kwargs)
        end_time = time.time()

        # 스트리밍 처리
        if kwargs.get("stream", False):
            return wrap_streaming_response(
                response, client, request_params, start_time, is_async=False
            )

        # 일반 응답 처리
        trace_data = build_trace_data(request_params, response, start_time, end_time, error=None)
        client._trace_method(**trace_data)
        return response

    except Exception as e:
        end_time = time.time()
        trace_data = build_trace_data(request_params, None, start_time, end_time, error=str(e))
        client._trace_method(**trace_data)
        raise


async def _execute_with_trace_async(
    original_func: Callable, args: tuple, kwargs: Dict[str, Any]
) -> Any:
    """
    비동기 함수에서 Trace를 포함하여 원본 함수를 실행합니다.

    Args:
        original_func: 원본 함수
        args: 위치 인자
        kwargs: 키워드 인자

    Returns:
        함수 실행 결과
    """
    client = get_active_client()
    if not client or not client.enabled:
        return await original_func(*args, **kwargs)

    start_time = time.time()
    request_params = extract_request_params(kwargs)

    try:
        response = await original_func(*args, **kwargs)
        end_time = time.time()

        # 스트리밍 처리
        if kwargs.get("stream", False):
            return wrap_streaming_response(
                response, client, request_params, start_time, is_async=True
            )

        # 일반 응답 처리
        trace_data = build_trace_data(request_params, response, start_time, end_time, error=None)
        client._trace_method(**trace_data)
        return response

    except Exception as e:
        end_time = time.time()
        trace_data = build_trace_data(request_params, None, start_time, end_time, error=str(e))
        client._trace_method(**trace_data)
        raise
