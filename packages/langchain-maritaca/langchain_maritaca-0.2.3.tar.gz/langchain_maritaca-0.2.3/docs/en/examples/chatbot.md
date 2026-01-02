# Simple Chatbot

A complete example of a chatbot with conversation memory.

## Complete Code

```python
from langchain_maritaca import ChatMaritaca
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


class ChatBot:
    """Simple chatbot with conversation memory."""

    def __init__(
        self,
        system_prompt: str = "You are a helpful assistant.",
        model: str = "sabia-3.1",
        max_history: int = 10,
    ):
        self.model = ChatMaritaca(model=model, temperature=0.7)
        self.system_prompt = system_prompt
        self.history: list = []
        self.max_history = max_history

    def _build_messages(self, input: str) -> list:
        """Builds message list for the model."""
        messages = [SystemMessage(content=self.system_prompt)]
        messages.extend(self.history)
        messages.append(HumanMessage(content=input))
        return messages

    def _update_history(self, input: str, response: str):
        """Updates history keeping the limit."""
        self.history.append(HumanMessage(content=input))
        self.history.append(AIMessage(content=response))

        # Keep only the last N messages
        if len(self.history) > self.max_history * 2:
            self.history = self.history[-(self.max_history * 2):]

    def chat(self, input: str) -> str:
        """Sends message and returns response."""
        messages = self._build_messages(input)
        response = self.model.invoke(messages)
        self._update_history(input, response.content)
        return response.content

    def chat_stream(self, input: str):
        """Sends message and returns streaming response."""
        messages = self._build_messages(input)

        complete_response = ""
        for chunk in self.model.stream(messages):
            if chunk.content:
                complete_response += chunk.content
                yield chunk.content

        self._update_history(input, complete_response)

    def clear_history(self):
        """Clears conversation history."""
        self.history = []


# Usage example
if __name__ == "__main__":
    bot = ChatBot(
        system_prompt="You are Sabia, a friendly and helpful Brazilian assistant."
    )

    print("ChatBot started! Type 'exit' to quit.\n")

    while True:
        input_text = input("You: ").strip()

        if input_text.lower() == "exit":
            print("Goodbye!")
            break

        if input_text.lower() == "clear":
            bot.clear_history()
            print("History cleared!\n")
            continue

        if not input_text:
            continue

        print("Sabia: ", end="", flush=True)
        for chunk in bot.chat_stream(input_text):
            print(chunk, end="", flush=True)
        print("\n")
```

## FastAPI Version

```python
from fastapi import FastAPI, WebSocket
from langchain_maritaca import ChatMaritaca
from pydantic import BaseModel

app = FastAPI()
model = ChatMaritaca()

# State per session (in production, use Redis/DB)
sessions: dict[str, list] = {}


class MessageRequest(BaseModel):
    session_id: str
    message: str


class MessageResponse(BaseModel):
    response: str


@app.post("/chat", response_model=MessageResponse)
async def chat(request: MessageRequest):
    # Get or create session history
    if request.session_id not in sessions:
        sessions[request.session_id] = []

    history = sessions[request.session_id]

    # Build messages
    messages = [
        ("system", "You are a helpful assistant."),
        *history,
        ("human", request.message),
    ]

    # Get response
    response = await model.ainvoke(messages)

    # Update history
    history.append(("human", request.message))
    history.append(("assistant", response.content))

    # Limit history
    if len(history) > 20:
        sessions[request.session_id] = history[-20:]

    return MessageResponse(response=response.content)


@app.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    await websocket.accept()

    if session_id not in sessions:
        sessions[session_id] = []

    while True:
        message = await websocket.receive_text()
        history = sessions[session_id]

        messages = [
            ("system", "You are a helpful assistant."),
            *history,
            ("human", message),
        ]

        # Streaming via WebSocket
        complete_response = ""
        async for chunk in model.astream(messages):
            if chunk.content:
                complete_response += chunk.content
                await websocket.send_text(chunk.content)

        # Mark end of streaming
        await websocket.send_text("[END]")

        # Update history
        history.append(("human", message))
        history.append(("assistant", complete_response))
```

## Gradio Version

```python
import gradio as gr
from langchain_maritaca import ChatMaritaca

model = ChatMaritaca()


def respond(message, history):
    # Convert Gradio history to LangChain format
    messages = [("system", "You are a helpful assistant.")]

    for h in history:
        messages.append(("human", h[0]))
        if h[1]:
            messages.append(("assistant", h[1]))

    messages.append(("human", message))

    # Streaming
    response = ""
    for chunk in model.stream(messages):
        if chunk.content:
            response += chunk.content
            yield response


demo = gr.ChatInterface(
    respond,
    title="Maritaca ChatBot",
    description="Chat with the Sabia-3.1 model from Maritaca AI",
    theme="soft",
)

if __name__ == "__main__":
    demo.launch()
```

## Next Steps

- [RAG Pipeline](rag.md) - Add external knowledge
- [Agent with Tools](agent.md) - Add action capabilities
