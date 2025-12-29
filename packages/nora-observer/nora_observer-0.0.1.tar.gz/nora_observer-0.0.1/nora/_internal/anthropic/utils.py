"""
Anthropic API 응답/요청 처리 유틸리티
"""

from typing import Any, Dict, Optional
from ..._internal.utils import safe_extract_attr, format_messages
from .types import RequestParams, ResponseContent, UsageInfo


def extract_request_params(kwargs: Dict[str, Any]) -> RequestParams:
    """
    요청 파라미터를 추출합니다.

    Args:
        kwargs: API 호출 키워드 인자

    Returns:
        추출된 요청 파라미터
    """
    return RequestParams(
        model=kwargs.get("model", "unknown"),
        messages=kwargs.get("messages", []),
        max_tokens=kwargs.get("max_tokens"),
        temperature=kwargs.get("temperature"),
        top_p=kwargs.get("top_p"),
        top_k=kwargs.get("top_k"),
        stop_sequences=kwargs.get("stop_sequences"),
        system=kwargs.get("system"),
        stream=kwargs.get("stream", False),
        tools=kwargs.get("tools"),
        metadata=kwargs.get("metadata"),
    )


def format_prompt(request_params: RequestParams) -> str:
    """
    요청 파라미터에서 prompt를 추출합니다.

    Args:
        request_params: 요청 파라미터

    Returns:
        포맷된 prompt 문자열
    """
    # System 프롬프트 추가
    prompt_parts = []
    if request_params.system:
        prompt_parts.append(f"System: {request_params.system}")

    # 메시지 추가
    if request_params.messages:
        prompt_parts.append(format_messages(request_params.messages))

    return "\n".join(prompt_parts) if prompt_parts else ""


def extract_response_content(response: Any) -> ResponseContent:
    """
    Anthropic API 응답에서 텍스트, stop_reason 등을 추출합니다.

    Args:
        response: Anthropic API 응답 객체

    Returns:
        추출된 응답 내용
    """
    result = ResponseContent()

    try:
        # 텍스트 추출
        if hasattr(response, "content") and response.content:
            content = response.content
            if isinstance(content, list) and content:
                # Anthropic은 content가 리스트
                text_parts = []
                for block in content:
                    if hasattr(block, "text"):
                        text_parts.append(block.text)
                    elif isinstance(block, dict) and block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                result.text = "".join(text_parts)

        # Stop reason 추출
        if hasattr(response, "stop_reason"):
            result.stop_reason = response.stop_reason

        # 사용량 추출
        result.usage = extract_usage_info(response)

    except Exception:
        pass

    return result


def extract_usage_info(response: Any) -> Optional[UsageInfo]:
    """
    Anthropic 응답 객체에서 토큰 사용량을 추출합니다.

    Args:
        response: Anthropic API 응답 객체

    Returns:
        토큰 사용량 정보
    """
    try:
        usage = safe_extract_attr(response, "usage")
        if usage:
            input_tokens = safe_extract_attr(usage, "input_tokens", default=0)
            output_tokens = safe_extract_attr(usage, "output_tokens", default=0)
            return UsageInfo(input_tokens=input_tokens, output_tokens=output_tokens)
        return None
    except Exception:
        return None


def extract_tokens(response: Any) -> Optional[int]:
    """
    Anthropic 응답 객체에서 총 토큰 사용량을 반환합니다.

    Args:
        response: Anthropic API 응답 객체

    Returns:
        총 토큰 사용량 (input + output)
    """
    usage = extract_usage_info(response)
    return usage.total_tokens if usage else None
