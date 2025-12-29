"""Gemini API 유틸리티 함수"""

from typing import Any, Dict, Optional
from .types import RequestParams, ResponseContent, UsageInfo


def extract_request_params(kwargs: Dict[str, Any]) -> RequestParams:
    """
    Gemini API 호출 파라미터에서 필요한 정보를 추출합니다.

    Args:
        kwargs: generate_content() 호출 시 전달된 키워드 인자

    Returns:
        추출된 요청 파라미터
    """
    return RequestParams(
        model=kwargs.get("model", ""),
        contents=kwargs.get("contents", []),
        generation_config=kwargs.get("generation_config"),
        safety_settings=kwargs.get("safety_settings"),
        system_instruction=kwargs.get("system_instruction"),
    )


def format_prompt(request_params: RequestParams) -> str:
    """
    요청 파라미터를 프롬프트 문자열로 포맷팅합니다.

    Args:
        request_params: 요청 파라미터

    Returns:
        포맷팅된 프롬프트 문자열
    """
    formatted_parts = []

    # System instruction
    if request_params.get("system_instruction"):
        formatted_parts.append(f"System: {request_params['system_instruction']}")

    # Contents
    contents = request_params.get("contents", [])

    # contents가 문자열인 경우 (간단한 호출)
    if isinstance(contents, str):
        formatted_parts.append(f"User: {contents}")
    # contents가 리스트인 경우
    elif isinstance(contents, list):
        for content in contents:
            if isinstance(content, dict):
                role = content.get("role", "user")
                parts = content.get("parts", [])

                # parts에서 텍스트 추출
                text_parts = []
                for part in parts:
                    if isinstance(part, dict):
                        if "text" in part:
                            text_parts.append(part["text"])
                    elif isinstance(part, str):
                        text_parts.append(part)

                if text_parts:
                    formatted_parts.append(f"{role}: {' '.join(text_parts)}")

    return "\n".join(formatted_parts) if formatted_parts else ""


def extract_usage_info(response: Any) -> Dict[str, int]:
    """
    응답에서 토큰 사용량 정보를 추출합니다.

    Args:
        response: Gemini API 응답 객체

    Returns:
        토큰 사용량 정보 (prompt_tokens, completion_tokens, total_tokens)
    """
    usage = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }

    # usage_metadata 속성 확인
    if hasattr(response, "usage_metadata"):
        metadata = response.usage_metadata
        if hasattr(metadata, "prompt_token_count"):
            usage["prompt_tokens"] = metadata.prompt_token_count
        if hasattr(metadata, "candidates_token_count"):
            usage["completion_tokens"] = metadata.candidates_token_count
        if hasattr(metadata, "total_token_count"):
            usage["total_tokens"] = metadata.total_token_count

    return usage


def extract_response_text(response: Any) -> str:
    """
    응답에서 텍스트를 추출합니다.

    Args:
        response: Gemini API 응답 객체

    Returns:
        응답 텍스트
    """
    # response.text 속성이 있는 경우
    if hasattr(response, "text"):
        return response.text

    # response.candidates를 확인
    if hasattr(response, "candidates"):
        candidates = response.candidates
        if candidates and len(candidates) > 0:
            candidate = candidates[0]
            if hasattr(candidate, "content"):
                content = candidate.content
                if hasattr(content, "parts"):
                    parts = content.parts
                    text_parts = []
                    for part in parts:
                        if hasattr(part, "text"):
                            text_parts.append(part.text)
                    return "".join(text_parts)

    return ""


def extract_finish_reason(response: Any) -> str:
    """
    응답에서 종료 이유를 추출합니다.

    Args:
        response: Gemini API 응답 객체

    Returns:
        종료 이유
    """
    if hasattr(response, "candidates") and response.candidates:
        candidate = response.candidates[0]
        if hasattr(candidate, "finish_reason"):
            # FinishReason enum을 문자열로 변환
            finish_reason = candidate.finish_reason
            if hasattr(finish_reason, "name"):
                return finish_reason.name
            return str(finish_reason)

    return "STOP"


def extract_response_content(response: Any) -> ResponseContent:
    """
    응답에서 내용을 추출하여 ResponseContent 형식으로 반환합니다.

    Args:
        response: Gemini API 응답 객체

    Returns:
        ResponseContent 객체
    """
    text = extract_response_text(response)
    finish_reason = extract_finish_reason(response)
    
    return ResponseContent(
        text=text,
        tool_calls=None,  # Gemini는 현재 tool_calls를 별도로 처리하지 않음
        finish_reason=finish_reason,
    )
