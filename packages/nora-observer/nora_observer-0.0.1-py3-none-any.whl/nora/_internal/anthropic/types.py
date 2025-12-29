"""
Anthropic API 타입 정의
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class RequestParams:
    """Anthropic API 요청 파라미터"""

    model: str
    messages: List[Dict[str, Any]] = field(default_factory=list)
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    stop_sequences: Optional[List[str]] = None
    system: Optional[str] = None
    stream: bool = False
    tools: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None

    def get(self, key: str, default: Any = None) -> Any:
        """딕셔너리처럼 접근"""
        return getattr(self, key, default)


@dataclass
class UsageInfo:
    """토큰 사용량 정보"""

    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class ResponseContent:
    """Anthropic API 응답 내용"""

    text: str = ""
    stop_reason: Optional[str] = None
    usage: Optional[UsageInfo] = None
