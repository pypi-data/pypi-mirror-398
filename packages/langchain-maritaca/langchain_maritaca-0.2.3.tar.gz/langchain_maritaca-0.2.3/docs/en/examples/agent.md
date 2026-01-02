# Agent with Tools

Example of an agent that can use tools to perform real-world actions.

!!! note "Dependencies"
    This example requires additional dependencies:
    ```bash
    pip install langchain langgraph
    ```

## Basic Agent with Tools

```python
from langchain_maritaca import ChatMaritaca
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage

# 1. Define tools
@tool
def calculate(expression: str) -> str:
    """Calculates a mathematical expression."""
    try:
        result = eval(expression)
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {e}"

@tool
def get_current_time() -> str:
    """Returns the current time."""
    from datetime import datetime
    return datetime.now().strftime("%H:%M:%S")

@tool
def search_zipcode(zipcode: str) -> str:
    """Searches information for a Brazilian ZIP code."""
    import httpx
    response = httpx.get(f"https://viacep.com.br/ws/{zipcode}/json/")
    if response.status_code == 200:
        data = response.json()
        return f"{data.get('logradouro', '')}, {data.get('bairro', '')}, {data.get('localidade', '')}-{data.get('uf', '')}"
    return "ZIP code not found"

# 2. Create model with tools
model = ChatMaritaca()
tools = [calculate, get_current_time, search_zipcode]
model_with_tools = model.bind_tools(tools)

# 3. Agent execution loop
def run_agent(question: str, max_iterations: int = 5) -> str:
    """Runs the agent until final response."""
    messages = [HumanMessage(content=question)]

    for _ in range(max_iterations):
        response = model_with_tools.invoke(messages)
        messages.append(response)

        # If no tool calls, return the response
        if not response.tool_calls:
            return response.content

        # Execute each tool call
        for tool_call in response.tool_calls:
            # Find the tool
            tool_func = next(
                (t for t in tools if t.name == tool_call["name"]),
                None
            )

            if tool_func:
                result = tool_func.invoke(tool_call["args"])
                messages.append(ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call["id"]
                ))

    return "Maximum iterations reached"

# 4. Use the agent
print(run_agent("How much is 15% of 250?"))
print(run_agent("What time is it?"))
print(run_agent("What's the address for ZIP code 01310-100?"))
```

## Agent with LangGraph

```python
from typing import Annotated, TypedDict
from langchain_maritaca import ChatMaritaca
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

# Define state
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# Tools
@tool
def web_search(query: str) -> str:
    """Searches for information on the web."""
    # Simulates search
    return f"Results for '{query}': relevant information found."

@tool
def send_email(recipient: str, subject: str, body: str) -> str:
    """Sends an email."""
    # Simulates sending
    return f"Email sent to {recipient} with subject '{subject}'"

tools = [web_search, send_email]
tools_dict = {t.name: t for t in tools}

# Model
model = ChatMaritaca().bind_tools(tools)

# Graph nodes
def call_model(state: AgentState) -> dict:
    """Calls the model."""
    response = model.invoke(state["messages"])
    return {"messages": [response]}

def execute_tools(state: AgentState) -> dict:
    """Executes the called tools."""
    last_message = state["messages"][-1]
    results = []

    for tool_call in last_message.tool_calls:
        tool_func = tools_dict[tool_call["name"]]
        result = tool_func.invoke(tool_call["args"])
        results.append(ToolMessage(
            content=str(result),
            tool_call_id=tool_call["id"]
        ))

    return {"messages": results}

def should_continue(state: AgentState) -> str:
    """Decides whether to continue or end."""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END

# Build graph
graph = StateGraph(AgentState)
graph.add_node("model", call_model)
graph.add_node("tools", execute_tools)

graph.set_entry_point("model")
graph.add_conditional_edges("model", should_continue, {
    "tools": "tools",
    END: END
})
graph.add_edge("tools", "model")

# Compile
agent = graph.compile()

# Use
result = agent.invoke({
    "messages": [HumanMessage(content="Search for Maritaca AI")]
})
print(result["messages"][-1].content)
```

## Manual ReAct Agent

```python
from langchain_maritaca import ChatMaritaca
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool

@tool
def wikipedia(query: str) -> str:
    """Searches for information on Wikipedia."""
    # Simplified for example
    return f"Wikipedia information about {query}: relevant content."

@tool
def calculator(expression: str) -> str:
    """Performs mathematical calculations."""
    return str(eval(expression))

tools = [wikipedia, calculator]
model = ChatMaritaca().bind_tools(tools)

SYSTEM_PROMPT = """You are an assistant that can use tools to answer questions.

Follow this process:
1. Think about the question
2. If you need external information, use the tools
3. Analyze the results
4. Provide a complete answer

Be concise and precise."""

def react_agent(question: str) -> str:
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=question)
    ]

    while True:
        response = model.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            return response.content

        for tool_call in response.tool_calls:
            tool_func = next(t for t in tools if t.name == tool_call["name"])
            result = tool_func.invoke(tool_call["args"])
            messages.append(ToolMessage(
                content=result,
                tool_call_id=tool_call["id"]
            ))

# Use
response = react_agent("Who was Santos Dumont and what year was he born?")
print(response)
```

## Agent with Memory

```python
from langchain_maritaca import ChatMaritaca
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool

@tool
def remember(information: str) -> str:
    """Saves important information."""
    return f"Information saved: {information}"

@tool
def query_memory(topic: str) -> str:
    """Queries saved information about a topic."""
    # In production, use a real database
    return f"Memory about {topic}: no information found."

tools = [remember, query_memory]
model = ChatMaritaca().bind_tools(tools)

class AgentWithMemory:
    def __init__(self):
        self.history = []
        self.memory = {}

    def process(self, input: str) -> str:
        messages = [
            SystemMessage(content="You are an assistant with persistent memory."),
            *self.history,
            HumanMessage(content=input)
        ]

        while True:
            response = model.invoke(messages)

            if not response.tool_calls:
                self.history.append(HumanMessage(content=input))
                self.history.append(response)
                return response.content

            messages.append(response)

            for tool_call in response.tool_calls:
                if tool_call["name"] == "remember":
                    info = tool_call["args"]["information"]
                    self.memory[info[:20]] = info
                    result = "Information saved successfully."
                elif tool_call["name"] == "query_memory":
                    topic = tool_call["args"]["topic"]
                    result = str(self.memory) if self.memory else "Memory empty."

                messages.append(ToolMessage(
                    content=result,
                    tool_call_id=tool_call["id"]
                ))

# Use
agent = AgentWithMemory()
print(agent.process("Remember that my name is John"))
print(agent.process("What is my name?"))
```

## Best Practices

### 1. Error Handling

```python
def execute_tool_safely(tool_func, args):
    """Executes tool with error handling."""
    try:
        return tool_func.invoke(args)
    except Exception as e:
        return f"Error executing {tool_func.name}: {str(e)}"
```

### 2. Tool Timeout

```python
import asyncio

async def execute_with_timeout(tool_func, args, timeout=30):
    """Executes tool with timeout."""
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(tool_func.invoke, args),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        return f"Timeout executing {tool_func.name}"
```

### 3. Action Logging

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def execute_with_logging(tool_func, args, tool_call_id):
    """Executes tool with logging."""
    logger.info(f"Executing {tool_func.name} with args: {args}")
    result = tool_func.invoke(args)
    logger.info(f"Result from {tool_func.name}: {result[:100]}...")
    return result
```

## Next Steps

- [Tool Calling](../guide/tool-calling.md) - Details on function calling
- [RAG Pipeline](rag.md) - Combine agents with document search
