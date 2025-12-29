"""
OpenAI API 응답/요청 처리 유틸리티
"""

from typing import Any, Dict, Optional
from ..._internal.utils import safe_extract_attr, format_messages
from .types import RequestParams, ResponseContent, UsageInfo


def extract_request_params(
    kwargs: Dict[str, Any],
    is_responses: bool = False,
) -> RequestParams:
    """
    요청 파라미터를 추출합니다.

    Args:
        kwargs: API 호출 키워드 인자
        is_responses: Responses API 여부

    Returns:
        추출된 요청 파라미터
    """
    if is_responses:
        # Responses API (2024) 파라미터
        return RequestParams(
            model=kwargs.get("model", "unknown"),
            input=kwargs.get("input", []),
            temperature=kwargs.get("temperature"),
            max_output_tokens=kwargs.get("max_output_tokens"),
            top_p=kwargs.get("top_p"),
            presence_penalty=kwargs.get("presence_penalty"),
            frequency_penalty=kwargs.get("frequency_penalty"),
            stop=kwargs.get("stop"),
            metadata=kwargs.get("metadata"),
            stream=kwargs.get("stream", False),
        )

    # Chat Completions API 파라미터
    return RequestParams(
        model=kwargs.get("model", "unknown"),
        messages=kwargs.get("messages", []),
        temperature=kwargs.get("temperature"),
        max_tokens=kwargs.get("max_tokens"),
        max_completion_tokens=kwargs.get("max_completion_tokens"),
        top_p=kwargs.get("top_p"),
        frequency_penalty=kwargs.get("frequency_penalty"),
        presence_penalty=kwargs.get("presence_penalty"),
        n=kwargs.get("n", 1),
        stream=kwargs.get("stream", False),
        stop=kwargs.get("stop"),
        tools=kwargs.get("tools"),
        tool_choice=kwargs.get("tool_choice"),
        response_format=kwargs.get("response_format"),
        seed=kwargs.get("seed"),
        logprobs=kwargs.get("logprobs"),
        top_logprobs=kwargs.get("top_logprobs"),
        user=kwargs.get("user"),
    )


def format_prompt(request_params: RequestParams, is_responses: bool) -> str:
    """
    요청 파라미터에서 prompt를 추출합니다.

    Args:
        request_params: 요청 파라미터
        is_responses: Responses API 여부

    Returns:
        포맷된 prompt 문자열
    """
    if is_responses:
        return format_messages(request_params.get("input", []))
    return format_messages(request_params.get("messages", []))


def extract_response_content(response: Any) -> ResponseContent:
    """
    Chat Completions API 응답에서 텍스트, tool calls, logprobs 등을 추출합니다.

    Args:
        response: OpenAI API 응답 객체

    Returns:
        추출된 응답 내용
    """
    result = ResponseContent(
        text="",
        tool_calls=None,
        logprobs=None,
    )

    try:
        if not hasattr(response, "choices") or not response.choices:
            return result

        first_choice = response.choices[0]
        message = first_choice.message

        # 텍스트 응답
        if hasattr(message, "content") and message.content:
            result["text"] = message.content

        # Tool calls
        if hasattr(message, "tool_calls") and message.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in message.tool_calls
            ]

        # Logprobs
        if hasattr(first_choice, "logprobs") and first_choice.logprobs:
            result["logprobs"] = serialize_logprobs(first_choice.logprobs)

    except Exception:
        pass

    return result


