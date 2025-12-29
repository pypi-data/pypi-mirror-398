"""
Nora Observability Client
자동으로 AI 라이브러리 호출을 trace하고 API로 전송합니다.
"""

import time
import threading
import inspect
import queue
from typing import Optional, Dict, Any, List, Callable, TypeVar, Union
from datetime import datetime
import uuid
from contextvars import ContextVar
from functools import wraps

try:
    import requests
except ImportError:
    requests = None


# Context variables for trace grouping and client tracking
_current_trace_group: ContextVar[Optional["TraceGroup"]] = ContextVar(
    "_current_trace_group", default=None
)
_current_client: ContextVar[Optional["NoraClient"]] = ContextVar("_current_client", default=None)
_current_execution_span: ContextVar[Optional[Dict[str, Any]]] = ContextVar(
    "_current_execution_span", default=None
)

# 클라이언트 레지스트리 (여러 인스턴스 지원)
_client_registry: List["NoraClient"] = []
_registry_lock = threading.Lock()

# Context variable for tracking current agent (for nested agent function calls)
_current_agent_context: ContextVar[Optional[str]] = ContextVar(
    "_current_agent_context", default=None
)

F = TypeVar("F", bound=Callable[..., Any])


class TraceGroup:
    """
    여러 LLM 호출을 하나의 논리적 그룹으로 묶는 컨텍스트.

    Context manager 또는 데코레이터로 사용 가능합니다.

    사용법 (Context Manager):
        with client.trace_group(name="multi_agent_pipeline"):
            # 이 블록 안의 모든 LLM 호출이 그룹으로 묶임
            response1 = client.chat.completions.create(...)
            response2 = client.chat.completions.create(...)

    사용법 (데코레이터):
        @client.trace_group(name="batch_process")
        async def generate():
            async for chunk in agent.streaming():
                yield chunk
    """

    def __init__(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None,
        client: Optional["NoraClient"] = None,
    ):
        self.group_id = str(uuid.uuid4())
        self.trace_id = None  # External API trace ID
        self.name = name
        self.metadata = metadata or {}
        self.start_time = None
        self.end_time = None
        self.traces = []
        self.execution_span_ids = []  # Track ExecutionSpan IDs for decision linking
        self._prev_auto_flush = None  # 이전 auto flush 상태 저장
        self._prev_trace_group = None  # 이전 trace_group 저장 (중첩 지원)
        self._client = client  # 연결된 클라이언트 인스턴스

    def _aggregate_output(self) -> str:
        """Aggregate output from all traces in the group."""
        outputs = [trace.get("response", "") for trace in self.traces if trace.get("response")]
        return "\n".join(outputs) if outputs else ""

    def _aggregate_tokens(self) -> Dict[str, int]:
        """Aggregate token usage from all traces in the group."""
        total_tokens = 0
        prompt_tokens = 0
        completion_tokens = 0

        for trace in self.traces:
            tokens = trace.get("tokens_used")
            if tokens is None:
                tokens = 0
            total_tokens += tokens

            # Try to extract detailed token info from metadata if available
            metadata = trace.get("metadata", {})
            response_info = metadata.get("response", {})
            usage = response_info.get("usage", {})

            if usage:
                prompt_tokens += usage.get("prompt_tokens", 0)
                completion_tokens += usage.get("completion_tokens", 0)

        return {
            "total_tokens": total_tokens,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        }

    def _calculate_cost(self) -> float:
        """Calculate total cost from all traces in the group."""
        # This is a placeholder - actual cost calculation would depend on provider pricing
        # You can implement custom cost calculation logic here
        return 0.0

    def __enter__(self):
        self.start_time = time.time()
        # 이전 trace_group 저장 (중첩 지원)
        self._prev_trace_group = _current_trace_group.get()
        _current_trace_group.set(self)

        # 클라이언트 가져오기 (인스턴스 또는 활성 클라이언트)
        client = self._client or _get_active_client()
        if client:
            self.trace_id = client._create_pending_trace(self.name, self.metadata)
            self._prev_auto_flush = getattr(client, "_auto_flush_enabled", True)
            client._auto_flush_enabled = False

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        # 이전 trace_group 복원 (중첩 지원)
        _current_trace_group.set(self._prev_trace_group)

        # 클라이언트 가져오기 (인스턴스 또는 활성 클라이언트)
        client = self._client or _get_active_client()

        # 자동 플러시 재개
        flush_after_exit = False
        if client:
            if self._prev_auto_flush is not None:
                flush_after_exit = self._prev_auto_flush
                client._auto_flush_enabled = self._prev_auto_flush

        # trace_group 종료 시 적체된 trace를 바로 플러시 (데코레이터 사용 시에도 보장)
        if client and flush_after_exit and client._traces:
            client.flush()

        # ⏳ Wait for all ExecutionSpans to be sent BEFORE updating trace status
        if client:
            client._execution_span_manager.wait_for_completion(timeout=5.0)

        # Auto-aggregate decisions on trace_group exit
        if client:
            try:
                client._decision_manager._build_and_send_agent_answer_decisions()
            except Exception as e:
                print(f"[Nora] ⚠️ Decision aggregation failed: {e}")

        # Now update trace to success status (AFTER all spans are sent)
        if client and self.trace_id:
            status = "error" if exc_type is not None else "success"
            # Aggregate data from all traces in the group
            output = self._aggregate_output()
            tokens = self._aggregate_tokens()
            cost = self._calculate_cost()

            client._update_trace_status(
                self.trace_id,
                status,
                self.start_time,
                self.end_time,
                output=output,
                tokens=tokens,
                cost=cost,
            )

        return False  # 예외를 재발생시킴

    async def __aenter__(self):
        """비동기 context manager 진입."""
        self.start_time = time.time()
        # 이전 trace_group 저장 (중첩 지원)
        self._prev_trace_group = _current_trace_group.get()
        _current_trace_group.set(self)

        # 클라이언트 가져오기 (인스턴스 또는 활성 클라이언트)
        client = self._client or _get_active_client()
        if client:
            self.trace_id = client._create_pending_trace(self.name, self.metadata)
            self._prev_auto_flush = getattr(client, "_auto_flush_enabled", True)
            client._auto_flush_enabled = False

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 context manager 종료."""
        self.end_time = time.time()
        # 이전 trace_group 복원 (중첩 지원)
        _current_trace_group.set(self._prev_trace_group)

        # 클라이언트 가져오기 (인스턴스 또는 활성 클라이언트)
        client = self._client or _get_active_client()

        # 자동 플러시 재개
        flush_after_exit = False
        if client:
            if self._prev_auto_flush is not None:
                flush_after_exit = self._prev_auto_flush
                client._auto_flush_enabled = self._prev_auto_flush

        # 그룹 요약 정보 생성
        if self.traces:
            if client:
                # 각 trace에 그룹 정보 추가
                for trace in self.traces:
                    if trace.get("metadata") is None:
                        trace["metadata"] = {}
                    trace["metadata"]["trace_group"] = {
                        "id": self.group_id,
                        "name": self.name,
                        "metadata": self.metadata,
                    }

        # 비동기 컨텍스트 종료 시에도 적체된 trace를 즉시 플러시
        if client and flush_after_exit and client._traces:
            client.flush()

        # ⏳ Wait for all ExecutionSpans to be sent BEFORE updating trace status
        if client:
            client._execution_span_manager.wait_for_completion(timeout=5.0)

        # Auto-aggregate decisions on trace_group exit
        if client:
            try:
                client._decision_manager._build_and_send_agent_answer_decisions()
            except Exception as e:
                print(f"[Nora] ⚠️ Decision aggregation failed: {e}")

        # Now update trace to success status (AFTER all spans are sent)
        if client and self.trace_id:
            status = "error" if exc_type is not None else "success"
            # Aggregate data from all traces in the group
            output = self._aggregate_output()
            tokens = self._aggregate_tokens()
            cost = self._calculate_cost()

            client._update_trace_status(
                self.trace_id,
                status,
                self.start_time,
                self.end_time,
                output=output,
                tokens=tokens,
                cost=cost,
            )

        return False  # 예외를 재발생시킴

    def __call__(self, func: F) -> F:
        """데코레이터로 사용될 때 호출됩니다."""
        group_name = self.name
        group_metadata = self.metadata

        def _new_group() -> "TraceGroup":
            meta_copy = dict(group_metadata) if isinstance(group_metadata, dict) else group_metadata
            return TraceGroup(name=group_name, metadata=meta_copy, client=self._client)

        # Async generator
        if inspect.isasyncgenfunction(func):

            @wraps(func)
            async def async_gen_wrapper(*args, **kwargs):
                group = _new_group()
                async with group:
                    async for item in func(*args, **kwargs):
                        yield item

            return async_gen_wrapper  # type: ignore

        # Generator
        elif inspect.isgeneratorfunction(func):

            @wraps(func)
            def gen_wrapper(*args, **kwargs):
                group = _new_group()
                with group:
                    yield from func(*args, **kwargs)

            return gen_wrapper  # type: ignore

        # Async function
        elif inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                group = _new_group()
                
                # Enter context FIRST to set _current_trace_group for child functions
                async with group:
                    # Check if function returns StreamingResponse before entering context
                    result = await func(*args, **kwargs)
                    
                    # FastAPI StreamingResponse 감지: 제너레이터를 trace_group 안에서 실행
                    if hasattr(result, 'body_iterator') and inspect.isasyncgen(result.body_iterator):
                        # 원본 제너레이터를 같은 trace_group 컨텍스트로 감싸기
                        original_gen = result.body_iterator
                        
                        async def traced_gen():
                            async with group:
                                async for chunk in original_gen:
                                    yield chunk
                        
                        result.body_iterator = traced_gen()
                        return result
                    else:
                        # 일반 함수: 기존 방식대로 처리
                        return result

            return async_wrapper  # type: ignore

        # Sync function
        else:

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                group = _new_group()
                
                # Check if function returns StreamingResponse before entering context
                result = func(*args, **kwargs)
                
                # StreamingResponse 감지 (동기 버전)
                if hasattr(result, 'body_iterator') and inspect.isgenerator(result.body_iterator):
                    original_gen = result.body_iterator
                    
                    def traced_gen():
                        with group:
                            yield from original_gen
                    
                    result.body_iterator = traced_gen()
                    return result
                else:
                    # 일반 함수: 기존 방식대로 처리
                    with group:
                        return result

            return sync_wrapper  # type: ignore


class NoraClient:
    """
    Nora Observability 클라이언트

    Trace 데이터를 수집하고 배치로 API에 전송합니다.

    사용법:
        client = NoraClient(api_key="your-api-key")
        client.patch()  # AI 라이브러리 자동 패치

        # 또는 편의 함수 사용
        client = nora.init(api_key="your-api-key")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        batch_size: int = 10,
        flush_interval: float = 5.0,
        service_url: Optional[str] = None,
        environment: str = "default",
        semantics: Optional[Dict[str, Dict[str, List[str]]]] = None,
        agent_map: Optional[Dict[str, List[str]]] = None,
        auto_patch: bool = True,
        traced_functions: Optional[List[str]] = None,
        thread_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        """
        Args:
            api_key: Nora API 키 (없으면 nora.init()으로 설정한 전역 설정 사용)
            api_url: Trace 데이터를 전송할 API 엔드포인트 URL (없으면 전역 설정 사용)
            batch_size: 한 번에 전송할 trace 개수 (기본값: 10)
            flush_interval: 자동 전송 간격(초) (기본값: 5.0)
            service_url: 외부 서비스 URL (선택사항, 나중에 외부 API 호출에 사용)
            environment: 환경 정보 (기본값: "default")
            semantics: span_kind 추론용 매핑 (예: {"retrieval": {"functions": [...], "classes": [...], "tools": [...]}})
            agent_map: 함수→에이전트 매핑 (예: {"research_agent": ["search_papers", "fetch_data"], "analysis_agent": [...]})
            auto_patch: 자동으로 AI 라이브러리를 패치할지 여부 (기본값: True)
            traced_functions: 자동으로 trace_group으로 감쌀 함수 이름 리스트
            thread_id: 스레드/세션 ID (선택사항)
            user_id: 사용자 ID (선택사항)
        """
        # 전역 설정에서 가져오기 (없으면 기본값 사용)
        from . import _global_config

        if api_key is None:
            if not _global_config or "api_key" not in _global_config:
                raise ValueError(
                    "api_key가 제공되지 않았습니다. "
                    "nora.init(api_key='...')를 먼저 호출하거나 "
                    "nora.Client(api_key='...')로 직접 전달해주세요."
                )
            api_key = _global_config["api_key"]

        if api_url is None:
            api_url = _global_config.get(
                "api_url", "https://noraobservabilitybackend-staging.up.railway.app/v1"
            )

        # 전역 설정의 다른 파라미터들도 적용 (명시적으로 전달되지 않은 경우만)
        if batch_size == 10 and "batch_size" in _global_config:
            batch_size = _global_config["batch_size"]
        if flush_interval == 5.0 and "flush_interval" in _global_config:
            flush_interval = _global_config["flush_interval"]
        if service_url is None and "service_url" in _global_config:
            service_url = _global_config["service_url"]
        if environment == "default" and "environment" in _global_config:
            environment = _global_config["environment"]
        if semantics is None and "semantics" in _global_config:
            semantics = _global_config["semantics"]
        if agent_map is None and "agent_map" in _global_config:
            agent_map = _global_config["agent_map"]
        if auto_patch and "auto_patch" in _global_config:
            auto_patch = _global_config["auto_patch"]
        if traced_functions is None and "traced_functions" in _global_config:
            traced_functions = _global_config["traced_functions"]
        if thread_id is None and "thread_id" in _global_config:
            thread_id = _global_config["thread_id"]
        if user_id is None and "user_id" in _global_config:
            user_id = _global_config["user_id"]

        self.api_key = api_key
        self.api_url = api_url
        self.trace_create_url = f"{api_url}/traces/"
        self.execution_span_url = f"{api_url}/executions/"
        self.decision_create_url = f"{api_url}/decision/"
        self.service_url = service_url
        self.environment = environment
        self.semantics = semantics or {}
        self.agent_map = agent_map or {}
        self.project_id: Optional[str] = None
        self.organization_id: Optional[str] = None
        self.thread_id = thread_id
        self.user_id = user_id
        self.enabled = True
        self._auto_flush_enabled = True  # trace_group에서 제어 가능

        self._traces: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._batch_size = batch_size
        self._flush_interval = flush_interval
        self._last_flush = time.time()
        self._patched = False

        # 클라이언트 레지스트리에 등록
        with _registry_lock:
            _client_registry.append(self)

        # 자동 패치
        if auto_patch:
            self.patch()

        # traced_functions 자동 설정
        if traced_functions:
            self._setup_traced_functions(traced_functions)

        # Decision 및 Execution Span 관리자 초기화
        from ._internal.decisions import DecisionManager
        from ._internal.execution_span import ExecutionSpanManager

        self._decision_manager = DecisionManager(self)
        self._execution_span_manager = ExecutionSpanManager(self)

        # Execution Span Manager의 execution_ids에 접근하기 위한 속성
        self._trace_execution_ids = self._execution_span_manager._trace_execution_ids
        self._trace_exec_lock = self._execution_span_manager._trace_exec_lock

        # Prompt API 초기화
        from .prompt import PromptAPI
        self.prompt = PromptAPI(self)

        # DataSet API 초기화
        from .data_set import DataSetAPI
        self.dataset = DataSetAPI(self)

    def _match_semantics(
        self,
        category: str,
        function_name: Optional[str],
        class_name: Optional[str],
        tool_names: List[str],
    ) -> bool:
        cfg = self.semantics.get(category, {})
        if function_name and function_name in cfg.get("functions", []):
            return True
        if class_name and class_name in cfg.get("classes", []):
            return True
        if any(t in cfg.get("tools", []) for t in tool_names):
            return True
        return False

    def _resolve_span_kind(
        self,
        span_kind: Optional[str],
        metadata: Optional[Dict[str, Any]],
        tool_calls: Optional[List[Dict[str, Any]]],
        provider: Optional[str],
        model: Optional[str],
    ) -> Optional[str]:
        # User-specified span_kind wins (free-form)
        if span_kind is not None:
            return span_kind

        md = metadata or {}
        function_name = md.get("function_name") if isinstance(md, dict) else None
        class_name = md.get("class_name") if isinstance(md, dict) else None
        tool_names = [
            tc.get("name") for tc in (tool_calls or []) if isinstance(tc, dict) and tc.get("name")
        ]

        # Semantics-based inference (optional)
        for category in ("retrieval", "router", "policy_eval"):
            if self._match_semantics(category, function_name, class_name, tool_names):
                return category

        # Default inference when nothing matches
        if tool_names:
            return "tool"
        if provider or model:
            return "llm"
        return None

    def _trace_method(
        self,
        provider: str,
        model: str,
        prompt: Optional[str] = None,
        response: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        tokens_used: Optional[int] = None,
        error: Optional[str] = None,
        finish_reason: Optional[str] = None,
        response_id: Optional[str] = None,
        system_fingerprint: Optional[str] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        span_kind: Optional[str] = None,
        **extra_fields,
    ) -> None:
        """
        Trace 데이터를 수집합니다.

        Args:
            provider: AI 제공자 (openai, anthropic, etc.)
            model: 사용된 모델 이름
            prompt: 입력 프롬프트
            response: 응답 내용
            metadata: 추가 메타데이터
            start_time: 요청 시작 시간 (timestamp)
            end_time: 요청 종료 시간 (timestamp)
            tokens_used: 사용된 토큰 수
            error: 에러 메시지 (있는 경우)
            finish_reason: 완료 이유 (stop, length, tool_calls, etc.)
            response_id: API 응답 ID
            system_fingerprint: 시스템 fingerprint
            tool_calls: Tool/Function calls 정보
            span_kind: 사용자 지정 가능. 기본 추론 순서: semantics 매칭 → tool_calls 감지 시 "tool" → provider/model 존재 시 "llm" → 그 외 None
            **extra_fields: 추가 필드 (확장성)
        """
        if not self.enabled:
            return

        resolved_span_kind = self._resolve_span_kind(
            span_kind=span_kind,
            metadata=metadata,
            tool_calls=tool_calls,
            provider=provider,
            model=model,
        )

        trace_data = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "provider": provider,
            "model": model,
            "prompt": prompt,
            "response": response,
            "metadata": metadata or {},
            "start_time": start_time,
            "end_time": end_time,
            "duration": (end_time - start_time) if (start_time and end_time) else None,
            "tokens_used": tokens_used,
            "error": error,
            "finish_reason": finish_reason,
            "response_id": response_id,
            "system_fingerprint": system_fingerprint,
            "tool_calls": tool_calls,
            "environment": self.environment,
            "span_kind": resolved_span_kind,
        }

        # 추가 필드 병합
        trace_data.update(extra_fields)

        # 현재 활성화된 trace group 정보 추가
        current_group = _get_current_trace_group()

        if current_group:
            if trace_data["metadata"] is None:
                trace_data["metadata"] = {}
            trace_data["metadata"]["trace_group"] = {
                "id": current_group.group_id,
                "name": current_group.name,
            }
            current_group.traces.append(trace_data)
            # TraceGroup에 클라이언트 연결 (없는 경우)
            if not current_group._client:
                current_group._client = self

            # Also keep a copy in client-level traces for aggregation APIs
            with self._lock:
                self._traces.append(trace_data)

            # Send execution span immediately if trace_id exists
            # send_execution_span will extract execution_id from API response and store it
            if current_group.trace_id:
                self._execution_span_manager.send_execution_span(current_group.trace_id, trace_data)

                # Capture atomic decision for LLM tool calling
                self._decision_manager._maybe_capture_llm_tool_decision(
                    trace_data=trace_data,
                    trace_group_id=current_group.group_id,
                    trace_id=current_group.trace_id,
                )
            else:
                print("[Nora] ⚠️  WARNING: trace_id is None, cannot send execution span")
        else:
            # No trace_group: use old batch behavior
            with self._lock:
                self._traces.append(trace_data)

                # trace_group 내부에서는 자동 플러시 비활성화
                if not self._auto_flush_enabled:
                    return

                # 배치 크기나 시간 간격에 따라 자동 전송
                should_flush = (
                    len(self._traces) >= self._batch_size
                    or (time.time() - self._last_flush) >= self._flush_interval
                )

                if should_flush:
                    self._flush()

            # After standard trace handling, decisions aggregation can be scheduled on flush only

    def _flush(self, sync: bool = False) -> None:
        """수집된 trace 데이터를 API로 전송합니다.

        Args:
            sync: True면 동기적으로 전송 (기본값: False, 비동기 전송)
        """
        if not self._traces:
            return

        if not requests:
            # requests가 없으면 경고 출력 (한 번만)
            if not hasattr(self, "_warned_no_requests"):
                print("[Nora] Warning: 'requests' library not found. Install it to send traces.")
                self._warned_no_requests = True
            return

        traces_to_send = self._traces.copy()
        self._traces.clear()
        self._last_flush = time.time()

        if sync:
            # 동기적으로 전송 (테스트용)
            self._send_traces(traces_to_send)
        else:
            # 비동기로 전송 (메인 스레드 블로킹 방지)
            thread = threading.Thread(target=self._send_traces, args=(traces_to_send,), daemon=True)
            thread.start()

        # Wait for any pending execution span threads to complete
        self._execution_span_manager.wait_for_completion(timeout=2.0)

        # After traces are sent, aggregate decisions (agent/answer) in background
        try:
            self._decision_manager._build_and_send_agent_answer_decisions()
        except Exception as e:
            print(f"[Nora] ⚠️ Decision aggregation failed: {e}")

    def _create_pending_trace(
        self, trace_name: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Create a pending trace and return trace_id.

        Args:
            trace_name: Name of the trace
            metadata: Additional metadata for the trace

        Returns:
            trace_id from API response, or None if failed
        """
        if not requests:
            return None

        try:
            headers = {
                "X-API-Key": self.api_key,
                "Content-Type": "application/json",
            }

            # Build payload with required fields
            payload = {
                "trace_name": trace_name,
                "input": metadata.get("input", "") if metadata else "",
                "environment": self.environment,
            }

            # Add project_id if available
            if self.project_id:
                payload["project_id"] = self.project_id

            if self.thread_id:
                payload["thread_id"] = self.thread_id
            if self.user_id:
                payload["user_id"] = self.user_id
            
            # metadata에 type 필드가 있으면 파라미터로 추가
            if metadata:
                if isinstance(metadata, dict) and "type" in metadata:
                    payload["type"] = metadata["type"]
                elif hasattr(metadata, "type"):
                    payload["type"] = metadata.type
                    
            response = requests.post(
                self.trace_create_url, json=payload, headers=headers, timeout=10
            )

            if response.status_code in (200, 201):
                response_data = response.json()

                # Get trace_id from 'id' field in response
                trace_id = response_data.get("id")

                if not trace_id:
                    print(f"[Nora] ❌ ERROR: 'id' not found in response. Response: {response_data}")
                    return None

                return trace_id
            else:
                print(f"[Nora] ⚠️  Warning: Failed to create trace (status: {response.status_code})")
                return None

        except requests.exceptions.RequestException as e:
            print(f"[Nora] ❌ Error creating trace: {str(e)}")
            return None
        except Exception as e:
            print(f"[Nora] ❌ Unexpected error creating trace: {str(e)}")
            return None

    def _update_trace_status(
        self,
        trace_id: str,
        status: str,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        output: Optional[str] = None,
        tokens: Optional[Dict[str, int]] = None,
        cost: Optional[float] = None,
    ) -> None:
        """Update trace status to success or error.

        Args:
            trace_id: The trace ID to update
            status: New status (success, error)
            start_time: Trace start time
            end_time: Trace end time
            output: Aggregated output from all spans
            tokens: Token usage information
            cost: Total cost
        """
        if not requests or not trace_id:
            return

        try:
            headers = {
                "X-API-Key": self.api_key,
                "Content-Type": "application/json",
            }

            # Build URL with trace_id dynamically
            update_url = f"{self.api_url}/traces/{trace_id}"

            # Build payload with required fields
            payload = {
                "status": status,
            }

            # Add optional fields
            if output:
                payload["output"] = output

            if start_time and end_time:
                payload["latency"] = end_time - start_time

            if cost is not None:
                payload["cost"] = cost

            if tokens:
                payload["tokens"] = tokens

            response = requests.patch(update_url, json=payload, headers=headers, timeout=10)


        except requests.exceptions.RequestException as e:
            print(f"[Nora] ❌ Error updating trace: {str(e)}")
        except Exception as e:
            print(f"[Nora] ❌ Unexpected error updating trace: {str(e)}")

    def _parse_input_from_span(self, span_data: Dict[str, Any]) -> Optional[str]:
        """Try to extract a sensible `input` string from an execution span.

        Heuristics (in order):
        1. `metadata.request.parameters.input`
        2. `metadata.input`
        3. `prompt` field on span
        4. `metadata.request.messages` -> join `user` messages or take first message content
        Returns None when no candidate found.
        """
        try:
            if not isinstance(span_data, dict):
                return None

            md = span_data.get("metadata") or {}

            # 1) metadata.request.parameters.input
            try:
                req_params = (md.get("request") or {}).get("parameters")
                if isinstance(req_params, dict):
                    inp = req_params.get("input")
                    if inp:
                        return inp if isinstance(inp, str) else str(inp)
            except Exception:
                pass

            # 2) metadata.input
            try:
                if isinstance(md, dict) and md.get("input"):
                    return (
                        md.get("input")
                        if isinstance(md.get("input"), str)
                        else str(md.get("input"))
                    )
            except Exception:
                pass

            # 3) prompt field
            try:
                if span_data.get("prompt"):
                    return (
                        span_data.get("prompt")
                        if isinstance(span_data.get("prompt"), str)
                        else str(span_data.get("prompt"))
                    )
            except Exception:
                pass

            # 4) metadata.request.messages (common OpenAI shape)
            try:
                msgs = (md.get("request") or {}).get("messages")
                if isinstance(msgs, list) and msgs:
                    user_parts = []
                    for m in msgs:
                        if isinstance(m, dict):
                            role = m.get("role")
                            content = m.get("content") or m.get("text") or m.get("value")
                            if role == "user" and content:
                                user_parts.append(content)
                    if user_parts:
                        return "\n".join(user_parts)

                    # fallback: first message content
                    for m in msgs:
                        if isinstance(m, dict):
                            content = m.get("content") or m.get("text")
                            if content:
                                return content
            except Exception:
                pass

            return None
        except Exception:
            return None

    def _update_trace_input(self, trace_id: str, input_value: str) -> None:
        """Patch only the `input` field of an existing trace.

        This method performs a focused PATCH containing only the `input` key so
        that other trace fields are not modified.
        """
        if not requests or not trace_id or input_value is None:
            return

        try:
            headers = {
                "X-API-Key": self.api_key,
                "Content-Type": "application/json",
            }

            update_url = f"{self.api_url}/traces/{trace_id}"
            payload = {"input": input_value}

            response = requests.patch(update_url, json=payload, headers=headers, timeout=10)

        except requests.exceptions.RequestException as e:
            print(f"[Nora] ❌ Error updating trace input: {str(e)}")
        except Exception as e:
            print(f"[Nora] ❌ Unexpected error updating trace input: {str(e)}")

    def _send_execution_span(self, trace_id: str, span_data: Dict[str, Any]) -> None:
        """Send execution span immediately to API and capture execution_id.

        Delegates to ExecutionSpanManager.
        """
        self._execution_span_manager.send_execution_span(trace_id, span_data)
        
        # Check if this span should create an atomic decision
        current_group = _current_trace_group.get()
        if current_group:
            self._decision_manager._maybe_capture_execution_decision(
                span_data, current_group.group_id, trace_id
            )

    def _send_traces(self, traces: List[Dict[str, Any]]) -> None:
        """실제 API로 trace 데이터를 전송합니다.

        Note: 개별 execution span은 이미 _send_execution_span()으로 전송되었으므로,
        여기서는 batch aggregation이나 메타데이터 업데이트만 필요하면 구현.
        현재는 no-op.
        """
        if not traces:
            return

        # ExecutionSpan이 개별적으로 전송되므로, batch 전송은 스킵

    # =========================
    # Decision span collection
    # =========================

    def _maybe_capture_llm_tool_decision(
        self,
        trace_data: Dict[str, Any],
        trace_group_id: Optional[str],
        trace_id: Optional[str],
    ) -> None:
        """Capture atomic decision when LLM is called with tools. Delegates to DecisionManager."""
        self._decision_manager._maybe_capture_llm_tool_decision(
            trace_data, trace_group_id, trace_id
        )

    def _maybe_capture_decision(
        self,
        func_name: str,
        result: Any,
        trace_group_id: Optional[str],
        execution_span_ids: Optional[List[str]] = None,
    ) -> None:
        """If semantics marks func_name as retrieval, extract decision and enqueue Atomic DecisionSpan.

        Delegates to DecisionManager.
        """
        self._decision_manager._maybe_capture_decision(
            func_name, result, trace_group_id, execution_span_ids
        )

    def flush(self, sync: bool = False) -> None:
        """수동으로 trace 데이터를 즉시 전송합니다.

        Args:
            sync: True면 동기적으로 전송 (기본값: False, 비동기 전송)
        """
        with self._lock:
            self._flush(sync=sync)

    def disable(self) -> None:
        """Trace 기능을 비활성화합니다."""
        self.flush()  # 비활성화 전에 남은 데이터 전송
        self.enabled = False

    def enable(self) -> None:
        """Trace 기능을 활성화합니다."""
        self.enabled = True

    def find_traces_by_group(self, group_name: str) -> List[Dict[str, Any]]:
        """특정 trace group 이름으로 수집된 모든 traces를 검색합니다."""
        matching_traces = []
        with self._lock:
            for trace in self._traces:
                group_info = trace.get("metadata", {}).get("trace_group", {})
                if group_info.get("name") == group_name:
                    matching_traces.append(trace)
        return matching_traces

    def find_traces_by_group_id(self, group_id: str) -> List[Dict[str, Any]]:
        """특정 trace group ID로 수집된 모든 traces를 검색합니다."""
        matching_traces = []
        with self._lock:
            for trace in self._traces:
                group_info = trace.get("metadata", {}).get("trace_group", {})
                if group_info.get("id") == group_id:
                    matching_traces.append(trace)
        return matching_traces

    def get_trace_groups(self) -> List[Dict[str, Any]]:
        """현재 수집된 모든 trace group 정보를 반환합니다."""
        groups_dict = {}
        with self._lock:
            for trace in self._traces:
                group_info = trace.get("metadata", {}).get("trace_group", {})
                if group_info:
                    group_id = group_info.get("id")
                    if group_id and group_id not in groups_dict:
                        groups_dict[group_id] = {
                            "id": group_id,
                            "name": group_info.get("name"),
                            "metadata": group_info.get("metadata", {}),
                            "trace_count": 0,
                            "total_tokens": 0,
                            "total_duration": 0.0,
                            "trace_ids": [],
                        }
                    if group_id:
                        groups_dict[group_id]["trace_count"] += 1
                        tokens = trace.get("tokens_used") or 0
                        groups_dict[group_id]["total_tokens"] += tokens
                        groups_dict[group_id]["trace_ids"].append(trace.get("id"))
                        duration = trace.get("duration") or 0.0
                        groups_dict[group_id]["total_duration"] += duration
        return list(groups_dict.values())

    def patch(self) -> None:
        """AI 라이브러리를 패치하여 자동 trace를 활성화합니다."""
        if self._patched:
            return

        from ._internal.patches import apply_all_patches

        # 현재 클라이언트를 활성화
        _current_client.set(self)
        try:
            apply_all_patches()
            self._patched = True
        finally:
            # ContextVar는 자동으로 복원되므로 명시적 복원 불필요
            pass

    def _setup_traced_functions(self, function_names: List[str]) -> None:
        """
        지정된 함수들을 자동으로 trace_group으로 감쌉니다.

        Args:
            function_names: 감쌀 함수 이름 리스트
        """
        import sys
        import types

        # 모든 모듈을 순회하면서 함수 찾기
        for module_name, module in sys.modules.items():
            if module is None:
                continue

            # 내장 모듈이나 특수 모듈은 건너뛰기
            if module_name.startswith("_") or not hasattr(module, "__dict__"):
                continue

            for func_name in function_names:
                if hasattr(module, func_name):
                    func = getattr(module, func_name)

                    # 함수인지 확인하고, 이미 래핑되지 않았는지 확인
                    if callable(func) and not hasattr(func, "_nora_traced"):
                        try:
                            # trace_group 데코레이터 적용
                            wrapped = self.trace_group(name=func_name)(func)
                            wrapped._nora_traced = True  # 중복 래핑 방지
                            setattr(module, func_name, wrapped)
                        except Exception as e:
                            # 함수 래핑 실패 시 경고만 출력하고 계속 진행
                            print(
                                f"[Nora] ⚠️  Failed to wrap function {func_name} in {module_name}: {e}"
                            )

    def trace_group(
        self,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TraceGroup:
        """
        여러 LLM 호출을 하나의 논리적 그룹으로 묶습니다.

        Context manager 또는 데코레이터로 사용 가능합니다.

        Args:
            name: 그룹 이름 (데코레이터 사용 시 기본값: 함수 이름)
            metadata: 그룹 메타데이터

        Returns:
            TraceGroup 객체 (context manager이자 데코레이터)

        예제 (Context Manager):
            >>> with client.trace_group("multi_agent_workflow"):
            ...     response1 = client.chat.completions.create(...)
            ...     response2 = client.chat.completions.create(...)

        예제 (데코레이터):
            >>> @client.trace_group(name="batch_process")
            ... async def generate():
            ...     async for chunk in agent.streaming():
            ...         yield chunk
        """
        if name is None:
            # 데코레이터로 사용될 때를 위한 팩토리 함수
            def decorator(func: Callable) -> Callable:
                group = TraceGroup(name=func.__name__, metadata=metadata, client=self)
                return group(func)

            return decorator

        return TraceGroup(name=name, metadata=metadata, client=self)

    def trace(self, func: Optional[F] = None, span_kind: Optional[str] = None) -> Union[F, Callable[[F], F]]:
        """
        함수 실행을 trace하는 데코레이터.

        - 동기/비동기 함수, 동기/비동기 제너레이터 모두 지원
        - trace_group 컨텍스트 내에서만 execution span을 생성
        """
        if func is None:
            return lambda f: self.trace(f, span_kind=span_kind)

        def _build_span_data(fn: Callable, args: tuple, kwargs: dict) -> Dict[str, Any]:
            span_id = str(uuid.uuid4())
            span_data = {
                "id": span_id,
                "name": fn.__name__,
                "start_time": time.time(),
                "span_kind": span_kind,
                "metadata": {
                    "function": fn.__name__,
                    "module": fn.__module__,
                },
            }
            try:
                import inspect
                sig = inspect.signature(fn)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                span_data["input"] = dict(bound_args.arguments)
            except Exception:
                span_data["input"] = {"args": args, "kwargs": kwargs}
            return span_data

        async def _async_finalize_and_send(span_data: Dict[str, Any], trace_id: str, status: str, error: Optional[Exception] = None, result: Any = None) -> None:
            span_data["end_time"] = time.time()
            span_data["status"] = status
            if error:
                span_data["error"] = str(error)
            # 항상 result 저장 (list/dict 모두 포함, non-serializable은 제외)
            if isinstance(result, (dict, list, str, int, float, bool, type(None))):
                span_data["result"] = result
            elif hasattr(result, '__dict__'):
                # Object인 경우 __dict__를 저장하거나 None
                try:
                    span_data["result"] = str(type(result).__name__)
                except:
                    pass
            # Note: Do NOT copy result['options'] to span_data['options'] separately
            # This causes duplication: both span_data.result.options and span_data.options
            # Decision extraction logic will handle options from result directly
            self._decision_manager._cache_execution_span(span_data)
            self._send_execution_span(trace_id, span_data)

        def _finalize_and_send(span_data: Dict[str, Any], trace_id: str, status: str, error: Optional[Exception] = None, result: Any = None) -> None:
            span_data["end_time"] = time.time()
            span_data["status"] = status
            if error:
                span_data["error"] = str(error)
            # 항상 result 저장 (list/dict 모두 포함, non-serializable은 제외)
            if isinstance(result, (dict, list, str, int, float, bool, type(None))):
                span_data["result"] = result
            elif hasattr(result, '__dict__'):
                # Object인 경우 __dict__를 저장하거나 None
                try:
                    span_data["result"] = str(type(result).__name__)
                except:
                    pass
            # Note: Do NOT copy result['options'] to span_data['options'] separately
            # This causes duplication: both span_data.result.options and span_data.options
            # Decision extraction logic will handle options from result directly
            self._decision_manager._cache_execution_span(span_data)
            self._send_execution_span(trace_id, span_data)

        # Async generator
        if inspect.isasyncgenfunction(func):

            @wraps(func)
            async def async_gen_wrapper(*args, **kwargs):
                current_group = _current_trace_group.get()
                if not (current_group and current_group.trace_id):
                    async for item in func(*args, **kwargs):
                        yield item
                    return

                current_span = _current_execution_span.get()
                span_data = _build_span_data(func, args, kwargs)
                if current_span:
                    span_data["execution_parent_id"] = current_span["id"]
                token = _current_execution_span.set(span_data)

                try:
                    async for item in func(*args, **kwargs):
                        yield item
                    await _async_finalize_and_send(span_data, current_group.trace_id, "completed", result=None)
                except Exception as e:
                    await _async_finalize_and_send(span_data, current_group.trace_id, "error", error=e, result=None)
                    raise
                finally:
                    _current_execution_span.reset(token)

            return async_gen_wrapper  # type: ignore

        # Generator
        if inspect.isgeneratorfunction(func):

            @wraps(func)
            def gen_wrapper(*args, **kwargs):
                current_group = _current_trace_group.get()
                if not (current_group and current_group.trace_id):
                    yield from func(*args, **kwargs)
                    return

                current_span = _current_execution_span.get()
                span_data = _build_span_data(func, args, kwargs)
                if current_span:
                    span_data["execution_parent_id"] = current_span["id"]
                token = _current_execution_span.set(span_data)

                try:
                    yield from func(*args, **kwargs)
                    _finalize_and_send(span_data, current_group.trace_id, "completed", result=None)
                except Exception as e:
                    _finalize_and_send(span_data, current_group.trace_id, "error", error=e, result=None)
                    raise
                finally:
                    _current_execution_span.reset(token)

            return gen_wrapper  # type: ignore

        # Async function
        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                current_group = _current_trace_group.get()
                if not (current_group and current_group.trace_id):
                    return await func(*args, **kwargs)

                current_span = _current_execution_span.get()
                span_data = _build_span_data(func, args, kwargs)
                if current_span:
                    span_data["execution_parent_id"] = current_span["id"]
                token = _current_execution_span.set(span_data)

                try:
                    result = await func(*args, **kwargs)
                    await _async_finalize_and_send(span_data, current_group.trace_id, "completed", result=result)
                    return result
                except Exception as e:
                    await _async_finalize_and_send(span_data, current_group.trace_id, "error", error=e, result=None)
                    raise
                finally:
                    _current_execution_span.reset(token)

            return async_wrapper  # type: ignore

        # Sync function
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_group = _current_trace_group.get()
            if not (current_group and current_group.trace_id):
                return func(*args, **kwargs)

            current_span = _current_execution_span.get()
            span_data = _build_span_data(func, args, kwargs)
            if current_span:
                span_data["execution_parent_id"] = current_span["id"]
            token = _current_execution_span.set(span_data)

            try:
                result = func(*args, **kwargs)
                _finalize_and_send(span_data, current_group.trace_id, "completed", result=result)
                return result
            except Exception as e:
                _finalize_and_send(span_data, current_group.trace_id, "error", error=e, result=None)
                raise
            finally:
                _current_execution_span.reset(token)

        return wrapper

    def __enter__(self):
        """Context manager로 사용할 때 현재 클라이언트를 활성화합니다."""
        _current_client.set(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료 시 클라이언트 비활성화."""
        _current_client.set(None)
        return False

    def __del__(self):
        """소멸 시 레지스트리에서 제거."""
        try:
            with _registry_lock:
                if self in _client_registry:
                    _client_registry.remove(self)
        except Exception:
            pass


# 내부 모듈 함수들 (패치 함수들이 사용)
def _get_active_client() -> Optional[NoraClient]:
    """현재 활성화된 클라이언트 인스턴스를 반환합니다. (내부 사용)

    우선순위:
    1. ContextVar의 현재 클라이언트
    2. 레지스트리의 가장 최근 클라이언트
    """
    # ContextVar에서 현재 클라이언트 확인
    current = _current_client.get()
    if current:
        return current

    # 레지스트리에서 활성화된 클라이언트 찾기
    with _registry_lock:
        if _client_registry:
            return _client_registry[-1]  # 가장 최근에 등록된 클라이언트

    return None


def _get_current_trace_group() -> Optional[TraceGroup]:
    """현재 활성화된 trace group을 반환합니다. (내부 사용)"""
    return _current_trace_group.get()
