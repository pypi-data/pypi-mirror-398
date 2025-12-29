"""
OpenAI 라이브러리 자동 패치
OpenAI API 호출을 자동으로 trace합니다.
"""

import time
import uuid
from datetime import datetime
from typing import Any, Callable, Dict

from ...client import _get_active_client as get_active_client, _current_execution_span
from ..._internal.openai import (
    extract_request_params,
    build_trace_data,
    auto_trace_tool_executions,
    auto_trace_tool_calls_from_response,
    wrap_streaming_response,
)


def patch_openai() -> None:
    """OpenAI 라이브러리를 패치하여 자동 trace를 활성화합니다."""
    try:
        import openai
        from openai.resources.chat.completions import Completions as ChatCompletions
        from openai.resources.chat.completions import AsyncCompletions as AsyncChatCompletions
        from openai.resources.responses import Responses as ResponsesAPI
        from openai.resources.responses import AsyncResponses as AsyncResponsesAPI
    except ImportError:
        return

    if hasattr(openai, "_nora_patched"):
        return

    # 원본 메서드 저장
    originals = {
        "chat_sync": ChatCompletions.create,
        "chat_async": AsyncChatCompletions.create,
        "responses_sync": ResponsesAPI.create,
        "responses_async": AsyncResponsesAPI.create,
    }

    # Chat Completions 패치
    ChatCompletions.create = _create_patched_function(
        originals["chat_sync"], is_async=False, is_responses=False
    )
    AsyncChatCompletions.create = _create_patched_function(
        originals["chat_async"], is_async=True, is_responses=False
    )

    # Responses API 패치
    ResponsesAPI.create = _create_patched_function(
        originals["responses_sync"], is_async=False, is_responses=True
    )
    AsyncResponsesAPI.create = _create_patched_function(
        originals["responses_async"], is_async=True, is_responses=True
    )

    openai._nora_patched = True


def _create_patched_function(
    original_func: Callable, is_async: bool, is_responses: bool
) -> Callable:
    """
    패치된 함수를 생성합니다.

    Args:
        original_func: 원본 함수
        is_async: 비동기 함수 여부
        is_responses: Responses API 여부

    Returns:
        패치된 함수
    """
    if is_async:

        async def patched_async(self, *args, **kwargs):
            return await _execute_with_trace_async(
                original_func, self, args, kwargs, is_responses=is_responses
            )

        return patched_async
    else:

        def patched_sync(self, *args, **kwargs):
            return _execute_with_trace_sync(
                original_func, self, args, kwargs, is_responses=is_responses
            )

        return patched_sync


def _execute_with_trace_sync(
    original_func: Callable,
    self: Any,
    args: tuple,
    kwargs: Dict[str, Any],
    is_responses: bool,
) -> Any:
    """
    동기 함수에서 Trace를 포함하여 원본 함수를 실행합니다.

    Args:
        original_func: 원본 함수
        self: 함수의 self 인자
        args: 위치 인자
        kwargs: 키워드 인자
        is_responses: Responses API 여부

    Returns:
        함수 실행 결과
    """
    client = get_active_client()
    if not client or not client.enabled:
        return original_func(self, *args, **kwargs)

    start_time = time.time()
    request_params = extract_request_params(kwargs, is_responses=is_responses)

    # Create execution span context placeholder for this LLM call
    # We'll update it with the real trace ID after _trace_method creates it
    span_data = {
        "id": None,  # Will be set after trace creation
        "timestamp": datetime.utcnow().isoformat(),
    }
    token = _current_execution_span.set(span_data)

    try:
        response = original_func(self, *args, **kwargs)
        end_time = time.time()

        # 스트리밍 처리
        if kwargs.get("stream", False):
            return wrap_streaming_response(
                response, client, request_params, start_time, is_async=False
            )

        # 일반 응답 처리
        trace_data = build_trace_data(request_params, response, start_time, end_time, error=None)
        
        # Update execution span context with the actual trace ID that will be created
        # We need to set this BEFORE calling _trace_method so tool traces can reference it
        span_data["id"] = trace_data.get("id")
        
        # Chat Completions API에서만 tool execution 자동 감지
        # This must happen AFTER we set the span ID but BEFORE the trace is sent
        if not is_responses:
            # First, check if response has tool_calls (first LLM call requesting tools)
            auto_trace_tool_calls_from_response(response, client, trace_data.get("id"))
            # Then, check if request has tool role messages (second LLM call with results)
            auto_trace_tool_executions(request_params, client)
        
        client._trace_method(**trace_data)
        return response

    except Exception as e:
        end_time = time.time()
        trace_data = build_trace_data(request_params, None, start_time, end_time, error=str(e))
        
        # Update execution span context with the actual trace ID
        span_data["id"] = trace_data.get("id")
        
        # Chat Completions API에서만 tool execution 자동 감지
        if not is_responses:
            auto_trace_tool_executions(request_params, client)
        
        client._trace_method(**trace_data)
        raise
    finally:
        _current_execution_span.reset(token)


async def _execute_with_trace_async(
    original_func: Callable,
    self: Any,
    args: tuple,
    kwargs: Dict[str, Any],
    is_responses: bool,
) -> Any:
    """
    비동기 함수에서 Trace를 포함하여 원본 함수를 실행합니다.

    Args:
        original_func: 원본 함수
        self: 함수의 self 인자
        args: 위치 인자
        kwargs: 키워드 인자
        is_responses: Responses API 여부

    Returns:
        함수 실행 결과
    """
    client = get_active_client()
    if not client or not client.enabled:
        return await original_func(self, *args, **kwargs)

    start_time = time.time()
    request_params = extract_request_params(kwargs, is_responses=is_responses)

    # Create execution span context placeholder for this LLM call
    # We'll update it with the real trace ID after _trace_method creates it
    span_data = {
        "id": None,  # Will be set after trace creation
        "timestamp": datetime.utcnow().isoformat(),
    }
    token = _current_execution_span.set(span_data)

    try:
        response = await original_func(self, *args, **kwargs)
        end_time = time.time()

        # 스트리밍 처리
        if kwargs.get("stream", False):
            return wrap_streaming_response(
                response, client, request_params, start_time, is_async=True
            )

        # 일반 응답 처리
        trace_data = build_trace_data(request_params, response, start_time, end_time, error=None)
        
        # Update execution span context with the actual trace ID that will be created
        # We need to set this BEFORE calling _trace_method so tool traces can reference it
        span_data["id"] = trace_data.get("id")
        
        # Chat Completions API에서만 tool execution 자동 감지
        # This must happen AFTER we set the span ID but BEFORE the trace is sent
        if not is_responses:
            # First, check if response has tool_calls (first LLM call requesting tools)
            auto_trace_tool_calls_from_response(response, client, trace_data.get("id"))
            # Then, check if request has tool role messages (second LLM call with results)
            auto_trace_tool_executions(request_params, client)
        
        client._trace_method(**trace_data)
        return response

    except Exception as e:
        end_time = time.time()
        trace_data = build_trace_data(request_params, None, start_time, end_time, error=str(e))
        
        # Update execution span context with the actual trace ID
        span_data["id"] = trace_data.get("id")
        
        # Chat Completions API에서만 tool execution 자동 감지
        if not is_responses:
            auto_trace_tool_executions(request_params, client)
        
        client._trace_method(**trace_data)
        raise
    finally:
        _current_execution_span.reset(token)
