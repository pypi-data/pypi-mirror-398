# Streaming

Stream tokens in real-time for better user experience.

## Why Streaming?

- **Better UX**: Users see responses as they're generated
- **Perceived latency**: Feels faster than waiting for complete response
- **Early interruption**: Users can stop generation early

## Basic Streaming

### Synchronous

```python
from langchain_maritaca import ChatMaritaca

model = ChatMaritaca()

for chunk in model.stream("Tell me a story about Brazil."):
    print(chunk.content, end="", flush=True)
```

### Asynchronous

```python
import asyncio
from langchain_maritaca import ChatMaritaca

async def main():
    model = ChatMaritaca()
    async for chunk in model.astream("Tell me a story."):
        print(chunk.content, end="", flush=True)

asyncio.run(main())
```

## Streaming with Messages

```python
from langchain_maritaca import ChatMaritaca
from langchain_core.messages import HumanMessage, SystemMessage

model = ChatMaritaca()

messages = [
    SystemMessage(content="You are a storyteller."),
    HumanMessage(content="Tell a short story."),
]

for chunk in model.stream(messages):
    print(chunk.content, end="", flush=True)
```

## Capturing Complete Response

```python
from langchain_maritaca import ChatMaritaca

model = ChatMaritaca()

complete_response = ""
for chunk in model.stream("Tell a story."):
    complete_response += chunk.content
    print(chunk.content, end="", flush=True)

print(f"\n\nComplete: {complete_response}")
```

## Streaming with FastAPI

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_maritaca import ChatMaritaca

app = FastAPI()
model = ChatMaritaca()

@app.get("/stream")
async def stream_response(question: str):
    async def generate():
        async for chunk in model.astream(question):
            if chunk.content:
                yield chunk.content

    return StreamingResponse(
        generate(),
        media_type="text/plain"
    )
```

## Streaming with WebSocket

```python
from fastapi import FastAPI, WebSocket
from langchain_maritaca import ChatMaritaca

app = FastAPI()
model = ChatMaritaca()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    while True:
        message = await websocket.receive_text()

        async for chunk in model.astream(message):
            if chunk.content:
                await websocket.send_text(chunk.content)

        await websocket.send_text("[END]")
```

## Streaming with Gradio

```python
import gradio as gr
from langchain_maritaca import ChatMaritaca

model = ChatMaritaca()

def respond(message, history):
    response = ""
    for chunk in model.stream(message):
        response += chunk.content
        yield response

demo = gr.ChatInterface(respond)
demo.launch()
```

## Streaming Events

For detailed events:

```python
from langchain_maritaca import ChatMaritaca

model = ChatMaritaca()

async for event in model.astream_events("Hello!", version="v2"):
    if event["event"] == "on_chat_model_stream":
        chunk = event["data"]["chunk"]
        print(chunk.content, end="")
```

## Streaming in LCEL Chains

```python
from langchain_maritaca import ChatMaritaca
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

model = ChatMaritaca()
prompt = ChatPromptTemplate.from_template("Tell about: {topic}")
parser = StrOutputParser()

chain = prompt | model | parser

for chunk in chain.stream({"topic": "Brazil"}):
    print(chunk, end="", flush=True)
```

## Tips

### 1. Use flush=True

```python
# Ensures immediate printing
print(chunk.content, end="", flush=True)
```

### 2. Handle Chunk Metadata

```python
for chunk in model.stream("Hello"):
    if chunk.content:  # Some chunks may be empty
        print(chunk.content, end="")

    # Final chunk has metadata
    if chunk.response_metadata:
        print(f"\nModel: {chunk.response_metadata.get('model')}")
```

### 3. Async Generators

```python
async def stream_response(question: str):
    async for chunk in model.astream(question):
        yield chunk.content
```

## Next Steps

- [Async](async.md) - Complete async support
- [LCEL](lcel.md) - Chains with streaming
