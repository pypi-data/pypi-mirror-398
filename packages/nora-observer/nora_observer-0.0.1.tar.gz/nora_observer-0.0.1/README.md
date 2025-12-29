# Nora Observability SDK

OpenAI, Anthropic, Google Gemini 등 주요 AI 라이브러리 호출을 자동으로 추적하고 분석하는 Python SDK입니다.

## ✨ 주요 기능

- 🚀 **2줄로 시작**: `import nora` + `nora.init()`만으로 자동 trace 활성화
- 🔍 **자동 감지**: OpenAI, Anthropic, Gemini API 자동 패치
- 🛠️ **Tool 실행 추적**: AI가 호출한 function tool 실행도 자동으로 추적
- 📊 **상세한 메타데이터**: 프롬프트, 응답, 토큰 사용량, 실행 시간, 비용 모두 기록
- 👥 **TraceGroup**: 여러 API 호출을 논리적으로 그룹화하여 멀티 에이전트 워크플로우 추적
- ⚡ **비동기 지원**: 동기/비동기 모두 완벽 지원 (async/await, generators)
- 🎯 **데코레이터 지원**: `@nora.trace_group` 데코레이터로 함수 단위 추적
- 🛡️ **안전한 동작**: 에러 발생 시에도 사용자 코드에 영향 없음

## 목차

