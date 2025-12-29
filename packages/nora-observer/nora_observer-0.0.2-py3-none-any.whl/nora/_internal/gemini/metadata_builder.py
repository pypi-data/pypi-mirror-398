"""Gemini API trace 데이터 빌더"""

from typing import Any, Dict, Optional
from .types import RequestParams
from .utils import format_prompt, extract_usage_info, extract_response_text, extract_finish_reason


def build_trace_data(
    request_params: RequestParams,
    response: Any,
    start_time: float,
    end_time: float,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Gemini API 호출에 대한 trace 데이터를 생성합니다.

    Args:
        request_params: 요청 파라미터
        response: API 응답 객체
        start_time: 요청 시작 시간
        end_time: 요청 종료 시간
        error: 에러 메시지 (있는 경우)

    Returns:
        trace 데이터
    """
    # 기본 정보
    model = request_params.get("model", "gemini-1.5-pro")
    prompt = format_prompt(request_params)

    # 응답 처리
    response_text = ""
    tokens_used = 0
    finish_reason = None
    metadata = {}

    if response and not error:
        response_text = extract_response_text(response)
        usage = extract_usage_info(response)
        tokens_used = usage.get("total_tokens", 0)
        finish_reason = extract_finish_reason(response)

        # 메타데이터
        metadata = {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "generation_config": request_params.get("generation_config"),
            "safety_settings": request_params.get("safety_settings"),
        }

    return {
        "provider": "gemini",
        "model": model,
        "prompt": prompt,
        "response": response_text,
        "start_time": start_time,
        "end_time": end_time,
        "tokens_used": tokens_used,
        "error": error,
        "finish_reason": finish_reason,
        "metadata": metadata,
    }


def build_metadata(
    request_params: RequestParams,
    response: Any,
) -> Dict[str, Any]:
    """
    Gemini API 호출에 대한 메타데이터를 생성합니다.

    Args:
        request_params: 요청 파라미터
        response: API 응답 객체

    Returns:
        메타데이터
    """
    metadata = {
        "request": {
            "model": request_params.get("model", "gemini-1.5-pro"),
            "generation_config": request_params.get("generation_config"),
            "safety_settings": request_params.get("safety_settings"),
            "system_instruction": request_params.get("system_instruction"),
        }
    }

    if response:
        usage = extract_usage_info(response)
        metadata["response"] = {
            "finish_reason": extract_finish_reason(response),
            "usage": usage,
        }

    return metadata
