"""
Execution Span 전송 모듈
Execution Span 관련 로직을 NoraClient에서 분리
"""

import threading
import queue
import time
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import NoraClient

try:
    import requests
except ImportError:
    requests = None


def _sanitize_for_json(obj: Any) -> Any:
    """Convert Pydantic models and other non-serializable objects to JSON-serializable format."""
    if obj is None:
        return None
    
    # Handle Pydantic models
    if hasattr(obj, 'model_dump'):
        return obj.model_dump()
    elif hasattr(obj, 'dict'):
        return obj.dict()
    
    # Handle dictionaries recursively
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    
    # Handle lists recursively
    if isinstance(obj, (list, tuple)):
        return [_sanitize_for_json(item) for item in obj]
    
    # Handle basic types
    if isinstance(obj, (str, int, float, bool)):
        return obj
    
    # Fallback: try to convert to string
    try:
        # Check if it's JSON serializable
        import json
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return str(obj)


class ExecutionSpanManager:
    """Execution Span 전송을 담당하는 클래스"""

    def __init__(self, client: "NoraClient"):  # type: ignore
        """ExecutionSpanManager 초기화
        
        Args:
            client: NoraClient 인스턴스
        """
        self.client = client

        # Map trace_id -> list of execution_ids
        self._trace_execution_ids: Dict[str, list] = {}
        self._trace_exec_lock = threading.Lock()

        # Queue for ordered, asynchronous sending of execution spans
        self._span_queue: "queue.Queue[tuple[str, Dict[str, Any]]]" = queue.Queue()

        # Worker thread that sends execution spans one-by-one (preserves order)
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()

        # Track active execution span threads (kept for compatibility)
        self._execution_threads: list = []
        self._execution_threads_lock = threading.Lock()

    def send_execution_span(self, trace_id: str, span_data: Dict[str, Any]) -> None:
        """Send execution span immediately to API and capture execution_id."""
        if not requests:
            print("[Nora] ⚠️  WARNING: requests module not available")
            return

        if not trace_id:
            print("[Nora] ⚠️  WARNING: trace_id is empty or None")
            return
        # Enqueue span for ordered asynchronous sending by worker thread
        # Use local id for fallback mapping in worker if needed
        try:
            self._span_queue.put_nowait((trace_id, span_data))
        except Exception:
            # If queueing fails for any reason, fall back to direct send
            self._do_send(trace_id, span_data)

    def wait_for_completion(self, timeout: float = 2.0) -> None:
        """Wait for all pending execution span threads to complete."""
        # Wait for the span queue to be processed (ordered completion)
        start = time.time()
        while True:
            if self._span_queue.empty():
                break
            if (time.time() - start) >= timeout:
                print(f"[Nora] ⚠️ Timeout waiting for execution span queue to empty")
                break
            time.sleep(0.01)
        
        # Give worker thread a bit more time to finish current item
        time.sleep(0.05)

        # Also join any auxiliary threads if present (compatibility)
        with self._execution_threads_lock:
            threads_to_wait = [t for t in self._execution_threads if t.is_alive()]

        for t in threads_to_wait:
            t.join(timeout=timeout)

        # Clean up finished threads
        with self._execution_threads_lock:
            self._execution_threads = [t for t in self._execution_threads if t.is_alive()]

    def _worker(self) -> None:
        """Worker thread that processes the span queue in FIFO order."""
        while True:
            try:
                item = self._span_queue.get()
            except Exception:
                continue

            try:
                trace_id, span_data = item
                self._do_send(trace_id, span_data)
            except Exception:
                pass
            finally:
                try:
                    self._span_queue.task_done()
                except Exception:
                    pass

    def _do_send(self, trace_id: str, span_data: Dict[str, Any]) -> None:
        """Actual sending logic extracted from previous inline _send() closure."""
        if not requests:
            print("[Nora] ⚠️  WARNING: requests module not available")
            return

        local_span_id = span_data.get("id")

        try:
            # Sanitize span_data to ensure all Pydantic models are converted to dicts
            sanitized_span_data = _sanitize_for_json(span_data)
            
            headers = {
                "X-API-Key": self.client.api_key,
                "Content-Type": "application/json",
            }

            span_name = sanitized_span_data.get("name") or (
                sanitized_span_data.get("provider", "unknown") + "_" + sanitized_span_data.get("model", "execution")
            )

            payload = {
                "trace_id": trace_id,
                "span_name": span_name,
                "span_data": sanitized_span_data,
            }
            
            # Include execution_parent_id if present
            execution_parent_id = sanitized_span_data.get("execution_parent_id")
            if execution_parent_id:
                payload["execution_parent_id"] = execution_parent_id

            # Parse and update trace input
            try:
                parsed_input = self.client._parse_input_from_span(sanitized_span_data)
                if parsed_input:
                    self.client._update_trace_input(trace_id, parsed_input)
            except Exception:
                pass

            # Include model and tokens for LLM spans
            try:
                span_kind = sanitized_span_data.get("span_kind")
            except Exception:
                span_kind = None

            if span_kind == "llm":
                model_val = sanitized_span_data.get("model")
                if model_val is not None:
                    payload["model"] = model_val

                # Build tokens object
                tokens_obj = None
                try:
                    tokens_field = sanitized_span_data.get("tokens")
                    if isinstance(tokens_field, dict):
                        if ("total_input" in tokens_field) or ("total_output" in tokens_field):
                            ti = tokens_field.get("total_input")
                            to = tokens_field.get("total_output")
                            obj: Dict[str, int] = {}
                            if ti is not None:
                                obj["total_input"] = int(ti)
                            if to is not None:
                                obj["total_output"] = int(to)
                            tokens_obj = obj if obj else None
                        else:
                            # Try alternative key names
                            alt_ti = None
                            alt_to = None
                            if isinstance(tokens_field.get("input_tokens"), int):
                                alt_ti = tokens_field.get("input_tokens")
                            if isinstance(tokens_field.get("output_tokens"), int):
                                alt_to = tokens_field.get("output_tokens")
                            if alt_ti is None and isinstance(
                                tokens_field.get("prompt_tokens"), int
                            ):
                                alt_ti = tokens_field.get("prompt_tokens")
                            if alt_to is None and isinstance(
                                tokens_field.get("completion_tokens"), int
                            ):
                                alt_to = tokens_field.get("completion_tokens")
                            if alt_to is None and isinstance(
                                tokens_field.get("tokens_used"), int
                            ):
                                alt_to = tokens_field.get("tokens_used")

                            if alt_ti is not None or alt_to is not None:
                                obj: Dict[str, int] = {}
                                if alt_ti is not None:
                                    obj["total_input"] = int(alt_ti)
                                if alt_to is not None:
                                    obj["total_output"] = int(alt_to)
                                tokens_obj = obj
                    else:
                        # Try metadata/usage fields
                        md = sanitized_span_data.get("metadata") or {}
                        usage = None
                        try:
                            usage = (md.get("response") or {}).get("usage")
                        except Exception:
                            usage = None

                        total_input = None
                        total_output = None

                        if isinstance(usage, dict):
                            if isinstance(usage.get("prompt_tokens"), int):
                                total_input = usage.get("prompt_tokens")
                            if isinstance(usage.get("completion_tokens"), int):
                                total_output = usage.get("completion_tokens")

                        # Fallback to metadata.input_tokens / metadata.output_tokens
                        if total_input is None:
                            try:
                                if isinstance(md.get("input_tokens"), int):
                                    total_input = md.get("input_tokens")
                            except Exception:
                                pass
                        if total_output is None:
                            try:
                                if isinstance(md.get("output_tokens"), int):
                                    total_output = md.get("output_tokens")
                            except Exception:
                                pass

                        if total_input is not None or total_output is not None:
                            obj: Dict[str, int] = {}
                            if total_input is not None:
                                obj["total_input"] = int(total_input)
                            if total_output is not None:
                                obj["total_output"] = int(total_output)
                            tokens_obj = obj
                        else:
                            tokens_used = sanitized_span_data.get("tokens_used")
                            if tokens_used is not None:
                                tokens_obj = {"total_output": int(tokens_used)}
                except Exception as e:
                    tokens_obj = None

                if tokens_obj is not None:
                    payload["tokens"] = tokens_obj

            response = requests.post(
                self.client.execution_span_url, json=payload, headers=headers, timeout=10
            )

            if response.status_code in (200, 201):
                try:
                    response_data = response.json()
                    execution_id = response_data.get("id")

                    if execution_id:

                        with self._trace_exec_lock:
                            if trace_id not in self._trace_execution_ids:
                                self._trace_execution_ids[trace_id] = []
                            self._trace_execution_ids[trace_id].append(execution_id)
                    else:
                        if local_span_id:
                            with self._trace_exec_lock:
                                if trace_id not in self._trace_execution_ids:
                                    self._trace_execution_ids[trace_id] = []
                                self._trace_execution_ids[trace_id].append(local_span_id)
                except Exception as e:
                    if local_span_id:
                        with self._trace_exec_lock:
                            if trace_id not in self._trace_execution_ids:
                                self._trace_execution_ids[trace_id] = []
                            self._trace_execution_ids[trace_id].append(local_span_id)

        except requests.exceptions.RequestException as e:
            print(f"[Nora] ❌ Error sending execution span: {str(e)}")
        except Exception as e:
            print(f"[Nora] ❌ Unexpected error sending execution span: {str(e)}")

