# Tool Calling

Function calling allows models to request tool execution for complex tasks.

## What is Tool Calling?

Tool Calling (or Function Calling) allows the model to:

1. Recognize when a tool is needed
2. Generate structured arguments
3. Request tool execution
4. Use results to compose the response

## Defining Tools

### With Pydantic (Recommended)

```python
from pydantic import BaseModel, Field

class GetWeather(BaseModel):
    """Gets the weather for a city."""
    city: str = Field(description="City name")
    unit: str = Field(default="celsius", description="Temperature unit")
```

### With @tool Decorator

```python
from langchain_core.tools import tool

@tool
def calculate(expression: str) -> str:
    """Evaluates a mathematical expression."""
    return str(eval(expression))
```

### With Dictionary

```python
tool_schema = {
    "type": "function",
    "function": {
        "name": "search_products",
        "description": "Searches for products in the database",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search term"},
                "category": {"type": "string", "description": "Category"},
            },
            "required": ["query"]
        }
    }
}
```

## Binding Tools

```python
from langchain_maritaca import ChatMaritaca

model = ChatMaritaca()
model_with_tools = model.bind_tools([GetWeather, calculate])
```

## Complete Usage Example

```python
from langchain_maritaca import ChatMaritaca
from langchain_core.messages import HumanMessage, ToolMessage
from pydantic import BaseModel, Field

# 1. Define tools
class GetWeather(BaseModel):
    """Gets the current weather."""
    city: str = Field(description="City name")

class Calculate(BaseModel):
    """Performs calculations."""
    expression: str = Field(description="Mathematical expression")

# 2. Tool implementations
def get_weather(city: str) -> str:
    # In production, call a real API
    return f"Weather in {city}: 25C, sunny"

def calculate(expression: str) -> str:
    return str(eval(expression))

# Map tools to implementations
tools_map = {
    "GetWeather": get_weather,
    "Calculate": calculate,
}

# 3. Setup model
model = ChatMaritaca()
model_with_tools = model.bind_tools([GetWeather, Calculate])

# 4. Agent loop
def run_agent(question: str) -> str:
    messages = [HumanMessage(content=question)]

    while True:
        response = model_with_tools.invoke(messages)
        messages.append(response)

        # No tool calls = final answer
        if not response.tool_calls:
            return response.content

        # Execute each tool call
        for tool_call in response.tool_calls:
            func = tools_map[tool_call["name"]]
            result = func(**tool_call["args"])

            messages.append(ToolMessage(
                content=result,
                tool_call_id=tool_call["id"]
            ))

# 5. Use
print(run_agent("What's the weather in Sao Paulo?"))
print(run_agent("How much is 15% of 250?"))
```

## Tool Choice

Control how the model selects tools:

### auto (default)

Model decides whether to use tools.

```python
model.bind_tools(tools, tool_choice="auto")
```

### required

Forces the model to use at least one tool.

```python
model.bind_tools(tools, tool_choice="required")
```

### Specific Tool

Forces use of a specific tool.

```python
model.bind_tools(tools, tool_choice={
    "type": "function",
    "function": {"name": "GetWeather"}
})
```

## Tool Call Structure

When the model calls a tool:

```python
response.tool_calls = [
    {
        "name": "GetWeather",
        "args": {"city": "Sao Paulo"},
        "id": "call_abc123"
    }
]
```

## ToolMessage

To return tool results:

```python
from langchain_core.messages import ToolMessage

tool_message = ToolMessage(
    content="25C, sunny",
    tool_call_id="call_abc123"  # Must match tool_call id
)
```

## Multiple Tools in One Call

The model can request multiple tools at once:

```python
# Question that requires multiple tools
response = model_with_tools.invoke(
    "What's the weather in SP and Rio, and calculate 10% of 500?"
)

# response.tool_calls may contain multiple calls
for tool_call in response.tool_calls:
    print(f"Tool: {tool_call['name']}")
    print(f"Args: {tool_call['args']}")
```

## Async Tool Calling

```python
import asyncio
from langchain_maritaca import ChatMaritaca

async def run_agent_async(question: str) -> str:
    messages = [HumanMessage(content=question)]

    while True:
        response = await model_with_tools.ainvoke(messages)
        messages.append(response)

        if not response.tool_calls:
            return response.content

        for tool_call in response.tool_calls:
            result = await execute_tool_async(tool_call)
            messages.append(ToolMessage(
                content=result,
                tool_call_id=tool_call["id"]
            ))
```

## Error Handling

```python
def execute_tool_safely(tool_call):
    try:
        func = tools_map.get(tool_call["name"])
        if not func:
            return f"Unknown tool: {tool_call['name']}"
        return func(**tool_call["args"])
    except Exception as e:
        return f"Error executing {tool_call['name']}: {str(e)}"
```

## Best Practices

### 1. Clear Descriptions

```python
class SearchProducts(BaseModel):
    """Searches for products in the e-commerce catalog.

    Use to find products by name, category or characteristics.
    Returns list of products with name, price and availability.
    """
    query: str = Field(description="Search term (name, category, brand)")
    max_results: int = Field(default=5, description="Maximum results (1-20)")
```

### 2. Input Validation

```python
from pydantic import validator

class GetWeather(BaseModel):
    city: str = Field(description="City name")

    @validator("city")
    def validate_city(cls, v):
        if len(v) < 2:
            raise ValueError("City name too short")
        return v.strip().title()
```

### 3. Iteration Limit

```python
def run_agent(question: str, max_iterations: int = 10) -> str:
    for _ in range(max_iterations):
        # agent logic...
        pass
    return "Maximum iterations reached"
```

## Next Steps

- [Agent Example](../examples/agent.md) - Complete agent
- [LCEL](lcel.md) - Chains with tools
