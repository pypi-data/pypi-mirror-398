"""
Tool 실행 자동 감지 및 trace 생성
"""

import time
import json
from typing import Any, Dict, List, Optional
from ...client import _current_trace_group, _current_execution_span
from .types import ToolExecutionInfo


def auto_trace_tool_calls_from_response(response: Any, client: Any, llm_span_id: str) -> None:
    """
    LLM response에서 tool_calls를 감지하여 나중에 tool execution을 추적할 수 있도록 매핑을 저장합니다.
    첫 번째 LLM call이 tool을 요청했을 때 호출됩니다.

    Args:
        response: OpenAI API response
        client: Nora client 인스턴스
        llm_span_id: 부모 LLM span ID
    """
    if not _current_trace_group.get():
        return

    if not hasattr(response, 'choices') or not response.choices:
        return

    choice = response.choices[0]
    if not hasattr(choice, 'message'):
        return

    message = choice.message
    if not hasattr(message, 'tool_calls') or not message.tool_calls:
        return

    # Store mapping of tool_call_id -> parent LLM span ID
    # This will be used when tool execution is detected
    if not hasattr(client, "_tool_call_parents"):
        client._tool_call_parents = {}

    for tool_call in message.tool_calls:
        if tool_call.type != "function":
            continue

        # Map this tool_call_id to the LLM span that requested it
        client._tool_call_parents[tool_call.id] = llm_span_id


def auto_trace_tool_executions(request_params: Dict[str, Any], client: Any) -> None:
    """
    Messages에서 tool role을 감지하여 tool execution trace를 생성합니다.
    두 번째 LLM call에서 tool 실행 결과를 포함한 완전한 trace를 만듭니다.

    Args:
        request_params: 요청 파라미터 (messages 포함)
        client: Nora client 인스턴스
    """
    if not _current_trace_group.get():
        return

    messages = request_params.get("messages", [])
    if not messages:
        return

    # Get tool_call_id -> parent LLM span ID mapping
    tool_call_parents = getattr(client, "_tool_call_parents", {})

    for i, msg in enumerate(messages):
        # Convert Pydantic model to dict if needed
        if hasattr(msg, 'model_dump'):
            msg_dict = msg.model_dump()
        elif hasattr(msg, 'dict'):
            msg_dict = msg.dict()
        elif isinstance(msg, dict):
            msg_dict = msg
        else:
            continue
        
        if msg_dict.get("role") != "tool":
            continue

        tool_call_id = msg_dict.get("tool_call_id", "")
        tool_result = msg_dict.get("content", "")

        # Extract tool info from previous messages
        tool_info = _extract_tool_info_from_messages(messages, i, msg_dict)
        if not tool_info:
            continue

        if _is_tool_already_traced(client, tool_info["call_id"], tool_info["name"]):
            continue

        # Get the parent LLM span ID (from first LLM call that requested this tool)
        parent_span_id = tool_call_parents.get(tool_call_id)
        
        # Create complete tool execution trace with result
        _create_tool_execution_trace(client, tool_info, tool_result, parent_span_id)