- [설치](#설치)
- [빠른 시작](#빠른-시작)
- [nora.init() 사용법](#norainit-사용법)
- [@nora.trace_group 데코레이터](#noratrace_group-데코레이터)
- [with/async with context manager](#withasync-with-context-manager)
- [고급 사용법](#고급-사용법)
- [API 응답 형식](#api-응답-형식)
- [지원하는 AI 라이브러리](#지원하는-ai-라이브러리)

## 설치

```bash
pip install nora-observability
```

## 빠른 시작

### 기본 사용 (OpenAI)

```python
import nora
from openai import OpenAI

# 1. Nora 초기화 (단 한 줄!)
nora.init(api_key="YOUR_NORA_API_KEY")

# 2. OpenAI 클라이언트 사용 - 이제 모든 호출이 자동으로 추적됩니다!
client = OpenAI(api_key="YOUR_OPENAI_API_KEY")
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
# 출력: "Hello! How can I assist you today?"
```

**무슨 일이 일어났나요?**
- Nora가 OpenAI API 호출을 자동으로 감지
- 요청 파라미터(model, messages)와 응답(content, tokens) 수집
- 백엔드 서버로 trace 데이터 전송
- 대시보드에서 실시간 확인 가능

### Anthropic (Claude) 사용

```python
import nora
from anthropic import Anthropic

nora.init(api_key="YOUR_NORA_API_KEY")

client = Anthropic(api_key="YOUR_ANTHROPIC_API_KEY")
response = client.messages.create(
    model="claude-opus-4-5-20251101",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Explain quantum computing"}]
)

print(response.content[0].text)
```

### Google Gemini 사용

```python
import nora
from google import genai

nora.init(api_key="YOUR_NORA_API_KEY")

client = genai.Client(api_key="YOUR_GOOGLE_API_KEY")
response = client.models.generate_content(
    model="gemini-2.0-flash-exp",
    contents="Write a haiku about AI"
)

print(response.text)
```

---

## nora.init() 사용법

`nora.init()`은 Nora Observability를 초기화하고 AI 라이브러리를 자동 패치합니다.

### 기본 문법

```python
nora.init(
    api_key: str,                    # 필수
    api_url: str = "...",            # 선택
    auto_patch: bool = True,         # 선택
    traced_functions: List[str] = None,  # 선택
    service_url: str = None,         # 선택
    environment: str = "default"     # 선택
)
```

### 파라미터 상세 설명

#### `api_key` (필수)
- **타입**: `str`
- **설명**: Nora 백엔드 인증용 API 키
- **예시**:
  ```python
  nora.init(api_key="mOSAWtuWhb58tQXMxkyAU6rfUhHUZll465cCqIpaymQ")
  ```

#### `api_url` (선택)
- **타입**: `str`
- **기본값**: `"https://noraobservabilitybackend-staging.up.railway.app/v1"`
- **설명**: Trace 데이터를 전송할 백엔드 서버 URL
- **예시**:
  ```python
  # 프로덕션 서버 사용
  nora.init(
      api_key="your-key",
      api_url="https://api.nora-production.com/v1"
  )
  
  # 로컬 개발 서버 사용
  nora.init(
      api_key="your-key",
      api_url="http://localhost:8000/v1"
  )
  ```

#### `auto_patch` (선택)
- **타입**: `bool`
- **기본값**: `True`
- **설명**: AI 라이브러리 자동 패치 활성화 여부
- **예시**:
  ```python
  # 자동 패치 비활성화 (수동으로 trace 기록할 때)
  nora.init(api_key="your-key", auto_patch=False)
  ```

#### `traced_functions` (선택)
- **타입**: `List[str]`
- **기본값**: `None`
- **설명**: 자동으로 `trace_group`으로 감쌀 함수명 리스트
- **예시**:
  ```python
  # multi_agent_workflow와 process_data 함수 자동 추적
  nora.init(
      api_key="your-key",
      traced_functions=["multi_agent_workflow", "process_data"]
  )
  
  # 이제 이 함수들이 호출되면 자동으로 trace_group이 생성됨
  def multi_agent_workflow():
      # 여기서 발생하는 모든 AI 호출이 그룹으로 묶임
      agent1_response = openai_client.chat.completions.create(...)
      agent2_response = openai_client.chat.completions.create(...)
  ```

#### `service_url` (선택)
- **타입**: `str`
- **기본값**: `None`
- **설명**: 외부 피드백 서비스 URL (나중에 사용자 피드백 수집용)
- **예시**:
  ```python
  nora.init(
      api_key="your-key",
      service_url="https://my-app.com/api/feedback"
  )
  ```

#### `environment` (선택)
- **타입**: `str`
- **기본값**: `"default"`
- **설명**: 실행 환경 태그 (개발/스테이징/프로덕션 구분)
- **예시**:
  ```python
  import os
  
  # 환경별로 다른 태그 설정
  env = os.getenv("APP_ENV", "development")
  nora.init(
      api_key="your-key",
      environment=env  # "development", "staging", "production"
  )
  
  # 대시보드에서 환경별로 필터링 가능
  ```

### 실전 예시

#### 예시 1: 최소 설정 (프로덕션)
```python
import nora

nora.init(api_key="mOSAWtuWhb58tQXMxkyAU6rfUhHUZll465cCqIpaymQ")
```

#### 예시 2: 환경 변수 사용 (권장)
```python
import os
from dotenv import load_dotenv
import nora

load_dotenv()

nora.init(
    api_key=os.getenv("NORA_API_KEY"),
    environment=os.getenv("APP_ENV", "production")
)
```

#### 예시 3: 멀티 에이전트 자동 추적
```python
import nora

nora.init(
    api_key="your-key",
    traced_functions=["research_agent", "writer_agent", "reviewer_agent"],
    environment="production"
)

# 이제 이 함수들이 호출되면 자동으로 그룹으로 추적됨
def research_agent(query):
    return openai_client.chat.completions.create(...)

def writer_agent(research_result):
    return openai_client.chat.completions.create(...)

def reviewer_agent(draft):
    return openai_client.chat.completions.create(...)
```

#### 예시 4: 개발 환경 전체 설정
```python
import nora

nora.init(
    api_key="dev-api-key",
    api_url="http://localhost:8000/v1",
    traced_functions=["main_workflow"],
    environment="development"
)

# 프로그램 종료 전 남은 trace 데이터 즉시 전송
import atexit
atexit.register(lambda: nora.flush(sync=True))
```

---

## @nora.trace_group 데코레이터

함수를 데코레이터로 감싸서 해당 함수 내부의 모든 AI 호출을 하나의 그룹으로 추적합니다.

### 기본 문법

```python
@nora.trace_group(name="그룹이름", metadata={"key": "value"})
def my_function():
    # 이 함수 내 모든 AI 호출이 그룹으로 묶임
    pass
```

### 파라미터

- **`name`** (선택): 그룹 이름 (생략 시 함수 이름 사용)
- **`metadata`** (선택): 추가 메타데이터 딕셔너리

### 예시 1: 기본 사용 (동기 함수)

```python
import nora
from openai import OpenAI

nora.init(api_key="your-key")
client = OpenAI()

@nora.trace_group(name="summarize_article")
def summarize_article(article_text):
    """기사를 요약하는 함수"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a summarization expert."},
            {"role": "user", "content": f"Summarize this: {article_text}"}
        ]
    )
    return response.choices[0].message.content

# 함수 호출
summary = summarize_article("Long article text here...")
print(summary)
```

**대시보드에서 보이는 내용:**
- 그룹 이름: `summarize_article`
- 포함된 호출: 1개 (GPT-4o-mini)
- 토큰 사용량: 총합 표시
- 실행 시간: 함수 시작~종료

### 예시 2: 이름 생략 (함수 이름 자동 사용)

```python
@nora.trace_group  # 괄호 없이 직접 적용
def translate_text(text, target_lang):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Translate to {target_lang}: {text}"}]
    )
    return response.choices[0].message.content

# 그룹 이름이 자동으로 "translate_text"가 됩니다
```

### 예시 3: 메타데이터 추가

```python
@nora.trace_group(
    name="user_query_handler",
    metadata={"user_id": "user_123", "session_id": "sess_456"}
)
def handle_user_query(user_id, query):
    """사용자 쿼리 처리 - 메타데이터로 사용자 추적"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": query}]
    )
    return response.choices[0].message.content

# 대시보드에서 user_id, session_id로 필터링 가능
```

### 예시 4: 멀티 에이전트 워크플로우

```python
@nora.trace_group(name="multi_agent_research")
def multi_agent_research(topic):
    """3개의 AI 에이전트가 협업하는 리서치 워크플로우"""
    
    # Agent 1: 주제 분석
    analysis = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Analyze topic: {topic}"}]
    ).choices[0].message.content
    
    # Agent 2: 정보 수집
    research = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Research based on: {analysis}"}]
    ).choices[0].message.content
    
    # Agent 3: 최종 요약
    summary = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Summarize: {research}"}]
    ).choices[0].message.content
    
    return summary

result = multi_agent_research("Quantum Computing")
```

**대시보드 표시:**
```
그룹: multi_agent_research
├─ Execution 1: gpt-4o-mini (분석) - 120 tokens
├─ Execution 2: gpt-4o-mini (리서치) - 450 tokens
└─ Execution 3: gpt-4o-mini (요약) - 200 tokens
총 토큰: 770 tokens
총 시간: 3.2초
```

### 예시 5: 비동기 함수 (Async)

```python
@nora.trace_group(name="async_translate")
async def async_translate(text):
    """비동기 함수도 자동으로 처리됨"""
    from openai import AsyncOpenAI
    
    async_client = AsyncOpenAI()
    response = await async_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Translate: {text}"}]
    )
    return response.choices[0].message.content

# 사용
import asyncio
result = asyncio.run(async_translate("Hello world"))
```

### 예시 6: 제너레이터 함수

```python
@nora.trace_group(name="streaming_chat")
def streaming_chat(messages):
    """스트리밍 응답도 추적 가능"""
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        stream=True
    )
    
    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

# 사용
for text_chunk in streaming_chat([{"role": "user", "content": "Tell me a story"}]):
    print(text_chunk, end="")
```

### 예시 7: Tool Calling과 함께

```python
@nora.trace_group(name="weather_assistant")
def weather_assistant(city):
    """Tool calling을 포함한 복잡한 워크플로우"""
    
    tools = [{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather information",
            "parameters": {
                "type": "object",
                "properties": {"location": {"type": "string"}}
            }
        }
    }]
    
    # 1단계: AI가 tool 호출 요청
    response1 = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"What's the weather in {city}?"}],
        tools=tools
    )
    
    tool_call = response1.choices[0].message.tool_calls[0]
    
    # 2단계: Tool 실행 (실제 날씨 API 호출)
    weather_data = get_weather(location=city)
    
    # 3단계: Tool 결과로 최종 답변 생성
    response2 = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": f"What's the weather in {city}?"},
            response1.choices[0].message,
            {"role": "tool", "tool_call_id": tool_call.id, "content": weather_data}
        ]
    )
    
    return response2.choices[0].message.content

# 전체 플로우가 하나의 그룹으로 추적됨
answer = weather_assistant("Seoul")
```

---

## with/async with context manager

`with` 문이나 `async with` 문을 사용하여 코드 블록 단위로 AI 호출을 그룹화합니다.

### 기본 문법 (동기)

```python
with nora.trace_group(name="그룹이름", metadata={"key": "value"}):
    # 이 블록 내 모든 AI 호출이 그룹으로 묶임
    response1 = client.chat.completions.create(...)
    response2 = client.chat.completions.create(...)
```

### 비동기 문법

```python
async with nora.trace_group(name="그룹이름"):
    # 비동기 호출도 지원
    response1 = await async_client.chat.completions.create(...)
    response2 = await async_client.chat.completions.create(...)
```

### 예시 1: 기본 with 사용

```python
import nora
from openai import OpenAI

nora.init(api_key="your-key")
client = OpenAI()

# 사용자 요청 처리를 하나의 그룹으로 묶기
with nora.trace_group(name="user_request_handler"):
    # 의도 분석
    intent = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "I want to book a flight to Paris"}]
    ).choices[0].message.content
    
    # 세부 정보 추출
    details = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Extract flight details from: {intent}"}]
    ).choices[0].message.content
    
    print(f"Intent: {intent}")
    print(f"Details: {details}")
```

**대시보드 표시:**
```
그룹: user_request_handler
├─ gpt-4o-mini (의도 분석) - 0.8초, 95 tokens
└─ gpt-4o-mini (세부 정보) - 1.1초, 120 tokens
총 실행 시간: 1.9초
총 토큰: 215 tokens
상태: success ✓
```

### 예시 2: 메타데이터와 함께

```python
user_id = "user_12345"
session_id = "sess_abc"

with nora.trace_group(
    name="chat_conversation",
    metadata={
        "user_id": user_id,
        "session_id": session_id,
        "input": "How do I reset my password?"
    }
):
    # 대화 이력 포함한 응답 생성
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful support agent."},
            {"role": "user", "content": "How do I reset my password?"}
        ]
    )
    
    answer = response.choices[0].message.content
    print(answer)

# metadata로 대시보드에서 검색/필터 가능
```

### 예시 3: 에러 처리

```python
try:
    with nora.trace_group(name="risky_operation"):
        # 에러가 발생할 수 있는 AI 호출
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Some query"}]
        )
except Exception as e:
    print(f"Error occurred: {e}")
    # trace는 자동으로 status="error"로 기록됨
```

**대시보드 표시 (에러 시):**
```
그룹: risky_operation
상태: error ✗
에러: RateLimitError: Too many requests
실행 시간: 0.5초
```

### 예시 4: 중첩 그룹 (Nested Groups)

```python
# 외부 그룹: 전체 워크플로우
with nora.trace_group(name="document_processing"):
    
    # 내부 그룹 1: 문서 분석
    with nora.trace_group(name="analyze_document"):
        analysis = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Analyze this document..."}]
        ).choices[0].message.content
    
    # 내부 그룹 2: 요약 생성
    with nora.trace_group(name="generate_summary"):
        summary = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Summarize: {analysis}"}]
        ).choices[0].message.content
    
    print(summary)
```

**대시보드 계층 구조:**
```
document_processing (부모 그룹)
├─ analyze_document (자식 그룹)
│  └─ gpt-4o-mini - 1.2초, 200 tokens
└─ generate_summary (자식 그룹)
   └─ gpt-4o-mini - 0.9초, 150 tokens
```

### 예시 5: async with (비동기)

```python
from openai import AsyncOpenAI
import asyncio

async_client = AsyncOpenAI()

async def async_workflow():
    async with nora.trace_group(name="async_multi_query"):
        # 여러 비동기 호출을 병렬로 실행
        task1 = async_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Query 1"}]
        )
        
        task2 = async_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Query 2"}]
        )
        
        # 동시 실행
        responses = await asyncio.gather(task1, task2)
        
        return [r.choices[0].message.content for r in responses]

# 실행
results = asyncio.run(async_workflow())
print(results)
```

### 예시 6: 반복문에서 사용

```python
queries = ["What is AI?", "Explain ML", "Define DL"]

with nora.trace_group(name="batch_queries", metadata={"count": len(queries)}):
    results = []
    
    for i, query in enumerate(queries):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": query}]
        )
        results.append(response.choices[0].message.content)
        print(f"Query {i+1} done")
    
    # 3개의 AI 호출이 모두 하나의 그룹으로 추적됨
```

**대시보드 표시:**
```
그룹: batch_queries
메타데이터: count=3
├─ gpt-4o-mini (Query 1) - 0.7초, 80 tokens
├─ gpt-4o-mini (Query 2) - 0.8초, 95 tokens
└─ gpt-4o-mini (Query 3) - 0.6초, 70 tokens
총 토큰: 245 tokens
총 시간: 2.1초
```

### 예시 7: Tool Calling 전체 플로우

```python
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current weather",
        "parameters": {
            "type": "object",
            "properties": {"location": {"type": "string"}}
        }
    }
}]

def get_weather(location):
    # 실제 API 호출
    return f"Weather in {location}: Sunny, 22°C"

with nora.trace_group(name="weather_query", metadata={"input": "Seoul weather"}):
    # 1. AI가 tool 호출 결정
    response1 = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "What's the weather in Seoul?"}],
        tools=tools,
        tool_choice="auto"
    )
    
    tool_calls = response1.choices[0].message.tool_calls
    
    if tool_calls:
        # 2. Tool 실행
        tool_results = []
        for tool_call in tool_calls:
            func_name = tool_call.function.name
            func_args = json.loads(tool_call.function.arguments)
            result = get_weather(**func_args)
            tool_results.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": func_name,
                "content": result
            })
        
        # 3. Tool 결과로 최종 답변
        messages = [
            {"role": "user", "content": "What's the weather in Seoul?"},
            response1.choices[0].message.model_dump(),
            *tool_results
        ]
        
        response2 = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        
        final_answer = response2.choices[0].message.content
        print(final_answer)
```

**대시보드 표시:**
```
그룹: weather_query
입력: "Seoul weather"
├─ gpt-4o-mini (Tool 요청) - 0.5초, 50 tokens
│  └─ Tool: get_weather(location="Seoul")
└─ gpt-4o-mini (최종 답변) - 0.7초, 45 tokens
총 실행 시간: 1.2초
총 토큰: 95 tokens
상태: success ✓
출력: "The weather in Seoul is sunny with a temperature of 22°C."
```

---

## 고급 사용법

### 프로그램 종료 시 데이터 플러시

```python
import nora
import atexit

nora.init(api_key="your-key")

# 프로그램 종료 시 자동으로 남은 trace 전송
atexit.register(lambda: nora.flush(sync=True))
```

### Trace 일시 중지/재개

```python
nora.init(api_key="your-key")

# 일시적으로 trace 비활성화
nora.disable()

# 이 호출은 추적되지 않음
response = client.chat.completions.create(...)

# 다시 활성화
nora.enable()

# 이제 다시 추적됨
response = client.chat.completions.create(...)
```

### Trace 데이터 조회

```python
# 모든 trace group 조회
groups = nora.get_trace_groups()
for group in groups:
    print(f"Group: {group['name']}")
    print(f"  Traces: {group['trace_count']}")
    print(f"  Tokens: {group['total_tokens']}")
    print(f"  Duration: {group['total_duration']}s")

# 특정 그룹의 trace 찾기
traces = nora.find_traces_by_group("multi_agent_workflow")
for trace in traces:
    print(f"Model: {trace['model']}, Tokens: {trace['tokens_used']}")

# 그룹 ID로 검색
traces = nora.find_traces_by_group_id("group-uuid-here")
```

---

## API 응답 형식

### Trace 생성 응답

**POST** `/v1/traces/`

```json
{
  "id": "44bcdebf-4418-44c2-ad78-9dd19b990e2f",
  "trace_name": "multi_agent_workflow",
  "input": "사용자 요청 텍스트",
  "output": null,
  "latency": null,
  "tokens": null,
  "cost": null,
  "status": "pending",
  "environment": "production",
  "created_at": "2025-12-16T04:15:30.123Z",
  "updated_at": "2025-12-16T04:15:30.123Z"
}
```

### Execution Span 생성 응답

**POST** `/v1/executions/`

```json
{
  "id": "exec-uuid-123",
  "trace_id": "44bcdebf-4418-44c2-ad78-9dd19b990e2f",
  "span_name": "openai_gpt-4o-mini",
  "span_data": {
    "id": "chatcmpl-xyz",
    "timestamp": "2025-12-16T04:15:31.456Z",
    "provider": "openai",
    "model": "gpt-4o-mini",
    "prompt": "User: Hello, how are you?",
    "response": "Assistant: I'm doing well, thank you!",
    "metadata": {
      "trace_group": {
        "id": "group-uuid-456",
        "name": "multi_agent_workflow"
      }
    },
    "start_time": 1734324931.123,
    "end_time": 1734324932.456,
    "duration": 1.333,
    "tokens_used": 25,
    "finish_reason": "stop",
    "response_id": "chatcmpl-xyz",
    "system_fingerprint": "fp_abc123",
    "tool_calls": null,
    "environment": "production"
  },
  "created_at": "2025-12-16T04:15:32.789Z"
}
```

### Trace 업데이트 응답

**PATCH** `/v1/traces/{trace_id}`

```json
{
  "id": "44bcdebf-4418-44c2-ad78-9dd19b990e2f",
  "trace_name": "multi_agent_workflow",
  "input": "사용자 요청 텍스트",
  "output": "최종 AI 응답 결과",
  "latency": 3.245,
  "tokens": {
    "total_tokens": 150,
    "prompt_tokens": 80,
    "completion_tokens": 70
  },
  "cost": 0.00045,
  "status": "success",
  "environment": "production",
  "created_at": "2025-12-16T04:15:30.123Z",
  "updated_at": "2025-12-16T04:15:33.456Z"
}
```

### OpenAI 응답 예시 (자동 추적)

```json
{
  "id": "chatcmpl-CnGgzl3lTNCnFJdhxUUdKcU9k3u1N",
  "choices": [
    {
      "finish_reason": "tool_calls",
      "index": 0,
      "message": {
        "content": null,
        "role": "assistant",
        "tool_calls": [
          {
            "id": "call_Gu6m4p8lTxey883A6lGaXeWP",
            "function": {
              "arguments": "{\"location\": \"Seoul, South Korea\"}",
              "name": "get_weather"
            },
            "type": "function"
          },
          {
            "id": "call_N0P1bFGIdpaEylgS35rSkb37",
            "function": {
              "arguments": "{\"location\": \"Tokyo, Japan\"}",
              "name": "get_weather"
            },
            "type": "function"
          }
        ]
      }
    }
  ],
  "created": 1765858273,
  "model": "gpt-4o-mini-2024-07-18",
  "object": "chat.completion",
  "service_tier": "default",
  "system_fingerprint": "fp_11f3029f6b",
  "usage": {
    "completion_tokens": 50,
    "prompt_tokens": 80,
    "total_tokens": 130,
    "completion_tokens_details": {
      "accepted_prediction_tokens": 0,
      "audio_tokens": 0,
      "reasoning_tokens": 0,
      "rejected_prediction_tokens": 0
    },
    "prompt_tokens_details": {
      "audio_tokens": 0,
      "cached_tokens": 0
    }
  }
}
```

**위 응답이 Nora로 전송되는 형식:**

```json
{
  "trace_id": "parent-trace-uuid",
  "span_name": "openai_gpt-4o-mini",
  "span_data": {
    "id": "chatcmpl-CnGgzl3lTNCnFJdhxUUdKcU9k3u1N",
    "provider": "openai",
    "model": "gpt-4o-mini-2024-07-18",
    "prompt": "User: What's the weather in Seoul and Tokyo?",
    "response": null,
    "tokens_used": 130,
    "finish_reason": "tool_calls",
    "tool_calls": [
      {
        "id": "call_Gu6m4p8lTxey883A6lGaXeWP",
        "function": {
          "name": "get_weather",
          "arguments": "{\"location\": \"Seoul, South Korea\"}"
        }
      },
      {
        "id": "call_N0P1bFGIdpaEylgS35rSkb37",
        "function": {
          "name": "get_weather",
          "arguments": "{\"location\": \"Tokyo, Japan\"}"
        }
      }
    ],
    "metadata": {
      "usage": {
        "total_tokens": 130,
        "prompt_tokens": 80,
        "completion_tokens": 50
      }
    },
    "duration": 1.234,
    "environment": "production"
  }
}
```

### 에러 응답 예시

```json
{
  "detail": "Unauthorized"
}
```

**HTTP 상태 코드:**
- `200`: 성공
- `201`: 생성 성공
- `401`: 인증 실패 (잘못된 API 키)
- `400`: 잘못된 요청
- `500`: 서버 에러

---

## 지원하는 AI 라이브러리

### OpenAI
- ✅ Chat Completions API (`gpt-4`, `gpt-4o`, `gpt-4o-mini`, `gpt-3.5-turbo` 등)
- ✅ Tool/Function Calling
- ✅ Streaming 응답
- ✅ 동기/비동기 (`AsyncOpenAI`)
- ✅ 토큰 사용량 추적 (reasoning tokens, cached tokens 포함)
- ✅ 비용 계산

**지원 메서드:**
```python
client.chat.completions.create(...)  # 동기
await async_client.chat.completions.create(...)  # 비동기
```

### Anthropic (Claude)
- ✅ Messages API (`claude-3-5-sonnet`, `claude-opus-4-5`, 등)
- ✅ Tool Calling
- ✅ Streaming 응답
- ✅ 동기/비동기
- ✅ 토큰 사용량 추적

**지원 메서드:**
```python
client.messages.create(...)  # 동기
await async_client.messages.create(...)  # 비동기
```

### Google Gemini
- ✅ Generate Content API (`gemini-2.0-flash`, `gemini-pro` 등)
- ✅ Tool Calling
- ✅ 동기/비동기
- ✅ 토큰 사용량 추적

**지원 메서드:**
```python
client.models.generate_content(...)  # 동기
await client.aio.models.generate_content(...)  # 비동기
```

---

## 실전 예시 모음

### 예시 1: RAG (Retrieval-Augmented Generation)

```python
import nora
from openai import OpenAI

nora.init(api_key="your-key")
client = OpenAI()

@nora.trace_group(name="rag_query")
def rag_query(user_question, context_docs):
    """RAG 파이프라인 전체를 하나의 그룹으로 추적"""
    
    # 1. 관련 문서 임베딩 및 검색 (외부 로직)
    relevant_context = "\n".join(context_docs)
    
    # 2. 컨텍스트 포함 프롬프트 생성
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Answer based on the context."},
            {"role": "user", "content": f"Context:\n{relevant_context}\n\nQuestion: {user_question}"}
        ]
    )
    
    return response.choices[0].message.content

answer = rag_query(
    "What is machine learning?",
    ["Doc1: ML is...", "Doc2: AI involves..."]
)
```

### 예시 2: 멀티 에이전트 시스템

```python
@nora.trace_group(name="multi_agent_system")
async def multi_agent_workflow(task):
    """3개 에이전트가 순차적으로 작업"""
    from openai import AsyncOpenAI
    
    async_client = AsyncOpenAI()
    
    # Agent 1: Planner
    plan = await async_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Create a plan for: {task}"}]
    )
    plan_text = plan.choices[0].message.content
    
    # Agent 2: Executor
    execution = await async_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Execute plan: {plan_text}"}]
    )
    execution_result = execution.choices[0].message.content
    
    # Agent 3: Reviewer
    review = await async_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Review result: {execution_result}"}]
    )
    
    return review.choices[0].message.content

import asyncio
result = asyncio.run(multi_agent_workflow("Build a website"))
```

### 예시 3: 배치 처리

```python
documents = ["Doc 1 text...", "Doc 2 text...", "Doc 3 text..."]

with nora.trace_group(name="batch_summarization", metadata={"count": len(documents)}):
    summaries = []
    
    for i, doc in enumerate(documents):
        summary = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Summarize: {doc}"}]
        ).choices[0].message.content
        
        summaries.append(summary)
        print(f"Processed {i+1}/{len(documents)}")
    
    # 모든 요약을 하나의 그룹으로 추적
```

### 예시 4: A/B 테스트

```python
import random

user_query = "Explain photosynthesis"

# 랜덤으로 모델 선택
model = random.choice(["gpt-4o-mini", "gpt-4o"])

with nora.trace_group(
    name="ab_test",
    metadata={"model": model, "variant": "A" if model == "gpt-4o-mini" else "B"}
):
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": user_query}]
    )
    
    print(f"Model: {model}")
    print(response.choices[0].message.content)

# 대시보드에서 variant별 성능 비교 가능
```

### 예시 5: 에러 재시도 로직

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
@nora.trace_group(name="robust_query")
def robust_ai_call(prompt):
    """재시도 로직 포함 - 각 시도가 모두 추적됨"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

try:
    result = robust_ai_call("Tell me about quantum physics")
except Exception as e:
    print(f"Failed after retries: {e}")
```

---

## 트러블슈팅

### 문제: Trace가 대시보드에 표시되지 않음

**해결 방법:**
1. API 키 확인
   ```python
   nora.init(api_key="올바른_키")
   ```

2. 네트워크 연결 확인
   ```python
   import requests
   response = requests.get("https://noraobservabilitybackend-staging.up.railway.app/v1/health")
   print(response.status_code)  # 200이어야 함
   ```

3. 수동으로 flush
   ```python
   nora.flush(sync=True)
   ```

### 문제: 401 Unauthorized 에러

**원인:** 잘못된 API 키

**해결:**
```python
# 환경 변수에서 로드
import os
nora.init(api_key=os.getenv("NORA_API_KEY"))
```

### 문제: Tool calls가 추적되지 않음

**확인 사항:**
1. `trace_group` 안에서 호출했는지 확인
2. Tool 응답을 올바른 형식으로 전달했는지 확인

```python
with nora.trace_group(name="tool_workflow"):
    # 1. Tool call 요청
    response1 = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[...],
        tools=[...]
    )
    
    # 2. Tool 실행
    tool_result = execute_tool(...)
    
    # 3. 결과 전달 (올바른 형식)
    response2 = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            ...,
            response1.choices[0].message.model_dump(),  # 중요!
            {"role": "tool", "tool_call_id": "...", "content": tool_result}
        ]
    )
```

### 문제: 비동기 함수에서 작동하지 않음

**해결:**
```python
# async with 사용
async with nora.trace_group(name="async_workflow"):
    response = await async_client.chat.completions.create(...)

# 또는 데코레이터
@nora.trace_group(name="async_func")
async def my_async_function():
    ...
```

---

## 베스트 프랙티스

### 1. 환경 변수로 API 키 관리

```python
# .env 파일
NORA_API_KEY=your-api-key-here
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# 코드
from dotenv import load_dotenv
import os

load_dotenv()
nora.init(api_key=os.getenv("NORA_API_KEY"))
```

### 2. 의미 있는 그룹 이름 사용

```python
# 나쁜 예
with nora.trace_group(name="func1"):
    ...

# 좋은 예
with nora.trace_group(name="user_onboarding_email_generation"):
    ...
```

### 3. 메타데이터 활용

```python
with nora.trace_group(
    name="customer_support",
    metadata={
        "user_id": user.id,
        "ticket_id": ticket.id,
        "priority": ticket.priority,
        "category": ticket.category
    }
):
    response = generate_support_response(ticket)
```

### 4. 프로덕션 환경 구분

```python
import os

env = os.getenv("ENVIRONMENT", "development")
nora.init(
    api_key=os.getenv("NORA_API_KEY"),
    environment=env
)
```

### 5. 에러 핸들링

```python
try:
    with nora.trace_group(name="critical_operation"):
        result = client.chat.completions.create(...)
except Exception as e:
    # Trace는 자동으로 error 상태로 기록됨
    logger.error(f"AI call failed: {e}")
    # Fallback 로직
```

---

## 프로젝트 구조

```
nora/
├── __init__.py              # 메인 API (init, trace_group, tool 등)
├── client.py                # NoraClient 및 TraceGroup 구현
├── utils.py                 # 공통 유틸리티 함수
├── openai/                  # OpenAI 전용 모듈
│   ├── __init__.py
│   ├── types.py             # 타입 정의
│   ├── utils.py             # 응답 파싱 유틸리티
│   ├── metadata_builder.py  # Trace 메타데이터 구성
│   ├── tool_tracer.py       # Tool 실행 자동 감지
│   └── streaming.py         # 스트리밍 응답 처리
├── anthropic/               # Anthropic 전용 모듈
│   ├── __init__.py
│   ├── types.py
│   ├── utils.py
│   ├── metadata_builder.py
│   └── streaming.py
├── gemini/                  # Gemini 전용 모듈
│   ├── __init__.py
│   ├── types.py
│   ├── utils.py
│   ├── metadata_builder.py
│   └── streaming.py
└── patches/                 # AI 라이브러리 패치
    ├── __init__.py
    ├── openai_patch.py      # OpenAI API 패치
    ├── anthropic_patch.py   # Anthropic API 패치
    └── gemini_patch.py      # Gemini API 패치
```

## 개발

### 의존성 설치

```bash
# 기본 설치
pip install nora-observability

# 개발 환경 설치
pip install -e ".[dev]"
```

### 테스트 실행

```bash
# 전체 테스트
pytest tests/ -v

# 특정 테스트만
pytest tests/test_decorator_and_with.py -v

# 커버리지 포함
pytest tests/ --cov=nora --cov-report=html
```

### 코드 품질

```bash
# 포맷팅
black nora/

# Linting
ruff check nora/

# 타입 체크
mypy nora/
```

## 아키텍처

### 자동 패치 메커니즘

Nora SDK는 monkey-patching을 사용하여 AI 라이브러리를 투명하게 가로챕니다:

1. **초기화**: `nora.init()` 호출 시 `patches/` 모듈의 패치 함수들이 실행됨
2. **메서드 래핑**: 원본 API 메서드(`chat.completions.create` 등)를 래퍼 함수로 교체
3. **요청 인터셉트**: API 호출 시점에 요청 파라미터 수집 (model, messages, tools 등)
4. **응답 처리**: 응답에서 텍스트, tool calls, 토큰 사용량 추출
5. **Trace 생성**: `NoraClient.trace()` 메서드로 trace 데이터 생성
6. **배치 전송**: 백그라운드 스레드에서 배치로 서버에 전송

**패치 예시 (간소화):**
```python
# patches/openai_patch.py
original_create = openai.chat.completions.create

def patched_create(*args, **kwargs):
    start_time = time.time()
    response = original_create(*args, **kwargs)  # 원본 호출
    end_time = time.time()
    
    # Trace 데이터 수집
    client = get_nora_client()
    client.trace(
        provider="openai",
        model=kwargs.get("model"),
        prompt=format_messages(kwargs.get("messages")),
        response=response.choices[0].message.content,
        tokens_used=response.usage.total_tokens,
        start_time=start_time,
        end_time=end_time
    )
    
    return response

# 패치 적용
openai.chat.completions.create = patched_create
```

### TraceGroup 동작 원리

`TraceGroup`은 컨텍스트 관리자로, 블록 내의 모든 trace를 하나로 묶습니다:

1. **진입** (`__enter__`):
   - 고유 `group_id` 생성
   - 백엔드에 pending trace 생성 → `trace_id` 받음
   - 현재 그룹을 `ContextVar`에 저장
   - 자동 flush 비활성화

2. **실행 중**:
   - AI 호출마다 `client.trace()` 실행
   - 현재 그룹 확인 → trace 데이터에 `trace_group` 메타데이터 추가
   - `_send_execution_span()`으로 즉시 백엔드에 전송

3. **종료** (`__exit__`):
   - 그룹 내 모든 trace 집계 (토큰, 비용, 출력)
   - 백엔드 trace를 `success` 또는 `error` 상태로 업데이트
   - 자동 flush 재개

**플로우 다이어그램:**
```
nora.init()
    ↓
[User Code]
    ↓
with trace_group("my_group"):  ← __enter__: POST /traces/ (pending)
    ↓
    AI Call 1  → client.trace() → POST /executions/ (span 1)
    ↓
    AI Call 2  → client.trace() → POST /executions/ (span 2)
    ↓
                                ← __exit__: PATCH /traces/{id} (success)
```

### 비동기 처리

- **스레드 사용**: Trace 전송은 별도 daemon 스레드에서 비동기 실행
- **블로킹 방지**: 메인 스레드는 AI 응답 대기만 하고, trace 전송은 백그라운드
- **에러 격리**: Trace 전송 실패 시 메인 코드에 영향 없음

```python
def _send_execution_span(trace_id, span_data):
    def _send():
        try:
            requests.post(url, json=payload)
        except Exception as e:
            print(f"Warning: {e}")
    
    thread = threading.Thread(target=_send, daemon=True)
    thread.start()  # 비동기 전송
```

---

## 라이선스

MIT License

---

## 기여하기

이슈 및 PR은 GitHub에서 환영합니다:
- Repository: `Kr-TeamWise/observability_sdk`
- Issues: [GitHub Issues](https://github.com/Kr-TeamWise/observability_sdk/issues)

---

## 변경 로그

### v1.0.19 (2025-12-16)
- ✨ Execution span 즉시 전송 기능 추가
- 🐛 Token aggregation 버그 수정 (None 처리)
- 🧪 테스트 스위트 전체 재작성
- 📝 README 대폭 업데이트

### v1.0.17 (2024-12-14)
- ✨ Environment 파라미터 추가
- 🐛 Trace group 메타데이터 개선

### v1.0.16 (2024-12-13)
- ✨ Service URL 등록 기능
- 🐛 버그 수정

---

## 지원

- 📧 이메일: support@nora.ai
- 💬 Discord: [Nora Community](https://discord.gg/nora)
- 📚 문서: [docs.nora.ai](https://docs.nora.ai)

