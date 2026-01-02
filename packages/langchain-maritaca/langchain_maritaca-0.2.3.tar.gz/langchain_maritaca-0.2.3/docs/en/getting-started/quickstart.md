# Quick Start

Get started with langchain-maritaca in 5 minutes.

## Prerequisites

1. Python 3.9+
2. Maritaca AI API key ([get one here](https://chat.maritaca.ai/))

## Step 1: Installation

```bash
pip install langchain-maritaca
```

## Step 2: Configure API Key

```bash
export MARITACA_API_KEY="your-api-key"
```

## Step 3: First Example

```python
from langchain_maritaca import ChatMaritaca

# Create model (uses sabia-3.1 by default)
model = ChatMaritaca()

# Simple call
response = model.invoke("What is Maritaca AI?")
print(response.content)
```

## Complete Examples

### Chat with Messages

```python
from langchain_maritaca import ChatMaritaca
from langchain_core.messages import HumanMessage, SystemMessage

model = ChatMaritaca()

messages = [
    SystemMessage(content="You are a helpful assistant."),
    HumanMessage(content="Tell me about Brazil.")
]

response = model.invoke(messages)
print(response.content)
```

### Streaming

```python
from langchain_maritaca import ChatMaritaca

model = ChatMaritaca()

for chunk in model.stream("Tell me a short story."):
    print(chunk.content, end="", flush=True)
```

### With Parameters

```python
from langchain_maritaca import ChatMaritaca

model = ChatMaritaca(
    model="sabia-3.1",
    temperature=0.7,
    max_tokens=500,
)

response = model.invoke("Write a poem about AI.")
print(response.content)
```

### Tool Calling

```python
from langchain_maritaca import ChatMaritaca
from pydantic import BaseModel, Field

# Define tool as Pydantic model
class GetWeather(BaseModel):
    """Gets the weather for a city."""
    city: str = Field(description="City name")

model = ChatMaritaca()
model_with_tools = model.bind_tools([GetWeather])

response = model_with_tools.invoke("What's the weather in Sao Paulo?")

if response.tool_calls:
    print(f"Tool: {response.tool_calls[0]['name']}")
    print(f"Args: {response.tool_calls[0]['args']}")
```

## What's Next?

<div class="grid cards" markdown>

- [:octicons-gear-24: Configuration](configuration.md)

    Learn all available options

- [:octicons-book-24: Basic Usage](../guide/basic-usage.md)

    Usage patterns and best practices

- [:octicons-tools-24: Tool Calling](../guide/tool-calling.md)

    Build intelligent agents

- [:octicons-zap-24: Streaming](../guide/streaming.md)

    Real-time responses

</div>
