"""
Decision 추적 및 관리 모듈
Decision 관련 로직을 NoraClient에서 분리
"""

import time
import queue
import threading
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

try:
    import requests
except ImportError:
    requests = None


class DecisionManager:
    """Decision 추적 및 전송을 담당하는 클래스"""

    def __init__(self, client: "NoraClient"):  # type: ignore
        """DecisionManager 초기화
        
        Args:
            client: NoraClient 인스턴스
        """
        self.client = client
        self._decisions_enabled = True
        self._atomic_decisions: List[Dict[str, Any]] = []
        self._decision_queue: "queue.Queue[Dict[str, Any]]" = queue.Queue()
        self._decision_stop = threading.Event()
        self._decision_worker = threading.Thread(
            target=self._decision_worker_loop, name="nora-decision-worker", daemon=True
        )
        self._decision_worker.start()

        # Map trace_id -> decision_id (for decision linking)
        self._trace_decision_ids: Dict[str, str] = {}
        self._decision_id_lock = threading.Lock()

        # Track last agent name for detecting agent changes
        self._last_agent_name: Optional[str] = None

        # Track per-trace execution order for matching execution_ids to atomics
        self._trace_execution_order: Dict[str, int] = {}

        # Track pending tool calls from LLM to group tool executions under same agent
        self._pending_tool_calls: Dict[str, str] = {}  # {tool_name: llm_agent_name}
        self._pending_tools_lock = threading.Lock()
        
        # Cache execution spans to track parent-child relationships
        self._execution_spans_cache: Dict[str, Dict[str, Any]] = {}  # {span_id: span_data}
        self._cache_lock = threading.Lock()
    
    def _cache_execution_span(self, span_data: Dict[str, Any]) -> None:
        """Cache execution span for parent-child agent tracking."""
        span_id = span_data.get("id")
        if span_id:
            with self._cache_lock:
                self._execution_spans_cache[span_id] = {
                    "id": span_id,
                    "name": span_data.get("name"),
                    "result": span_data.get("result"),
                    "execution_parent_id": span_data.get("execution_parent_id"),
                }

    def _create_decision(self, trace_id: str) -> Optional[str]:
        """Create a decision and return decision_id."""
        if not requests or not trace_id:
            return None

        try:
            headers = {
                "X-API-Key": self.client.api_key,
                "Content-Type": "application/json",
            }

            payload = {"trace_id": trace_id}

            response = requests.post(
                self.client.decision_create_url, json=payload, headers=headers, timeout=10
            )

            if response.status_code in (200, 201):
                response_data = response.json()
                decision_id = response_data.get("id")

                if not decision_id:
                    print(
                        f"[Nora] ❌ ERROR: 'id' not found in decision response. Response: {response_data}"
                    )
                    return None

                with self._decision_id_lock:
                    self._trace_decision_ids[trace_id] = decision_id

                return decision_id
            else:
                print(
                    f"[Nora] ⚠️  Warning: Failed to create decision (status: {response.status_code})"
                )
                print(f"[Nora] Response body: {response.text[:500]}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"[Nora] ❌ Error creating decision: {str(e)}")
            return None
        except Exception as e:
            print(f"[Nora] ❌ Unexpected error creating decision: {str(e)}")
            return None

    def _update_decision_span(self, decision_span_id: str, updates: Dict[str, Any]) -> bool:
        """Patch/update an existing decision span via API."""
        if not requests or not decision_span_id:
            return False

        try:
            url = f"{self.client.api_url}/decision/{decision_span_id}"
            headers = {
                "X-API-Key": self.client.api_key,
                "Content-Type": "application/json",
            }

            response = requests.patch(url, json=updates, headers=headers, timeout=10)

        except requests.exceptions.RequestException as e:
            print(f"[Nora] ❌ HTTP error updating decision span: {e}")
            return False
        except Exception as e:
            print(f"[Nora] ❌ Unexpected error updating decision span: {e}")
            return False

    def _maybe_capture_llm_tool_decision(
        self,
        trace_data: Dict[str, Any],
        trace_group_id: Optional[str],
        trace_id: Optional[str],
    ) -> None:
        """Capture atomic decision when LLM is called with tools."""
        try:
            metadata = trace_data.get("metadata", {})
            request_params = metadata.get("request", {}).get("parameters", {})
            available_tools = request_params.get("tools", [])

            if not available_tools:
                return

            # Extract tool names from available tools
            tool_options = []
            for tool in available_tools:
                if isinstance(tool, dict) and "function" in tool:
                    func_info = tool["function"]
                    tool_name = func_info.get("name")
                    tool_desc = func_info.get("description", "")
                    if tool_name:
                        tool_options.append(
                            {
                                "content": f"{tool_name}: {tool_desc}" if tool_desc else tool_name,
                                "score": None,
                            }
                        )

            if not tool_options:
                return

            # Extract selected tools from response tool_calls
            selected_tools = []
            tool_calls = trace_data.get("tool_calls", [])
            if tool_calls:
                for tc in tool_calls:
                    if isinstance(tc, dict):
                        func_info = tc.get("function", {})
                        tool_name = func_info.get("name") if func_info else tc.get("name")
                        if tool_name:
                            selected_tools.append(
                                {"content": tool_name, "score": 1.0}
                            )

            # Determine agent name
            agent_name = f"llm_{trace_data.get('model', 'unknown')}"

            # Determine span_kind from semantics
            span_kind = "llm"
            model = trace_data.get("model", "unknown")
            llm_cfg = self.client.semantics.get("llm", {})
            if model in llm_cfg.get("functions", []):
                span_kind = "llm"

            # Check if agent changed
            if self._last_agent_name and self._last_agent_name != agent_name:
                if self._atomic_decisions:
                    print(
                        f"[Nora] 🔄 Agent changed: {self._last_agent_name} -> {agent_name}, flushing previous agent decisions"
                    )
                    self._flush_current_agent_decisions()

            self._last_agent_name = agent_name

            # Determine execution order
            execution_order = None
            if trace_id:
                execution_order = self._trace_execution_order.get(trace_id, 0)
                self._trace_execution_order[trace_id] = execution_order + 1

            # Register selected tools as pending
            with self._pending_tools_lock:
                for tool in selected_tools:
                    tool_name = tool.get("content")
                    if tool_name:
                        self._pending_tool_calls[tool_name] = agent_name

            atomic = {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "span_kind": span_kind,
                "trace_group_id": trace_group_id,
                "agent_name": agent_name,
                "function_name": f"llm_tool_call_{trace_data.get('model', 'unknown')}",
                "options": tool_options,
                "selected_option": selected_tools,
                "evidence": [],
                "execution_id": None,
                "decision_id": None,
                "_trace_id": trace_id,
                "_execution_order": execution_order,
            }

            self._atomic_decisions.append(atomic)
            self._send_decision_async("atomic", atomic)
        except Exception as e:
            print(f"[Nora] ⚠️ LLM tool decision capture skipped due to error: {e}")

    def _maybe_capture_execution_decision(
        self,
        span_data: Dict[str, Any],
        trace_group_id: Optional[str],
        trace_id: Optional[str],
    ) -> None:
        """Capture atomic decision from execution span if conditions are met.
        
        Conditions for creating atomic decision:
        1. span_kind is 'llm', 'rag', 'tool', or 'select'
        2. For 'llm': tools/tool_calls are present in metadata or result, OR options are present
        3. For 'rag' or 'tool': options are present (with content and optional score)
        4. For 'select': input becomes options, output becomes selected_option
        """
        try:
            span_kind = span_data.get("span_kind")
            
            if not span_kind or span_kind not in ["llm", "rag", "tool", "select"]:
                print(f"[Nora] ⏭️  Skipping decision: span_kind '{span_kind}' not in [llm, rag, tool, select]")
                return
            
            options = None
            selected_option = []
            
            # Select span: input -> options, output -> selected_option
            if span_kind == "select":
                # Get input as options
                input_data = span_data.get("input", {})
                
                # Case 1: input has 'options' field
                if isinstance(input_data, dict) and "options" in input_data:
                    options = input_data["options"]
                # Case 2: input itself is a list (treated as options)
                elif isinstance(input_data, list):
                    options = input_data
                # Case 3: Check function parameters (query, documents, candidates, etc.)
                elif isinstance(input_data, dict):
                    # Try to find list parameters that could be options
                    for key, value in input_data.items():
                        if isinstance(value, list) and key in ["documents", "candidates", "options", "items", "data"]:
                            options = value
                            break
                
                if not options:
                    return
                
                # Normalize options
                valid_options = []
                for opt in options:
                    if isinstance(opt, dict) and "content" in opt:
                        valid_options.append({
                            "content": opt["content"],
                            "score": opt.get("score")
                        })
                    elif isinstance(opt, str):
                        valid_options.append({"content": opt, "score": None})
                
                if not valid_options:
                    print(f"[Nora] ⏭️  Skipping select decision: could not normalize options")
                    return
                
                options = valid_options
                
                # Get output/result as selected_option
                result = span_data.get("result", {})
                output_data = span_data.get("output", result)
                
                # Case 1: output has 'selected' or 'selected_option' field
                if isinstance(output_data, dict):
                    selected_raw = (
                        output_data.get("selected_option") or 
                        output_data.get("selected") or 
                        output_data.get("result")
                    )
                # Case 2: output/result itself is the selection
                else:
                    selected_raw = output_data
                
                # If still no selected_raw but result is dict with 'content' or 'score'
                if not selected_raw and isinstance(output_data, dict):
                    if "content" in output_data or "score" in output_data:
                        selected_raw = output_data
                
                # Normalize selected_option format
                if selected_raw:
                    if isinstance(selected_raw, list):
                        for item in selected_raw:
                            if isinstance(item, dict) and "content" in item:
                                selected_option.append({
                                    "content": item["content"],
                                    "score": item.get("score")
                                })
                            elif isinstance(item, str):
                                selected_option.append({"content": item, "score": None})
                    elif isinstance(selected_raw, dict):
                        # Case: dict with 'content' key
                        if "content" in selected_raw:
                            selected_option = [{
                                "content": selected_raw["content"],
                                "score": selected_raw.get("score")
                            }]
                        # Case: dict returned from select function (like from rerank_documents)
                        elif all(isinstance(v, dict) and "content" in v for v in selected_raw.values()):
                            # Dict of items with content
                            for item in selected_raw.values():
                                selected_option.append({
                                    "content": item["content"],
                                    "score": item.get("score")
                                })
                    elif isinstance(selected_raw, str):
                        selected_option = [{"content": selected_raw, "score": None}]
            
            # LLM with tools OR options
            if span_kind == "llm":
                # First check for options (simple case - RAG-like behavior with llm span_kind)
                if "options" in span_data:
                    options = span_data["options"]
                else:
                    result = span_data.get("result", {})
                    if isinstance(result, dict) and "options" in result:
                        options = result["options"]
                
                # If options found, treat as RAG-like
                if options:
                    # Validate options format
                    if isinstance(options, list) and options:
                        valid_options = []
                        for opt in options:
                            if isinstance(opt, dict) and "content" in opt:
                                valid_options.append({
                                    "content": opt["content"],
                                    "score": opt.get("score")
                                })
                            elif isinstance(opt, str):
                                valid_options.append({"content": opt, "score": None})
                        
                        if valid_options:
                            options = valid_options
                        else:
                            options = None
                    else:
                        options = None
                
                # If no options, check for tools
                if not options:
                    # Check for tools in metadata
                    metadata = span_data.get("metadata", {})
                    request_params = metadata.get("request", {}).get("parameters", {})
                    available_tools = request_params.get("tools", [])
                    
                    # Also check result for tools
                    result = span_data.get("result", {})
                    if not available_tools and isinstance(result, dict):
                        available_tools = result.get("tools", [])
                    
                    if not available_tools:
                        print(f"[Nora] ⏭️  Skipping LLM decision: no tools or options found")
                        return
                    
                    # Extract tool names as options
                    tool_options = []
                    for tool in available_tools:
                        if isinstance(tool, dict):
                            if "function" in tool:
                                tool_name = tool.get("function", {}).get("name")
                                if tool_name:
                                    tool_options.append({"content": tool_name, "score": None})
                            elif "name" in tool:
                                tool_options.append({"content": tool["name"], "score": None})
                    
                    if not tool_options:
                        print(f"[Nora] ⏭️  Skipping LLM decision: could not extract tool names")
                        return
                    
                    options = tool_options
                    
                    # Extract selected tools from tool_calls
                    tool_calls = span_data.get("tool_calls", [])
                    if not tool_calls and isinstance(result, dict):
                        tool_calls = result.get("tool_calls", [])
                    
                    if tool_calls:
                        for tc in tool_calls:
                            if isinstance(tc, dict):
                                tc_name = tc.get("function", {}).get("name") or tc.get("name")
                                if tc_name:
                                    selected_option.append(tc_name)
                
            # RAG or Tool with options
            elif span_kind in ["rag", "tool"]:
                # Check span_data for options
                if "options" in span_data:
                    options = span_data["options"]
                else:
                    # Check result
                    result = span_data.get("result", {})
                    if isinstance(result, dict) and "options" in result:
                        options = result["options"]
                    else:
                        return
                
                # Validate options format
                if not isinstance(options, list) or not options:
                    return
                
                # Ensure options have content field
                valid_options = []
                for opt in options:
                    if isinstance(opt, dict) and "content" in opt:
                        valid_options.append({
                            "content": opt["content"],
                            "score": opt.get("score")
                        })
                    elif isinstance(opt, str):
                        valid_options.append({"content": opt, "score": None})
                
                if not valid_options:
                    return
                
                options = valid_options
            
            if not options:
                return
            
            # Determine agent name
            func_name = span_data.get("name", "unknown")
            result_data = span_data.get("result", {})
            agent_name = self._resolve_agent_name(func_name, result_data, span_data)
            
            # Note: We no longer flush on agent change - instead we track all atomics
            # and send them together at trace_group exit
            # This avoids timing issues with execution_id assignment
            
            # Track last agent for reference (but don't flush)
            if self._last_agent_name and self._last_agent_name != agent_name:
                print(
                    f"[Nora] 🔄 Agent changed: {self._last_agent_name} -> {agent_name}"
                )
            
            self._last_agent_name = agent_name
            
            # Determine execution order
            execution_order = None
            if trace_id:
                execution_order = self._trace_execution_order.get(trace_id, 0)
                self._trace_execution_order[trace_id] = execution_order + 1
            
            atomic = {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "span_kind": span_kind,
                "trace_group_id": trace_group_id,
                "agent_name": agent_name,
                "function_name": func_name,
                "options": options,
                "selected_option": selected_option,
                "evidence": [],
                "execution_id": None,
                "decision_id": None,
                "_trace_id": trace_id,
                "_execution_order": execution_order,
            }
            
            self._atomic_decisions.append(atomic)
            self._send_decision_async("atomic", atomic)
        except Exception as e:
            print(f"[Nora] ⚠️ Execution decision capture skipped due to error: {e}")

    def _maybe_capture_decision(
        self,
        func_name: str,
        result: Any,
        trace_group_id: Optional[str],
        execution_span_ids: Optional[List[str]] = None,
    ) -> None:
        """If semantics marks func_name as retrieval, extract decision and enqueue Atomic DecisionSpan."""
        try:
            cfg = self.client.semantics.get("retrieval", {})
            if not cfg or func_name not in (cfg.get("functions") or []):
                return

            extracted = self._extract_retrieval_options(result)
            if not extracted:
                return

            agent_name = self._resolve_agent_name(func_name, result)

            # Override agent if this function is a pending tool call from LLM
            with self._pending_tools_lock:
                if func_name in self._pending_tool_calls:
                    llm_agent = self._pending_tool_calls[func_name]
                    agent_name = llm_agent
                    del self._pending_tool_calls[func_name]

            # Check if agent changed
            if self._last_agent_name and self._last_agent_name != agent_name:
                if self._atomic_decisions:
                    self._flush_current_agent_decisions()

            self._last_agent_name = agent_name

            # Get current trace group to find its trace_id
            from ..client import _get_current_trace_group

            current_group = _get_current_trace_group()
            trace_id = None
            if current_group:
                trace_id = current_group.trace_id

            # Determine execution order
            execution_order = None
            if trace_id:
                execution_order = self._trace_execution_order.get(trace_id, 0)
                self._trace_execution_order[trace_id] = execution_order + 1

            atomic = {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "span_kind": "retrieval",
                "trace_group_id": trace_group_id,
                "agent_name": agent_name,
                "function_name": func_name,
                "options": extracted["options"],
                "execution_id": None,
                "decision_id": None,
                "_trace_id": trace_id,
                "_execution_order": execution_order,
            }

            self._atomic_decisions.append(atomic)
            self._send_decision_async("atomic", atomic)
        except Exception as e:
            print(f"[Nora] ⚠️ decision capture skipped due to error: {e}")

    def _extract_retrieval_options(self, result: Any) -> Optional[Dict[str, Any]]:
        """Normalize retrieval results into a list of {content: str, score: float|None}."""
        options = None
        if isinstance(result, dict) and "options" in result:
            options = result.get("options")
        elif isinstance(result, list):
            options = result
        else:
            return None

        if not isinstance(options, list) or not options:
            return None

        normalized: List[Dict[str, Any]] = []
        for opt in options:
            if isinstance(opt, dict) and ("content" in opt):
                normalized.append({"content": opt["content"], "score": opt.get("score")})
            elif isinstance(opt, str):
                normalized.append({"content": opt, "score": None})
            else:
                return None

        return {"options": normalized}

    def _resolve_agent_name(self, func_name: str, result: Any, span_data: Optional[Dict[str, Any]] = None) -> str:
        """Resolve agent_name used to aggregate AgentDecision.
        
        Priority:
        1. result['agent_name'] - explicit agent name in result
        2. Parent execution span with agent_name in result
        3. _current_agent_context - contextvar
        4. agent_map configuration
        5. func_name - fallback
        """
        # 1. Check result for explicit agent_name
        try:
            if isinstance(result, dict) and isinstance(result.get("agent_name"), str):
                return result["agent_name"]
        except Exception:
            pass

        # 2. Check parent execution span for agent_name
        if span_data:
            try:
                parent_id = span_data.get("execution_parent_id")
                if parent_id:
                    # Look up parent in cache
                    with self._cache_lock:
                        parent_span = self._execution_spans_cache.get(parent_id)
                    
                    if parent_span:
                        parent_result = parent_span.get("result", {})
                        if isinstance(parent_result, dict) and "agent_name" in parent_result:
                            parent_agent = parent_result["agent_name"]
                            return parent_agent
            except Exception as e:
                print(f"[Nora] ⚠️ Error checking parent span: {e}")

        # 3. Check current agent context (set by parent agent function)
        try:
            from ..client import _current_agent_context

            current_context = _current_agent_context.get()
            if current_context:
                return current_context
        except Exception:
            pass

        # 4. Check agent_map configuration
        try:
            agent_map = self.client.agent_map or {}
            if isinstance(agent_map, dict):
                matched_agents = []
                for agent_name, func_list in agent_map.items():
                    if isinstance(func_list, list) and func_name in func_list:
                        matched_agents.append(agent_name)

                if len(matched_agents) > 1:
                    print(
                        f"[Nora] ⚠️  Warning: Function '{func_name}' found in multiple agents: {matched_agents}. Using first match: {matched_agents[0]}"
                    )
                    return matched_agents[0]
                elif len(matched_agents) == 1:
                    return matched_agents[0]
        except Exception as e:
            print(f"[Nora] ⚠️  Error resolving agent from agent_map: {e}")

        # 5. Fallback to function name
        return func_name

    def _send_decision_async(self, kind: str, payload: Dict[str, Any]) -> None:
        """Send decision asynchronously."""
        if not self._decisions_enabled:
            return

        # Atomic decisions are queued directly during flush after IDs are assigned
        # Other decisions go to queue immediately
        if kind != "atomic":
            self._decision_queue.put({"kind": kind, "payload": payload})

    def _decision_worker_loop(self) -> None:
        """Background worker loop for processing decisions."""
        while not self._decision_stop.is_set():
            try:
                item = self._decision_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                kind = item.get("kind")
                payload = item.get("payload")
                if kind == "atomic":
                    self._post_atomic_decision(payload)
                elif kind == "agent":
                    self._post_agent_decision(payload)
                else:
                    print(f"[Nora] 🧠 (PRINT) Would POST Decision kind='{kind}': {payload}")
            except Exception as e:
                print(f"[Nora] ❌ Decision processing error: {e}")
            finally:
                try:
                    self._decision_queue.task_done()
                except Exception:
                    pass

    def _post_atomic_decision(self, atomic: Dict[str, Any]) -> None:
        """Send atomic decision to backend."""
        if not requests:
            print("[Nora] ⚠️  WARNING: requests module not available for atomic decision")
            return

        try:
            decision_span_id = atomic.get("decision_id")
            execution_span_id = atomic.get("execution_id")
            agent_name = atomic.get("agent_name")
            function_name = atomic.get("function_name")
            span_kind = atomic.get("span_kind")
            options = atomic.get("options") or []
            selected_option = atomic.get("selected_option") or []
            evidence = atomic.get("evidence") or []

            if not (
                decision_span_id
                and execution_span_id
                and agent_name
                and function_name
                and span_kind
            ):
                print(
                    "[Nora] ⚠️  Missing required fields for atomic decision, "
                    f"decision_span_id={decision_span_id}, execution_span_id={execution_span_id}, "
                    f"agent_name={agent_name}, function_name={function_name}, span_kind={span_kind}"
                )
                return

            url = f"{self.client.decision_create_url}atomic-decision"
            headers = {
                "X-API-Key": self.client.api_key,
                "Content-Type": "application/json",
            }
            payload = {
                "decision_span_id": decision_span_id,
                "execution_span_id": execution_span_id,
                "agent_name": agent_name,
                "function_name": function_name,
                "span_kind": span_kind,
                "options": options,
                "selected_option": selected_option,
                "evidence": evidence,
            }

            response = requests.post(url, json=payload, headers=headers, timeout=10)
        except requests.exceptions.RequestException as e:
            print(f"[Nora] ❌ HTTP error posting atomic decision: {e}")
        except Exception as e:
            print(f"[Nora] ❌ Unexpected error posting atomic decision: {e}")

    def _post_agent_decision(self, agent_decision: Dict[str, Any]) -> None:
        """Send agent decision to backend."""
        if not requests:
            print("[Nora] ⚠️  WARNING: requests module not available for agent decision")
            return

        try:
            decision_span_id = agent_decision.get("decision_id")
            contributors = agent_decision.get("contributors") or []
            agent_name = agent_decision.get("agent_name")
            p_error = agent_decision.get("p_error")

            if not (decision_span_id and agent_name):
                print(
                    "[Nora] ⚠️  Missing required fields for agent decision, "
                    f"decision_span_id={decision_span_id}, agent_name={agent_name}"
                )
                return

            url = f"{self.client.decision_create_url}agent-decision"
            headers = {
                "X-API-Key": self.client.api_key,
                "Content-Type": "application/json",
            }

            payload: Dict[str, Any] = {
                "decision_span_id": decision_span_id,
                "contributors": contributors,
                "agent_name": agent_name,
            }
            if p_error is not None:
                payload["p_error"] = p_error

            response = requests.post(url, json=payload, headers=headers, timeout=10)

            # Always attempt to PATCH the trace-level decision span
            try:
                updates: Dict[str, Any] = {"contributors": contributors}
                if agent_name:
                    updates["agent_name"] = agent_name
                if p_error is not None:
                    updates["p_error"] = p_error
                updates["status"] = "agent_posted"

                if decision_span_id:
                    self._update_decision_span(decision_span_id, updates)
            except Exception as e:
                print(f"[Nora] ⚠️ Failed to update decision span after agent post: {e}")
        except requests.exceptions.RequestException as e:
            print(f"[Nora] ❌ HTTP error posting agent decision: {e}")
        except Exception as e:
            print(f"[Nora] ❌ Unexpected error posting agent decision: {e}")

    def _build_and_send_agent_answer_decisions(self) -> None:
        """Aggregate Atomic -> AgentDecision, then one Decision."""
        if not self._atomic_decisions:
            return

        # Step 1: Create decision_id for each unique trace_id
        unique_trace_ids = set()
        for atomic in self._atomic_decisions:
            trace_id = atomic.get("_trace_id")
            if trace_id:
                unique_trace_ids.add(trace_id)

        for trace_id in unique_trace_ids:
            # Check if decision already exists WITHOUT holding the lock during _create_decision
            needs_creation = False
            with self._decision_id_lock:
                if trace_id not in self._trace_decision_ids:
                    needs_creation = True
            
            # Create decision OUTSIDE the lock to avoid deadlock
            if needs_creation:
                self._create_decision(trace_id)

        # Step 2: Wait for execution span queue to be processed
        try:
            # Don't wait too long - just give it a short time
            self.client._execution_span_manager.wait_for_completion(timeout=1.0)
        except Exception as e:
            print(f"[Nora] ⚠️ Error waiting for execution spans: {e}")
        
        # Additional brief sleep to ensure execution_ids are stored
        time.sleep(0.2)

        # Step 3: Fill execution_id and decision_id
        from ..client import _get_current_trace_group

        with self.client._trace_exec_lock:
            for atomic in self._atomic_decisions:
                trace_id = atomic.get("_trace_id")
                execution_order = atomic.get("_execution_order")

                if (
                    trace_id
                    and execution_order is not None
                    and trace_id in self.client._execution_span_manager._trace_execution_ids
                ):
                    exec_ids = self.client._execution_span_manager._trace_execution_ids[trace_id]
                    if execution_order < len(exec_ids):
                        atomic["execution_id"] = exec_ids[execution_order]
                else:
                    if trace_id:
                        available = trace_id in self.client._execution_span_manager._trace_execution_ids
                        print(f"[Nora]   ✗ Missing: trace_id={trace_id}, order={execution_order}, available={available}")

        # Fill decision_id
        for atomic in self._atomic_decisions:
            trace_id = atomic.get("_trace_id")

            with self._decision_id_lock:
                if trace_id and trace_id in self._trace_decision_ids:
                    atomic["decision_id"] = self._trace_decision_ids[trace_id]

            atomic.pop("_trace_id", None)
            atomic.pop("_execution_order", None)

        # Step 3: Send all atomics
        for atomic in self._atomic_decisions:
            self._decision_queue.put({"kind": "atomic", "payload": atomic})

        # Step 4: Group by agent_name and create AgentDecisions
        by_agent: Dict[str, List[Dict[str, Any]]] = {}
        for d in self._atomic_decisions:
            agent = d.get("agent_name") or "unknown"
            by_agent.setdefault(agent, []).append(d)

        # AgentDecision per agent
        for agent_name, items in by_agent.items():
            trace_groups = sorted(
                {x.get("trace_group_id") for x in items if x.get("trace_group_id")}
            )

            contributors = []
            for x in items:
                exec_id = x.get("execution_id")
                if exec_id:
                    contributors.append(exec_id)

            decision_id = None
            for x in items:
                if x.get("decision_id"):
                    decision_id = x["decision_id"]
                    break

            agent_decision = {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "agent_name": agent_name,
                "atomic_ids": [x["id"] for x in items],
                "contributors": contributors,
                "trace_groups": trace_groups,
                "decision_id": decision_id,
            }
            self._send_decision_async("agent", agent_decision)

        # Step 5: Create final Decision
        agent_names = sorted(by_agent.keys())
        all_groups = sorted(
            {
                x.get("trace_group_id")
                for items in by_agent.values()
                for x in items
                if x.get("trace_group_id")
            }
        )

        all_contributors = []
        for items in by_agent.values():
            for x in items:
                exec_id = x.get("execution_id")
                if exec_id:
                    all_contributors.append(exec_id)

        decision = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "span_kind": "retrieval",
            "decision_type": "retrieval",
            "groups": all_groups,
            "agent_names": agent_names,
            "contributors": all_contributors,
        }
        self._send_decision_async("decision", decision)

        # Update per-trace decision spans
        for trace_id in unique_trace_ids:
            with self._decision_id_lock:
                decision_span_id = self._trace_decision_ids.get(trace_id)

            if decision_span_id:
                with self.client._trace_exec_lock:
                    contributors = list(self.client._trace_execution_ids.get(trace_id, []))

                updates: Dict[str, Any] = {
                    "contributors": contributors,
                    "status": "completed",
                }
                try:
                    self._update_decision_span(decision_span_id, updates)
                except Exception as e:
                    print(f"[Nora] ⚠️ Failed to PATCH decision span {decision_span_id}: {e}")

        # Clear after scheduling posts
        self._atomic_decisions.clear()

        # Reset execution order counters
        for trace_id in unique_trace_ids:
            self._trace_execution_order.pop(trace_id, None)

        # Ensure queued decisions are processed (with timeout)
        try:
            # Wait up to 2 seconds for queue to be processed
            start_time = time.time()
            while not self._decision_queue.empty() and (time.time() - start_time) < 2.0:
                time.sleep(0.05)
        except Exception as e:
            print(f"[Nora] ⚠️ Error waiting for decision queue: {e}")

    def _flush_current_agent_decisions(self) -> None:
        """Flush only the current agent's atomic decisions without creating final Decision."""
        if not self._atomic_decisions:
            return

        # Step 1: Create decision_id for each unique trace_id
        unique_trace_ids = set()
        for atomic in self._atomic_decisions:
            trace_id = atomic.get("_trace_id")
            if trace_id:
                unique_trace_ids.add(trace_id)

        for trace_id in unique_trace_ids:
            # Check if decision already exists WITHOUT holding the lock during _create_decision
            needs_creation = False
            with self._decision_id_lock:
                if trace_id not in self._trace_decision_ids:
                    needs_creation = True
            
            # Create decision OUTSIDE the lock to avoid deadlock
            if needs_creation:
                self._create_decision(trace_id)

        # Step 2: Wait longer for execution span responses
        time.sleep(0.5)

        # Step 3: Fill execution_id and decision_id
        with self.client._trace_exec_lock:
            for atomic in self._atomic_decisions:
                trace_id = atomic.get("_trace_id")
                execution_order = atomic.get("_execution_order")

                if trace_id and trace_id in self.client._execution_span_manager._trace_execution_ids:
                    exec_ids = self.client._execution_span_manager._trace_execution_ids[trace_id]
                    if execution_order is not None and execution_order < len(exec_ids):
                        atomic["execution_id"] = exec_ids[execution_order]
                    else:
                        print(f"[Nora] ⚠️  Order {execution_order} out of range (have {len(exec_ids)} exec_ids)")
                else:
                    print(f"[Nora] ⚠️  No execution_ids found for trace {trace_id}")

        # Fill decision_id
        for atomic in self._atomic_decisions:
            trace_id = atomic.get("_trace_id")

            with self._decision_id_lock:
                if trace_id and trace_id in self._trace_decision_ids:
                    atomic["decision_id"] = self._trace_decision_ids[trace_id]

        # Step 4: Send atomics (before popping _trace_id)
        for atomic in self._atomic_decisions:
            self._decision_queue.put({"kind": "atomic", "payload": atomic})

        # Step 5: Create AgentDecision for current agent
        if self._atomic_decisions:
            agent_name = self._atomic_decisions[0].get("agent_name", "unknown")
            trace_groups = sorted(
                {x.get("trace_group_id") for x in self._atomic_decisions if x.get("trace_group_id")}
            )

            contributors = []
            for x in self._atomic_decisions:
                exec_id = x.get("execution_id")
                if exec_id:
                    contributors.append(exec_id)

            decision_id = None
            for x in self._atomic_decisions:
                if x.get("decision_id"):
                    decision_id = x["decision_id"]
                    break

            agent_decision = {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "agent_name": agent_name,
                "atomic_ids": [x["id"] for x in self._atomic_decisions],
                "contributors": contributors,
                "trace_groups": trace_groups,
                "decision_id": decision_id,
            }
            self._send_decision_async("agent", agent_decision)

        # Update per-trace decision spans (before clearing)
        for trace_id in unique_trace_ids:
            with self._decision_id_lock:
                decision_span_id = self._trace_decision_ids.get(trace_id)

            if decision_span_id:
                with self.client._trace_exec_lock:
                    contributors = list(self.client._execution_span_manager._trace_execution_ids.get(trace_id, []))

                updates: Dict[str, Any] = {
                    "contributors": contributors,
                    "status": "agent_flushed",
                }
                try:
                    self._update_decision_span(decision_span_id, updates)
                except Exception as e:
                    print(f"[Nora] ⚠️ Failed to PATCH decision span {decision_span_id}: {e}")

        # Clean up _trace_id and _execution_order from atomics
        for atomic in self._atomic_decisions:
            atomic.pop("_trace_id", None)
            atomic.pop("_execution_order", None)

        self._atomic_decisions.clear()

        # Ensure queued decisions are processed (with timeout)
        try:
            # Wait up to 2 seconds for queue to be processed
            start_time = time.time()
            while not self._decision_queue.empty() and (time.time() - start_time) < 2.0:
                time.sleep(0.05)
        except Exception as e:
            print(f"[Nora] ⚠️ Error waiting for decision queue: {e}")

