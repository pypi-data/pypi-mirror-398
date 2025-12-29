"""
Anthropic trace 메타데이터 구성
"""

from typing import Any, Dict, Optional
from .types import RequestParams, ResponseContent


def build_trace_data(
    request_params: RequestParams,
    response: Optional[ResponseContent],
    start_time: float,
    end_time: float,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Trace 데이터를 구성합니다.

    Args:
        request_params: 요청 파라미터
        response: 응답 내용
        start_time: 시작 시간
        end_time: 종료 시간
        error: 에러 메시지 (있는 경우)

    Returns:
        Trace 데이터
    """
    from .utils import format_prompt

    trace_data = {
        "provider": "anthropic",
        "model": request_params.model,
        "prompt": format_prompt(request_params),
        "response": response.text if response else None,
        "start_time": start_time,
        "end_time": end_time,
        "stop_reason": response.stop_reason if response else None,
        "tokens_used": response.usage.total_tokens if response and response.usage else None,
        "error": error,
        "metadata": build_metadata(request_params, response),
    }

    return trace_data


def build_metadata(
    request_params: RequestParams,
    response: Optional[ResponseContent] = None,
) -> Dict[str, Any]:
    """
    메타데이터를 구성합니다.

    Args:
        request_params: 요청 파라미터
        response: 응답 내용

    Returns:
        메타데이터
    """
    metadata = {
        "temperature": request_params.temperature,
        "max_tokens": request_params.max_tokens,
        "top_p": request_params.top_p,
        "top_k": request_params.top_k,
        "stop_sequences": request_params.stop_sequences,
        "system": request_params.system,
        "messages_count": len(request_params.messages),
        "has_tools": bool(request_params.tools),
    }

    # 응답 메타데이터 추가
    if response and response.usage:
        metadata["input_tokens"] = response.usage.input_tokens
        metadata["output_tokens"] = response.usage.output_tokens

    return metadata
