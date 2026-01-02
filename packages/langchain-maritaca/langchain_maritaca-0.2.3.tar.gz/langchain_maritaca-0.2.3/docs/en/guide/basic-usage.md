# Basic Usage

Learn how to use ChatMaritaca effectively.

## Message Types

LangChain uses different message types for conversations:

```python
from langchain_core.messages import (
    HumanMessage,    # User message
    AIMessage,       # Assistant message
    SystemMessage,   # System instruction
    ToolMessage,     # Tool response
)
```

## Simple Usage

### Single Message

```python
from langchain_maritaca import ChatMaritaca

model = ChatMaritaca()
response = model.invoke("Hello!")
print(response.content)
```

### With Message Types

```python
from langchain_maritaca import ChatMaritaca
from langchain_core.messages import HumanMessage

model = ChatMaritaca()
response = model.invoke([HumanMessage(content="Hello!")])
print(response.content)
```

### With System Prompt

```python
from langchain_maritaca import ChatMaritaca
from langchain_core.messages import HumanMessage, SystemMessage

model = ChatMaritaca()

messages = [
    SystemMessage(content="You are a helpful assistant who responds formally."),
    HumanMessage(content="How are you?")
]

response = model.invoke(messages)
print(response.content)
```

## Conversations with History

```python
from langchain_maritaca import ChatMaritaca
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

model = ChatMaritaca()

messages = [
    SystemMessage(content="You are a helpful assistant."),
    HumanMessage(content="My name is John."),
    AIMessage(content="Hello John! How can I help you?"),
    HumanMessage(content="What is my name?"),
]

response = model.invoke(messages)
print(response.content)  # "Your name is John!"
```

## Using Tuples (Shortcut)

```python
from langchain_maritaca import ChatMaritaca

model = ChatMaritaca()

messages = [
    ("system", "You are a helpful assistant."),
    ("human", "Hello!"),
]

response = model.invoke(messages)
print(response.content)
```

## Response Metadata

```python
from langchain_maritaca import ChatMaritaca

model = ChatMaritaca()
response = model.invoke("Hello!")

# Response content
print(response.content)

# Usage (tokens)
print(response.usage_metadata)
# {'input_tokens': 5, 'output_tokens': 10, 'total_tokens': 15}

# Model metadata
print(response.response_metadata)
# {'model': 'sabia-3.1', 'finish_reason': 'stop'}
```

## Batch Processing

Process multiple messages simultaneously:

```python
from langchain_maritaca import ChatMaritaca

model = ChatMaritaca()

questions = [
    [("human", "What is 2+2?")],
    [("human", "What is the capital of Brazil?")],
    [("human", "Who wrote Dom Casmurro?")],
]

responses = model.batch(questions)
for r in responses:
    print(r.content)
```

## Best Practices

### 1. Use System Prompt

```python
messages = [
    ("system", "You are an expert in Brazilian history. Answer concisely."),
    ("human", "Who was Tiradentes?"),
]
```

### 2. Manage History

```python
MAX_HISTORY = 10

if len(history) > MAX_HISTORY * 2:
    history = history[-(MAX_HISTORY * 2):]
```

### 3. Handle Errors

```python
import httpx

try:
    response = model.invoke(messages)
except httpx.HTTPStatusError as e:
    if e.response.status_code == 429:
        print("Rate limit exceeded")
    elif e.response.status_code == 401:
        print("Invalid API key")
except httpx.TimeoutException:
    print("Request timeout")
```

### 4. Configure Appropriately

```python
# For consistent answers
model = ChatMaritaca(temperature=0)

# For chatbots
model = ChatMaritaca(temperature=0.7, max_tokens=500)

# For creative generation
model = ChatMaritaca(temperature=1.2)
```

## Next Steps

- [Streaming](streaming.md) - Real-time responses
- [Async](async.md) - Async support
- [Tool Calling](tool-calling.md) - Function calling
