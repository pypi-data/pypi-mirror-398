# Configuration

Complete guide to all ChatMaritaca configuration options.

## Basic Parameters

```python
from langchain_maritaca import ChatMaritaca

model = ChatMaritaca(
    model="sabia-3.1",          # Model to use
    temperature=0.7,            # Randomness (0.0-2.0)
    max_tokens=1000,            # Maximum response tokens
    api_key="your-key",         # API key (or env var)
)
```

## Model Parameters

### model

Model name to use.

| Value | Description |
|-------|-------------|
| `sabia-3.1` | Most powerful model (default) |
| `sabiazinho-3.1` | Faster, more economical |

```python
model = ChatMaritaca(model="sabiazinho-3.1")
```

### temperature

Controls randomness of responses. Higher values = more creative.

| Value | Behavior |
|-------|----------|
| `0.0` | Deterministic, consistent |
| `0.7` | Balanced (default) |
| `1.0+` | More creative, varied |

```python
# Deterministic responses
model = ChatMaritaca(temperature=0)

# Creative responses
model = ChatMaritaca(temperature=1.2)
```

### max_tokens

Maximum number of tokens in response. `None` = no limit.

```python
model = ChatMaritaca(max_tokens=500)
```

### top_p

Nucleus sampling. Controls diversity of responses.

```python
model = ChatMaritaca(top_p=0.9)  # Default
```

### frequency_penalty

Penalty for repeating tokens. Range: -2.0 to 2.0.

```python
model = ChatMaritaca(frequency_penalty=0.5)
```

### presence_penalty

Penalty for talking about new topics. Range: -2.0 to 2.0.

```python
model = ChatMaritaca(presence_penalty=0.5)
```

### stop_sequences

Tokens that stop generation.

```python
model = ChatMaritaca(stop_sequences=["END", "###"])
```

## Client Parameters

### api_key

API key. If not provided, uses `MARITACA_API_KEY` environment variable.

```python
model = ChatMaritaca(api_key="your-key")
```

### base_url

Custom API base URL.

```python
model = ChatMaritaca(base_url="https://custom.api.com")
```

### timeout

Request timeout in seconds.

```python
model = ChatMaritaca(timeout=120.0)  # 2 minutes
```

### max_retries

Number of automatic retries on failure.

```python
model = ChatMaritaca(max_retries=3)
```

### streaming

Enable streaming by default.

```python
model = ChatMaritaca(streaming=True)
```

## Tool Parameters

### tools

List of available tools (function calling).

```python
tools = [{"type": "function", "function": {...}}]
model = ChatMaritaca(tools=tools)
```

### tool_choice

Tool selection control.

| Value | Behavior |
|-------|----------|
| `"auto"` | Model decides (default) |
| `"required"` | Forces tool use |
| `{"type": "function", ...}` | Specific tool |

```python
model = ChatMaritaca(tool_choice="required")
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `MARITACA_API_KEY` | Authentication key |
| `MARITACA_API_BASE` | Custom base URL |

## Common Configurations

### Chatbot

```python
model = ChatMaritaca(
    model="sabia-3.1",
    temperature=0.7,
    max_tokens=500,
)
```

### Consistent Answers

```python
model = ChatMaritaca(
    model="sabia-3.1",
    temperature=0,
    max_tokens=1000,
)
```

### Creative Generation

```python
model = ChatMaritaca(
    model="sabia-3.1",
    temperature=1.2,
    top_p=0.95,
    frequency_penalty=0.5,
)
```

### Fast and Economical

```python
model = ChatMaritaca(
    model="sabiazinho-3.1",
    temperature=0.5,
    max_tokens=200,
)
```

### Agent with Tools

```python
from pydantic import BaseModel

class MyTool(BaseModel):
    """Tool description."""
    param: str

model = ChatMaritaca().bind_tools(
    [MyTool],
    tool_choice="auto"
)
```

## Next Steps

- [Basic Usage](../guide/basic-usage.md) - Usage patterns
- [Tool Calling](../guide/tool-calling.md) - Function calling
- [Streaming](../guide/streaming.md) - Real-time responses
