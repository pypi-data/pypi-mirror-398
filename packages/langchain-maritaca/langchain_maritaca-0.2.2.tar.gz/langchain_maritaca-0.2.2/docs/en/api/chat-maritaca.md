# ChatMaritaca

Main class for interacting with Maritaca AI language models.

## Import

```python
from langchain_maritaca import ChatMaritaca
```

## Initialization

```python
model = ChatMaritaca(
    model="sabia-3.1",
    temperature=0.7,
    max_tokens=None,
    api_key=None,  # Uses MARITACA_API_KEY from environment
)
```

## Parameters

### Model Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `str` | `"sabia-3.1"` | Model name to use |
| `temperature` | `float` | `0.7` | Controls randomness (0.0-2.0) |
| `max_tokens` | `int \| None` | `None` | Maximum tokens in response |
| `top_p` | `float` | `0.9` | Nucleus sampling |
| `frequency_penalty` | `float` | `0.0` | Frequency penalty (-2.0 to 2.0) |
| `presence_penalty` | `float` | `0.0` | Presence penalty (-2.0 to 2.0) |
| `stop_sequences` | `list[str] \| None` | `None` | Stop tokens |
| `n` | `int` | `1` | Number of completions |

### Client Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | `str \| None` | `None` | API key (or env var) |
| `base_url` | `str` | `"https://chat.maritaca.ai/api"` | API base URL |
| `timeout` | `float` | `60.0` | Timeout in seconds |
| `max_retries` | `int` | `2` | Maximum retries |
| `streaming` | `bool` | `False` | Enable streaming by default |

### Tool Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tools` | `list[dict] \| None` | `None` | List of available tools |
| `tool_choice` | `str \| dict \| None` | `None` | Tool selection control |

## Methods

### invoke()

Executes a single call to the model.

```python
def invoke(
    messages: list[BaseMessage],
    stop: list[str] | None = None,
    **kwargs
) -> AIMessage
```

**Example:**

```python
from langchain_core.messages import HumanMessage

response = model.invoke([HumanMessage(content="Hello!")])
print(response.content)
```

### ainvoke()

Async version of `invoke()`.

```python
async def ainvoke(
    messages: list[BaseMessage],
    stop: list[str] | None = None,
    **kwargs
) -> AIMessage
```

**Example:**

```python
response = await model.ainvoke([HumanMessage(content="Hello!")])
```

### stream()

Returns an iterator of response chunks.

```python
def stream(
    messages: list[BaseMessage],
    stop: list[str] | None = None,
    **kwargs
) -> Iterator[AIMessageChunk]
```

**Example:**

```python
for chunk in model.stream([HumanMessage(content="Tell a story.")]):
    print(chunk.content, end="")
```

### astream()

Async version of `stream()`.

```python
async def astream(
    messages: list[BaseMessage],
    stop: list[str] | None = None,
    **kwargs
) -> AsyncIterator[AIMessageChunk]
```

**Example:**

```python
async for chunk in model.astream([HumanMessage(content="...")]):
    print(chunk.content, end="")
```

### batch()

Processes multiple conversations.

```python
def batch(
    inputs: list[list[BaseMessage]],
    config: dict | None = None,
    **kwargs
) -> list[AIMessage]
```

**Example:**

```python
responses = model.batch([
    [HumanMessage(content="Question 1")],
    [HumanMessage(content="Question 2")],
])
```

### abatch()

Async version of `batch()`.

### bind_tools()

Binds tools to the model for function calling.

```python
def bind_tools(
    tools: Sequence[dict | type | Callable | BaseTool],
    *,
    tool_choice: str | dict | None = None,
    **kwargs
) -> Runnable
```

**Parameters:**

- `tools`: List of tools (Pydantic models, functions, or dicts)
- `tool_choice`: Selection control
  - `"auto"`: Model decides (default)
  - `"required"`: Forces tool use
  - `{"type": "function", "function": {"name": "..."}}`: Specific tool

**Example:**

```python
from pydantic import BaseModel, Field

class GetWeather(BaseModel):
    """Gets the weather."""
    city: str = Field(description="City name")

model_with_tools = model.bind_tools([GetWeather])
response = model_with_tools.invoke([HumanMessage(content="Weather in SP?")])
```

## Properties

### _llm_type

```python
@property
def _llm_type(self) -> str
```

Returns `"maritaca-chat"`.

### _default_params

```python
@property
def _default_params(self) -> dict[str, Any]
```

Returns default parameters for API calls.

### lc_secrets

```python
@property
def lc_secrets(self) -> dict[str, str]
```

Maps secret environment variables.

## Return Types

### AIMessage

Standard model response:

```python
AIMessage(
    content="Response text",
    tool_calls=[...],  # If there are tool calls
    usage_metadata={
        "input_tokens": 10,
        "output_tokens": 20,
        "total_tokens": 30,
    },
    response_metadata={
        "model": "sabia-3.1",
        "finish_reason": "stop",
    },
)
```

### AIMessageChunk

Streaming chunk:

```python
AIMessageChunk(
    content="Token ",
    response_metadata={...},  # Only in final chunk
)
```

## Exceptions

| Exception | Cause |
|-----------|-------|
| `httpx.HTTPStatusError` | HTTP error (401, 429, 500, etc.) |
| `httpx.TimeoutException` | Request timeout |
| `ValueError` | Invalid parameters |
| `RuntimeError` | Failure after retries |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `MARITACA_API_KEY` | Authentication key |
| `MARITACA_API_BASE` | Custom base URL |
