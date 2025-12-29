"""
OpenAI Trace 메타데이터 구성
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from ..._internal.utils import safe_extract_attr
from .types import RequestParams, ResponseContent, UsageInfo
from .utils import (
    format_prompt,
    extract_response_content,
    extract_responses_content,
    extract_detailed_usage,
    extract_finish_reason,
)


def build_trace_data(
    request_params: RequestParams,
    response: Any,
    start_time: float,
    end_time: float,
    error: Optional[str],
) -> Dict[str, Any]:
    """
    완전한 trace 데이터를 구성합니다.

    Args:
        request_params: 요청 파라미터
        response: API 응답
        start_time: 시작 시간
        end_time: 종료 시간
        error: 에러 메시지 (있는 경우)

    Returns:
        Trace 데이터 dictionary
    """
    is_responses = "input" in request_params

    trace_data = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "provider": "openai",
        "model": request_params["model"],
        "start_time": start_time,
        "end_time": end_time,
        "prompt": format_prompt(request_params, is_responses),
    }

    if response and not error:
        _add_response_data(trace_data, response, request_params, is_responses)
    else:
        _add_error_data(trace_data, error, request_params, is_responses)

    return trace_data


def _add_response_data(
    trace_data: Dict[str, Any], response: Any, request_params: RequestParams, is_responses: bool
) -> None:
    """응답 데이터를 trace_data에 추가합니다."""
    # 응답 내용 추출
    response_content = (
        extract_responses_content(response) if is_responses else extract_response_content(response)
    )
    trace_data["response"] = response_content["text"]

    # 토큰 사용량
    usage = extract_detailed_usage(response)
    trace_data["tokens_used"] = usage.get("total_tokens")

    # 완료 이유
    finish_reason = extract_finish_reason(response, is_responses)
    if finish_reason:
        trace_data["finish_reason"] = finish_reason

    # 시스템 정보
    trace_data["system_fingerprint"] = safe_extract_attr(
        response, "system_fingerprint", default=None
    )
    trace_data["response_id"] = safe_extract_attr(response, "id", default=None)

    # Tool calls
    if response_content.get("tool_calls"):
        trace_data["tool_calls"] = response_content["tool_calls"]

    # Metadata 구성
    trace_data["metadata"] = build_metadata(
        request_params,
        usage,
        response_content,
        finish_reason,
        trace_data.get("system_fingerprint"),
        is_responses,
        len(safe_extract_attr(response, "choices", default=[])),
    )


def _add_error_data(
    trace_data: Dict[str, Any], error: str, request_params: RequestParams, is_responses: bool
) -> None:
    """에러 데이터를 trace_data에 추가합니다."""
    trace_data["error"] = error
    trace_data["metadata"] = {
        "request": {
            "parameters": {
                k: v
                for k, v in request_params.items()
                if k not in ["messages", "model", "input"] and v is not None
            }
        }
    }

    if is_responses:
        trace_data["metadata"]["request"]["input"] = request_params.get("input", [])
    else:
        trace_data["metadata"]["request"]["messages"] = request_params.get("messages", [])


def build_metadata(
    request_params: RequestParams,
    usage: UsageInfo,
    response_content: ResponseContent,
    finish_reason: Optional[str],
    system_fingerprint: Optional[str],
    is_responses: bool,
    choices_count: int,
) -> Dict[str, Any]:
    """
    Metadata를 구성합니다.

    Args:
        request_params: 요청 파라미터
        usage: 토큰 사용량 정보
        response_content: 응답 내용
        finish_reason: 완료 이유
        system_fingerprint: 시스템 fingerprint
        is_responses: Responses API 여부
        choices_count: choices 개수

    Returns:
        Metadata dictionary
    """
    metadata = {
        "request": {
            "parameters": {
                k: v
                for k, v in request_params.items()
                if k not in ["messages", "model", "prompt", "input"] and v is not None
            }
        },
        "response": {
            "usage": usage,
            "finish_reason": finish_reason,
            "system_fingerprint": system_fingerprint,
        },
    }

    # API 타입별 request 데이터
    if is_responses:
        metadata["request"]["input"] = request_params.get("input", [])
    else:
        metadata["request"]["messages"] = request_params.get("messages", [])
        metadata["response"]["choices_count"] = choices_count

    # Tool calls 및 logprobs
    if response_content.get("tool_calls"):
        metadata["response"]["tool_calls"] = response_content["tool_calls"]
    if response_content.get("logprobs"):
        metadata["response"]["logprobs"] = response_content["logprobs"]

    return metadata
