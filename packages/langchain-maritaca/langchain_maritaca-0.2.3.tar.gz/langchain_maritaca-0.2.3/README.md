# langchain-maritaca

[![PyPI version](https://img.shields.io/pypi/v/langchain-maritaca.svg)](https://pypi.org/project/langchain-maritaca/)
[![Python](https://img.shields.io/pypi/pyversions/langchain-maritaca.svg)](https://pypi.org/project/langchain-maritaca/)
[![Downloads](https://img.shields.io/pypi/dm/langchain-maritaca.svg)](https://pypi.org/project/langchain-maritaca/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/anderson-ufrj/langchain-maritaca/actions/workflows/ci.yml/badge.svg)](https://github.com/anderson-ufrj/langchain-maritaca/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/anderson-ufrj/langchain-maritaca/graph/badge.svg)](https://codecov.io/gh/anderson-ufrj/langchain-maritaca)

[🇧🇷 Leia em Português](README.pt-br.md)

An integration package connecting [Maritaca AI](https://www.maritaca.ai/) and [LangChain](https://langchain.com/) for Brazilian Portuguese language models.

**Author:** Anderson Henrique da Silva
**Location:** Minas Gerais, Brasil
**GitHub:** [anderson-ufrj](https://github.com/anderson-ufrj)

## Overview

Maritaca AI provides state-of-the-art Brazilian Portuguese language models, including the Sabiá family of models. This integration allows you to use Maritaca's models seamlessly within the LangChain ecosystem.

### Available Models

| Model | Description | Pricing (per 1M tokens) |
|-------|-------------|------------------------|
| `sabia-3.1.1` | Most capable model, best for complex tasks | Check [Maritaca AI](https://www.maritaca.ai/) for pricing |
| `sabiazinho-3.1` | Fast and economical, great for simple tasks | Check [Maritaca AI](https://www.maritaca.ai/) for pricing |

## Installation

```bash
pip install langchain-maritaca
```

## Setup

Set your Maritaca API key as an environment variable:

```bash
export MARITACA_API_KEY="your-api-key"
```

Or pass it directly to the model:

```python
from langchain_maritaca import ChatMaritaca

model = ChatMaritaca(api_key="your-api-key")
```

## Usage

### Basic Usage

```python
from langchain_maritaca import ChatMaritaca

model = ChatMaritaca(
    model="sabia-3.1",
    temperature=0.7,
)

messages = [
    ("system", "Você é um assistente prestativo especializado em cultura brasileira."),
    ("human", "Quais são as principais festas populares do Brasil?"),
]

response = model.invoke(messages)
print(response.content)
```

### Streaming

```python
from langchain_maritaca import ChatMaritaca

model = ChatMaritaca(model="sabia-3.1", streaming=True)

for chunk in model.stream("Conte uma história sobre o folclore brasileiro"):
    print(chunk.content, end="", flush=True)
```

### Async Usage

```python
import asyncio
from langchain_maritaca import ChatMaritaca

async def main():
    model = ChatMaritaca(model="sabia-3.1")
    response = await model.ainvoke("Qual é a receita de pão de queijo?")
    print(response.content)

asyncio.run(main())
```

### With LangChain Expression Language (LCEL)

```python
from langchain_maritaca import ChatMaritaca
from langchain_core.prompts import ChatPromptTemplate

model = ChatMaritaca(model="sabia-3.1")

prompt = ChatPromptTemplate.from_messages([
    ("system", "Você é um especialista em {topic}."),
    ("human", "{question}"),
])

chain = prompt | model

response = chain.invoke({
    "topic": "história do Brasil",
    "question": "Quem foi Tiradentes?"
})
print(response.content)
```

### With Tool Calling (Function Calling)

```python
from langchain_maritaca import ChatMaritaca
from langchain_core.tools import tool

@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    return f"O clima em {city} está ensolarado, 25°C"

model = ChatMaritaca(model="sabia-3.1")
model_with_tools = model.bind_tools([get_weather])

response = model_with_tools.invoke("Como está o tempo em São Paulo?")
print(response)
```

## Why Maritaca AI?

Maritaca AI models are specifically trained for Brazilian Portuguese, offering:

- **Native Portuguese Understanding**: Better comprehension of Brazilian idioms, expressions, and cultural context
- **Local Data Training**: Trained on diverse Brazilian Portuguese data sources
- **Cost-Effective**: Competitive pricing for Portuguese language tasks
- **Low Latency**: Servers located in Brazil for faster response times

## Used in Production

**[Cidadão.AI](https://cidadao-ai-frontend.vercel.app/pt)** - Brazilian government transparency platform powered by AI agents, handling 331K+ requests/month.

- Frontend: [github.com/anderson-ufrj/cidadao.ai-frontend](https://github.com/anderson-ufrj/cidadao.ai-frontend)
- Backend: [github.com/anderson-ufrj/cidadao.ai-backend](https://github.com/anderson-ufrj/cidadao.ai-backend)

> *Using this package in production? [Open an issue](https://github.com/anderson-ufrj/langchain-maritaca/issues) to get featured!*

## API Reference

### ChatMaritaca

Main class for interacting with Maritaca AI models.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | str | `"sabia-3.1"` | Model name to use |
| `temperature` | float | `0.7` | Sampling temperature (0.0-2.0) |
| `max_tokens` | int | None | Maximum tokens to generate |
| `top_p` | float | `0.9` | Top-p sampling parameter |
| `api_key` | str | None | Maritaca API key (or use env var) |
| `base_url` | str | `"https://chat.maritaca.ai/api"` | API base URL |
| `timeout` | float | `60.0` | Request timeout in seconds |
| `max_retries` | int | `2` | Maximum retry attempts |
| `retry_if_rate_limited` | bool | `True` | Auto-retry on rate limit (HTTP 429) |
| `retry_delay` | float | `1.0` | Initial delay between retries (seconds) |
| `retry_max_delay` | float | `60.0` | Maximum delay between retries (seconds) |
| `retry_multiplier` | float | `2.0` | Multiplier for exponential backoff |
| `streaming` | bool | `False` | Enable streaming responses |

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/anderson-ufrj/langchain-maritaca.git
cd langchain-maritaca

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .
ruff format .

# Run type checking
mypy langchain_maritaca
```

### Running Tests

```bash
# Unit tests only
pytest tests/unit_tests/

# Integration tests (requires MARITACA_API_KEY)
pytest tests/integration_tests/

# With coverage
pytest --cov=langchain_maritaca --cov-report=html
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Related Projects

- [LangChain](https://github.com/langchain-ai/langchain) - Building applications with LLMs through composability
- [Maritaca AI](https://www.maritaca.ai/) - Brazilian Portuguese language models
