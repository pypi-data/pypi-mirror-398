"""공통 유틸리티 함수"""

from typing import Any, Dict, List


def format_messages(messages: List[Dict[str, Any]]) -> str:
    """
    메시지 리스트를 문자열로 포맷팅합니다.

    OpenAI와 Anthropic 모두 지원하는 범용 포맷터입니다.
    """
    if not messages:
        return ""

    formatted = []
    for msg in messages:
        # Handle both dict and Pydantic model objects
        if hasattr(msg, 'model_dump'):
            # Pydantic model - convert to dict
            msg_dict = msg.model_dump()
        elif hasattr(msg, 'dict'):
            # Older Pydantic version
            msg_dict = msg.dict()
        elif isinstance(msg, dict):
            msg_dict = msg
        else:
            # Fallback: try to access as object attributes
            try:
                msg_dict = {
                    'role': getattr(msg, 'role', 'unknown'),
                    'content': getattr(msg, 'content', '')
                }
            except Exception:
                continue
        
        role = msg_dict.get("role", "unknown")
        content = msg_dict.get("content", "")

        # Anthropic은 content가 리스트일 수 있음
        if isinstance(content, list):
            text_parts = [
                c.get("text", "")
                for c in content
                if isinstance(c, dict) and c.get("type") == "text"
            ]
            content = " ".join(text_parts)

        formatted.append(f"{role}: {content}")

    return "\n".join(formatted)


def safe_extract_attr(obj: Any, *attrs: str, default: Any = None) -> Any:
    """
    안전하게 중첩된 속성을 추출합니다.

    예: safe_extract_attr(response, 'usage', 'total_tokens', default=0)
    """
    current = obj
    for attr in attrs:
        if not hasattr(current, attr):
            return default
        current = getattr(current, attr)
    return current if current is not None else default
