# LCEL Integration

LangChain Expression Language (LCEL) for composable chains.

## What is LCEL?

LCEL is a declarative way to compose LangChain components using the `|` operator. Benefits:

- **Streaming**: Native streaming in all chains
- **Async**: Automatic async support
- **Batch**: Parallel processing
- **Retry**: Built-in error handling

## Basic Chain

```python
from langchain_maritaca import ChatMaritaca
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

model = ChatMaritaca()
prompt = ChatPromptTemplate.from_template("Tell me about: {topic}")
parser = StrOutputParser()

chain = prompt | model | parser

result = chain.invoke({"topic": "Brazilian AI"})
print(result)
```

## Chain Components

### PromptTemplate

```python
from langchain_core.prompts import ChatPromptTemplate

# Simple
prompt = ChatPromptTemplate.from_template("Translate to English: {text}")

# With messages
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("human", "{question}")
])
```

### Output Parsers

```python
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser

# String
parser = StrOutputParser()

# JSON
parser = JsonOutputParser()
```

### RunnablePassthrough

```python
from langchain_core.runnables import RunnablePassthrough

# Passes input unchanged
chain = {"text": RunnablePassthrough()} | prompt | model
```

### RunnableLambda

```python
from langchain_core.runnables import RunnableLambda

def process(text: str) -> str:
    return text.upper()

chain = prompt | model | StrOutputParser() | RunnableLambda(process)
```

## Practical Examples

### Translator

```python
from langchain_maritaca import ChatMaritaca
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

model = ChatMaritaca()

translator = (
    ChatPromptTemplate.from_template(
        "Translate the following text to {language}:\n\n{text}"
    )
    | model
    | StrOutputParser()
)

result = translator.invoke({
    "language": "English",
    "text": "Ola, como vai voce?"
})
print(result)
```

### Summarizer

```python
summarizer = (
    ChatPromptTemplate.from_template(
        "Summarize the following text in {num_sentences} sentences:\n\n{text}"
    )
    | model
    | StrOutputParser()
)

result = summarizer.invoke({
    "num_sentences": 3,
    "text": "Long text..."
})
```

### Chain with Context

```python
from langchain_core.runnables import RunnablePassthrough

qa_chain = (
    {
        "context": lambda x: search_context(x["question"]),
        "question": RunnablePassthrough()
    }
    | ChatPromptTemplate.from_template(
        "Based on the context below, answer:\n\nContext: {context}\n\nQuestion: {question}"
    )
    | model
    | StrOutputParser()
)
```

## Streaming with LCEL

```python
from langchain_maritaca import ChatMaritaca
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

chain = (
    ChatPromptTemplate.from_template("Tell about: {topic}")
    | ChatMaritaca()
    | StrOutputParser()
)

for chunk in chain.stream({"topic": "AI"}):
    print(chunk, end="", flush=True)
```

## Async with LCEL

```python
import asyncio

async def main():
    result = await chain.ainvoke({"topic": "AI"})
    print(result)

    async for chunk in chain.astream({"topic": "AI"}):
        print(chunk, end="")

asyncio.run(main())
```

## Batch with LCEL

```python
results = chain.batch([
    {"topic": "AI"},
    {"topic": "machine learning"},
    {"topic": "deep learning"},
])

for r in results:
    print(r[:100])
```

## Parallel Composition

```python
from langchain_core.runnables import RunnableParallel

parallel_chain = RunnableParallel({
    "summary": summarize_chain,
    "translation": translate_chain,
    "keywords": keywords_chain,
})

result = parallel_chain.invoke({"text": "..."})
print(result["summary"])
print(result["translation"])
print(result["keywords"])
```

## Sequential Composition

```python
full_chain = (
    first_step
    | second_step
    | third_step
)
```

## Branching

```python
from langchain_core.runnables import RunnableBranch

classifier_chain = RunnableBranch(
    (lambda x: "weather" in x["question"].lower(), weather_chain),
    (lambda x: "calculate" in x["question"].lower(), math_chain),
    default_chain  # default
)
```

## Error Handling

```python
from langchain_core.runnables import RunnableConfig

chain_with_retry = chain.with_retry(
    stop_after_attempt=3,
    wait_exponential_jitter=True
)

chain_with_fallback = chain.with_fallbacks([
    fallback_chain
])
```

## Integration with Tools

```python
from langchain_maritaca import ChatMaritaca
from langchain_core.prompts import ChatPromptTemplate

model_with_tools = ChatMaritaca().bind_tools([MyTool])

chain = (
    ChatPromptTemplate.from_messages([
        ("system", "You are an assistant with tools."),
        ("human", "{question}")
    ])
    | model_with_tools
)
```

## Tips

### 1. Name Your Chains

```python
chain = (prompt | model | parser).with_config({"run_name": "TranslatorChain"})
```

### 2. Add Logging

```python
from langchain.callbacks import StdOutCallbackHandler

result = chain.invoke(
    {"topic": "AI"},
    config={"callbacks": [StdOutCallbackHandler()]}
)
```

### 3. Validate Inputs

```python
from pydantic import BaseModel

class ChainInput(BaseModel):
    topic: str

validated_chain = chain.with_types(input_type=ChainInput)
```

## Next Steps

- [RAG Example](../examples/rag.md) - Complete RAG chain
- [Agent Example](../examples/agent.md) - LCEL with agents
