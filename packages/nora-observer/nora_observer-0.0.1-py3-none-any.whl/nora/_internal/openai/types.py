"""
OpenAI API 관련 타입 정의
"""

from typing import TypedDict, Optional, List, Dict, Any, Literal, Union


class ToolCallInfo(TypedDict, total=False):
    """Tool call 정보"""

    id: str
    type: Literal["function"]
    function: Dict[str, str]  # name, arguments


class ResponseContent(TypedDict, total=False):
    """API 응답 내용"""

    text: str
    tool_calls: Optional[List[ToolCallInfo]]
    logprobs: Optional[Dict[str, Any]]


class UsageInfo(TypedDict, total=False):
    """토큰 사용량 정보"""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    reasoning_tokens: int
    cached_tokens: int
    audio_tokens: int
    accepted_prediction_tokens: int
    rejected_prediction_tokens: int


class RequestParams(TypedDict, total=False):
    """요청 파라미터 (Chat Completions 또는 Responses API)"""

    model: str
    # Chat Completions API
    messages: List[Dict[str, Any]]
    temperature: Optional[float]
    max_tokens: Optional[int]
    max_completion_tokens: Optional[int]
    top_p: Optional[float]
    frequency_penalty: Optional[float]
    presence_penalty: Optional[float]
    n: int
    stream: bool
    stop: Optional[Union[str, List[str]]]
    tools: Optional[List[Dict[str, Any]]]
    tool_choice: Optional[Union[str, Dict[str, Any]]]
    response_format: Optional[Dict[str, Any]]
    seed: Optional[int]
    logprobs: Optional[bool]
    top_logprobs: Optional[int]
    user: Optional[str]
    # Responses API
    input: List[Dict[str, Any]]
    max_output_tokens: Optional[int]
    metadata: Optional[Dict[str, Any]]


class ToolExecutionInfo(TypedDict):
    """Tool 실행 정보"""

    call_id: str
    name: str
    arguments: Union[str, Dict[str, Any]]