def _extract_tool_info_from_messages(
    messages: List[Dict], tool_msg_index: int, tool_msg: Dict
) -> Optional[ToolExecutionInfo]:
    """
    Tool message로부터 tool call 정보를 추출합니다.

    Args:
        messages: 메시지 리스트
        tool_msg_index: Tool 메시지의 인덱스
        tool_msg: Tool 메시지 (dict)

    Returns:
        Tool 정보 dict 또는 None (찾지 못한 경우)
    """
    tool_call_id = tool_msg.get("tool_call_id", "")

    # 이전 메시지에서 assistant의 tool_calls 찾기
    for j in range(tool_msg_index - 1, -1, -1):
        prev_msg = messages[j]
        
        # Convert to dict if needed
        if hasattr(prev_msg, 'model_dump'):
            prev_msg_dict = prev_msg.model_dump()
        elif hasattr(prev_msg, 'dict'):
            prev_msg_dict = prev_msg.dict()
        elif isinstance(prev_msg, dict):
            prev_msg_dict = prev_msg
        else:
            continue
        
        if prev_msg_dict.get("role") != "assistant":
            continue

        tool_calls = prev_msg_dict.get("tool_calls", [])
        for tc in tool_calls:
            # Convert tool call to dict if needed
            if hasattr(tc, 'model_dump'):
                tc_dict = tc.model_dump()
            elif hasattr(tc, 'dict'):
                tc_dict = tc.dict()
            elif isinstance(tc, dict):
                tc_dict = tc
            else:
                continue
                
            if tc_dict.get("id") == tool_call_id:
                func_info = tc_dict.get("function", {})
                # Convert function info to dict if needed
                if hasattr(func_info, 'model_dump'):
                    func_dict = func_info.model_dump()
                elif hasattr(func_info, 'dict'):
                    func_dict = func_info.dict()
                elif isinstance(func_info, dict):
                    func_dict = func_info
                else:
                    func_dict = {}
                    
                return ToolExecutionInfo(
                    call_id=tool_call_id,
                    name=func_dict.get("name", "unknown"),
                    arguments=func_dict.get("arguments", "{}"),
                )

    return None


def _is_tool_already_traced(client: Any, tool_call_id: str, tool_name: str) -> bool:
    """
    Tool이 이미 trace되었는지 확인합니다.

    Args:
        client: Nora client 인스턴스
        tool_call_id: Tool call ID
        tool_name: Tool 이름

    Returns:
        이미 trace되었으면 True
    """
    if not hasattr(client, "_traced_tools"):
        client._traced_tools = set()

    trace_key = f"{tool_call_id}_{tool_name}"
    if trace_key in client._traced_tools:
        return True

    client._traced_tools.add(trace_key)
    return False


def _create_tool_execution_trace(
    client: Any, tool_info: ToolExecutionInfo, tool_result: str, parent_span_id: Optional[str] = None
) -> None:
    """
    Tool execution trace를 생성합니다.

    Args:
        client: Nora client 인스턴스
        tool_info: Tool 실행 정보
        tool_result: Tool 실행 결과
        parent_span_id: 부모 LLM span ID (첫 번째 LLM call that requested the tool)
    """
    try:
        args_dict = (
            json.loads(tool_info["arguments"])
            if isinstance(tool_info["arguments"], str)
            else tool_info["arguments"]
        )
    except (json.JSONDecodeError, TypeError):
        args_dict = {}

    # Prepare metadata
    metadata = {
        "tool_name": tool_info["name"],
        "tool_call_id": tool_info["call_id"],
        "arguments": args_dict,
        "result": tool_result,
        "is_tool_execution": True,
    }
    
    # Add execution_parent_id if we have the parent LLM span
    extra_fields = {}
    if parent_span_id:
        extra_fields["execution_parent_id"] = parent_span_id

    # Use the internal _trace_method to record a tool execution trace
    try:
        client._trace_method(
            provider="tool_execution",
            model=tool_info["name"],
            prompt=f"Tool: {tool_info['name']}\nArguments: {json.dumps(args_dict, ensure_ascii=False)}",
            response=tool_result,
            start_time=time.time() - 0.001,
            end_time=time.time(),
            tokens_used=0,
            metadata=metadata,
            **extra_fields,
        )
    except Exception:
        # Fall back: if _trace_method is not available for some reason, safely ignore
        try:
            # Best-effort: append minimal trace info to client's traces list if present
            if hasattr(client, "_traces"):
                trace_data = {
                    "provider": "tool_execution",
                    "model": tool_info["name"],
                    "prompt": f"Tool: {tool_info['name']}",
                    "response": tool_result,
                    "start_time": time.time() - 0.001,
                    "end_time": time.time(),
                    "metadata": {
                        "tool_name": tool_info["name"],
                        "tool_call_id": tool_info["call_id"],
                    },
                }
                # Add parent relationship in fallback case too
                if parent_span_id:
                    trace_data["execution_parent_id"] = parent_span_id
                client._traces.append(trace_data)
        except Exception:
            pass
