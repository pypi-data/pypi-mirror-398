# Async Support

Complete async/await support for high-performance applications.

## Why Async?

- **Concurrency**: Process multiple requests simultaneously
- **Non-blocking I/O**: Doesn't block while waiting for API
- **Web frameworks**: Better integration with FastAPI, Starlette, etc.

## Available Methods

| Synchronous | Asynchronous |
|-------------|--------------|
| `invoke()` | `ainvoke()` |
| `stream()` | `astream()` |
| `batch()` | `abatch()` |

## Basic Usage

### ainvoke()

```python
import asyncio
from langchain_maritaca import ChatMaritaca

async def main():
    model = ChatMaritaca()
    response = await model.ainvoke("Hello!")
    print(response.content)

asyncio.run(main())
```

### astream()

```python
import asyncio
from langchain_maritaca import ChatMaritaca

async def main():
    model = ChatMaritaca()
    async for chunk in model.astream("Tell a story."):
        print(chunk.content, end="", flush=True)

asyncio.run(main())
```

### abatch()

```python
import asyncio
from langchain_maritaca import ChatMaritaca

async def main():
    model = ChatMaritaca()

    questions = [
        [("human", "What is 2+2?")],
        [("human", "What is the capital of Brazil?")],
    ]

    responses = await model.abatch(questions)
    for r in responses:
        print(r.content)

asyncio.run(main())
```

## Concurrent Requests

```python
import asyncio
from langchain_maritaca import ChatMaritaca

async def ask(model, question):
    response = await model.ainvoke(question)
    return response.content

async def main():
    model = ChatMaritaca()

    questions = [
        "What is AI?",
        "What is machine learning?",
        "What is deep learning?",
    ]

    # Execute all concurrently
    results = await asyncio.gather(*[
        ask(model, q) for q in questions
    ])

    for q, r in zip(questions, results):
        print(f"Q: {q}")
        print(f"A: {r[:100]}...\n")

asyncio.run(main())
```

## Integration with FastAPI

```python
from fastapi import FastAPI
from langchain_maritaca import ChatMaritaca
from pydantic import BaseModel

app = FastAPI()
model = ChatMaritaca()

class Question(BaseModel):
    text: str

@app.post("/ask")
async def ask_model(question: Question):
    response = await model.ainvoke(question.text)
    return {"answer": response.content}
```

## Integration with Starlette

```python
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from langchain_maritaca import ChatMaritaca

model = ChatMaritaca()

async def ask(request):
    data = await request.json()
    response = await model.ainvoke(data["question"])
    return JSONResponse({"answer": response.content})

app = Starlette(routes=[
    Route("/ask", ask, methods=["POST"]),
])
```

## Async Streaming in Web Apps

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_maritaca import ChatMaritaca

app = FastAPI()
model = ChatMaritaca()

@app.get("/stream")
async def stream(question: str):
    async def generate():
        async for chunk in model.astream(question):
            if chunk.content:
                yield chunk.content

    return StreamingResponse(generate(), media_type="text/plain")
```

## Error Handling

```python
import asyncio
import httpx
from langchain_maritaca import ChatMaritaca

async def safe_invoke(model, message):
    try:
        response = await model.ainvoke(message)
        return response.content
    except httpx.HTTPStatusError as e:
        return f"HTTP error: {e.response.status_code}"
    except httpx.TimeoutException:
        return "Timeout"
    except Exception as e:
        return f"Error: {str(e)}"

async def main():
    model = ChatMaritaca()
    result = await safe_invoke(model, "Hello!")
    print(result)

asyncio.run(main())
```

## Semaphore for Rate Limiting

```python
import asyncio
from langchain_maritaca import ChatMaritaca

async def main():
    model = ChatMaritaca()
    semaphore = asyncio.Semaphore(5)  # Max 5 concurrent

    async def limited_request(question):
        async with semaphore:
            return await model.ainvoke(question)

    questions = [f"Question {i}" for i in range(20)]
    results = await asyncio.gather(*[
        limited_request(q) for q in questions
    ])

asyncio.run(main())
```

## Async Context Manager

```python
import asyncio
from langchain_maritaca import ChatMaritaca

class AsyncChatSession:
    def __init__(self):
        self.model = ChatMaritaca()
        self.history = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        self.history.clear()

    async def chat(self, message):
        self.history.append(("human", message))
        response = await self.model.ainvoke(self.history)
        self.history.append(("assistant", response.content))
        return response.content

async def main():
    async with AsyncChatSession() as session:
        print(await session.chat("Hello!"))
        print(await session.chat("How are you?"))

asyncio.run(main())
```

## Tips

### 1. Prefer async in Web Apps

```python
# FastAPI, Starlette, aiohttp prefer async
@app.post("/chat")
async def chat(request):
    response = await model.ainvoke(request.message)
    return response
```

### 2. Use gather for Concurrency

```python
# Process multiple requests at once
results = await asyncio.gather(*tasks)
```

### 3. Limit Concurrency

```python
# Avoid overwhelming the API
semaphore = asyncio.Semaphore(10)
```

## Next Steps

- [LCEL](lcel.md) - Chains with async
- [Tool Calling](tool-calling.md) - Async agents
