"""
OpenAI 스트리밍 응답 처리
"""

from ..._internal.utils import format_messages
from .utils import extract_detailed_usage


def wrap_streaming_response(response, client, request_params, start_time, is_async: bool):
    """
    스트리밍 응답을 래핑하여 완료 시 trace를 기록합니다.

    Args:
        response: OpenAI 스트리밍 응답
        client: Nora client 인스턴스
        request_params: 요청 파라미터
        start_time: 시작 시간
        is_async: 비동기 여부

    Returns:
        래핑된 스트리밍 응답
    """
    # 스트리밍 데이터 수집용
    collected_data = {
        "chunks": [],
        "text": "",
        "tool_calls": {},
        "finish_reason": None,
        "usage": None,
    }

    def process_chunk(chunk):
        """청크를 처리하고 데이터를 수집합니다."""
        try:
            # Usage 정보 추출 (stream_options: {"include_usage": True}일 때)
            # 이 경우 마지막 청크에만 usage가 있고 choices는 비어있을 수 있음
            if hasattr(chunk, "usage") and chunk.usage:
                collected_data["usage"] = extract_detailed_usage(chunk)

            # Choices가 있는 경우 (텍스트/tool_call 데이터)
            if hasattr(chunk, "choices") and chunk.choices:
                choice = chunk.choices[0]

                # 텍스트 델타
                if hasattr(choice, "delta"):
                    delta = choice.delta
                    if hasattr(delta, "content") and delta.content:
                        collected_data["text"] += delta.content

                    # Tool call 델타
                    if hasattr(delta, "tool_calls") and delta.tool_calls:
                        for tc_delta in delta.tool_calls:
                            idx = tc_delta.index
                            if idx not in collected_data["tool_calls"]:
                                collected_data["tool_calls"][idx] = {
                                    "id": "",
                                    "type": "function",
                                    "function": {"name": "", "arguments": ""},
                                }

                            if hasattr(tc_delta, "id") and tc_delta.id:
                                collected_data["tool_calls"][idx]["id"] = tc_delta.id
                            if hasattr(tc_delta, "function"):
                                func = tc_delta.function
                                if hasattr(func, "name") and func.name:
                                    collected_data["tool_calls"][idx]["function"][
                                        "name"
                                    ] = func.name
                                if hasattr(func, "arguments") and func.arguments:
                                    collected_data["tool_calls"][idx]["function"][
                                        "arguments"
                                    ] += func.arguments

                # Finish reason
                if hasattr(choice, "finish_reason") and choice.finish_reason:
                    collected_data["finish_reason"] = choice.finish_reason

        except Exception:
            pass

        return chunk

    def finalize_trace():
        """스트리밍 완료 후 trace를 기록합니다."""
        import time

        end_time = time.time()

        # Tool calls를 리스트로 변환
        tool_calls_list = None
        if collected_data["tool_calls"]:
            tool_calls_list = [
                collected_data["tool_calls"][idx]
                for idx in sorted(collected_data["tool_calls"].keys())
            ]

        trace_data = {
            "provider": "openai",
            "model": request_params["model"],
            "prompt": format_messages(request_params.get("messages", [])),
            "response": collected_data["text"],
            "start_time": start_time,
            "end_time": end_time,
            "finish_reason": collected_data["finish_reason"],
            "metadata": {
                "request": {
                    "parameters": {
                        k: v
                        for k, v in request_params.items()
                        if k not in ["messages", "model", "prompt"] and v is not None
                    }
                },
                "response": {
                    "streaming": True,
                    "chunks_count": len(collected_data["chunks"]),
                    "usage": collected_data["usage"],
                    "finish_reason": collected_data["finish_reason"],
                },
            },
        }

        trace_data["metadata"]["request"]["messages"] = request_params.get("messages", [])

        if tool_calls_list:
            trace_data["tool_calls"] = tool_calls_list
            trace_data["metadata"]["response"]["tool_calls"] = tool_calls_list

        if collected_data["usage"]:
            trace_data["tokens_used"] = collected_data["usage"].get("total_tokens")

        client._trace_method(**trace_data)

    # 동기 스트리밍 래퍼
    if not is_async:

        def sync_wrapper():
            try:
                for chunk in response:
                    collected_data["chunks"].append(chunk)
                    yield process_chunk(chunk)
            finally:
                finalize_trace()

        return sync_wrapper()

    # 비동기 스트리밍 래퍼
    else:

        async def async_wrapper():
            try:
                async for chunk in response:
                    collected_data["chunks"].append(chunk)
                    yield process_chunk(chunk)
            finally:
                finalize_trace()

        return async_wrapper()
