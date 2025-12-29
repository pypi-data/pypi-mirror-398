"""
Nora Observability SDK
AI 라이브러리 호출을 자동으로 trace하는 Observability 서비스

사용법:
    import nora

    # 방법 1: init()으로 한 번만 설정
    nora.init(api_key="YOUR_KEY")
    client = nora.Client()  # api_key 자동 사용

    # 방법 2: 직접 api_key 전달
    client = nora.Client(api_key="YOUR_KEY")
    # 또는
    client = nora.NoraClient(api_key="YOUR_KEY")

    # 이제 OpenAI, Anthropic 등의 호출이 자동으로 trace됩니다!
"""

from typing import Optional, List
from .client import NoraClient

# 전역 설정 저장
_global_config: dict = {}


def init(
    api_key: str,
    api_url: str = "https://noraobservabilitybackend-staging.up.railway.app/v1",
    thread_id: Optional[str] = None,
    user_id: Optional[str] = None,
    traced_functions: Optional[List[str]] = None,
    **kwargs,
) -> None:
    """
    Nora SDK를 전역으로 초기화합니다.
    init()으로 설정한 후에는 nora.Client()를 api_key 없이 호출할 수 있습니다.

    Args:
        api_key: Nora API 키
        api_url: Trace 데이터를 전송할 API 엔드포인트 URL (프롬프트 API도 동일하게 사용됨)
        thread_id: 스레드/세션 ID (옵션)
        user_id: 사용자 ID (옵션)
        traced_functions: 자동으로 trace_group으로 감쌀 함수 이름 리스트
        **kwargs: NoraClient의 다른 파라미터들 (batch_size, flush_interval 등)
    """
    global _global_config
    
    _global_config = {
        "api_key": api_key,
        "api_url": api_url,
        **kwargs
    }
    
    if thread_id is not None:
        _global_config["thread_id"] = thread_id
    if user_id is not None:
        _global_config["user_id"] = user_id

    # traced_functions가 있으면 별도로 저장 (클라이언트 생성 후 적용)
    if traced_functions:
        _global_config["traced_functions"] = traced_functions
    
    # 전역 클라이언트 인스턴스 생성
    global _global_client
    _global_client = NoraClient(**_global_config)
    
    # Return client instance for API compatibility
    return _global_client


# 전역 클라이언트 인스턴스
_global_client: Optional[NoraClient] = None


def trace_group(name: Optional[str] = None, metadata: Optional[dict] = None):
    """
    여러 LLM 호출을 하나의 논리적 그룹으로 묶습니다.
    
    nora.init()을 먼저 호출해야 합니다.
    
    Context manager 또는 데코레이터로 사용 가능합니다.
    
    Args:
        name: 그룹 이름 (데코레이터 사용 시 기본값: 함수 이름)
        metadata: 그룹 메타데이터
    
    예제 (Context Manager):
        >>> with nora.trace_group("multi_agent_workflow"):
        ...     response = client.chat.completions.create(...)
    
    예제 (데코레이터):
        >>> @nora.trace_group(name="batch_process")
        ... def generate():
        ...     return client.chat.completions.create(...)
    """
    if _global_client is None:
        raise RuntimeError("nora.init() must be called before using trace_group")
    return _global_client.trace_group(name=name, metadata=metadata)


# Client를 NoraClient의 별칭으로 export
Client = NoraClient

__version__ = "1.0.24"

__all__ = [
    "NoraClient",
    "Client",
    "init",
    "trace_group",
    "__version__",
]
