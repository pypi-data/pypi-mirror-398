"""Gemini API 타입 정의"""

from typing import TypedDict, Optional, List, Any, Dict, Literal


class ToolCallInfo(TypedDict, total=False):
    """Tool call 정보"""

    id: str
    type: Literal["function"]
    function: Dict[str, str]  # name, arguments


class ResponseContent(TypedDict, total=False):
    """API 응답 내용"""

    text: str
    tool_calls: Optional[List[ToolCallInfo]]
    finish_reason: Optional[str]


class UsageInfo(TypedDict, total=False):
    """토큰 사용량 정보"""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class RequestParams(TypedDict, total=False):
    """Gemini API 요청 파라미터"""

    model: str
    contents: List[Dict[str, Any]]
    generation_config: Optional[Dict[str, Any]]
    safety_settings: Optional[List[Dict[str, Any]]]
    system_instruction: Optional[str]