def extract_responses_content(response: Any) -> ResponseContent:
    """
    Responses API 응답에서 텍스트와 tool calls를 추출합니다.

    Args:
        response: OpenAI Responses API 응답 객체

    Returns:
        추출된 응답 내용
    """
    result = ResponseContent(
        text="",
        tool_calls=None,
        logprobs=None,
    )

    try:
        # 우선 output_text 속성 활용
        if hasattr(response, "output_text") and response.output_text:
            result["text"] = response.output_text

        # output 리스트 구조 탐색
        if hasattr(response, "output") and response.output:
            for output_item in response.output:
                # ResponseFunctionToolCall 타입인 경우 (tool call)
                if hasattr(output_item, "type") and output_item.type == "function_call":
                    if result["tool_calls"] is None:
                        result["tool_calls"] = []

                    tool_call = {
                        "id": getattr(output_item, "call_id", ""),
                        "type": "function",
                        "function": {
                            "name": getattr(output_item, "name", ""),
                            "arguments": getattr(output_item, "arguments", "{}"),
                        },
                    }
                    result["tool_calls"].append(tool_call)

                # content 배열 처리 (텍스트 응답)
                elif hasattr(output_item, "content") and output_item.content:
                    for content_item in output_item.content:
                        # 텍스트 추출
                        if hasattr(content_item, "type") and content_item.type == "text":
                            if hasattr(content_item, "text"):
                                text_val = (
                                    getattr(content_item.text, "value", None) or content_item.text
                                )
                                if text_val and isinstance(text_val, str):
                                    result["text"] += text_val

        # choices/message 스타일이 있다면 재사용 (fallback)
        if not result["text"] and not result["tool_calls"] and hasattr(response, "choices"):
            return extract_response_content(response)

    except Exception:
        pass

    return result


def extract_detailed_usage(response: Any) -> UsageInfo:
    """
    상세한 토큰 사용량을 추출합니다.

    Args:
        response: OpenAI API 응답 객체

    Returns:
        토큰 사용량 정보
    """
    usage = UsageInfo()

    try:
        if hasattr(response, "usage") and response.usage:
            usage_obj = response.usage

            # 기본 토큰 정보
            usage["prompt_tokens"] = safe_extract_attr(usage_obj, "prompt_tokens", default=0)
            usage["completion_tokens"] = safe_extract_attr(
                usage_obj, "completion_tokens", default=0
            )
            usage["total_tokens"] = safe_extract_attr(usage_obj, "total_tokens", default=0)

            # O1 모델의 reasoning tokens
            if hasattr(usage_obj, "completion_tokens_details"):
                details = usage_obj.completion_tokens_details
                if details:
                    usage["reasoning_tokens"] = safe_extract_attr(
                        details, "reasoning_tokens", default=0
                    )
                    usage["accepted_prediction_tokens"] = safe_extract_attr(
                        details, "accepted_prediction_tokens", default=0
                    )
                    usage["rejected_prediction_tokens"] = safe_extract_attr(
                        details, "rejected_prediction_tokens", default=0
                    )

            # Prompt tokens 상세
            if hasattr(usage_obj, "prompt_tokens_details"):
                details = usage_obj.prompt_tokens_details
                if details:
                    usage["cached_tokens"] = safe_extract_attr(details, "cached_tokens", default=0)
                    usage["audio_tokens"] = safe_extract_attr(details, "audio_tokens", default=0)

    except Exception:
        pass

    return usage


def serialize_logprobs(logprobs: Any) -> Optional[Dict[str, Any]]:
    """
    Logprobs를 직렬화 가능한 형태로 변환합니다.

    Args:
        logprobs: Logprobs 객체

    Returns:
        직렬화된 logprobs 또는 None
    """
    try:
        # Pydantic 모델을 dict로 변환
        if hasattr(logprobs, "model_dump"):
            return logprobs.model_dump()
        elif hasattr(logprobs, "dict"):
            return logprobs.dict()
        else:
            return str(logprobs)
    except Exception:
        return None


def extract_finish_reason(response: Any, is_responses: bool) -> Optional[str]:
    """
    완료 이유를 추출합니다.

    Args:
        response: OpenAI API 응답 객체
        is_responses: Responses API 여부

    Returns:
        완료 이유 문자열 또는 None
    """
    if is_responses:
        return safe_extract_attr(response, "finish_reason", default=None)

    choices = safe_extract_attr(response, "choices", default=[])
    if choices and len(choices) > 0:
        return safe_extract_attr(choices[0], "finish_reason", default=None)

    return None
