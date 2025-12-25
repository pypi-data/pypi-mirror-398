# langchain-maritaca

Official LangChain integration for Maritaca AI models - **the best LLM for Brazilian Portuguese**.

<div class="grid cards" markdown>

- :material-rocket-launch: **Quick Start**

    ---

    Get started in minutes with simple installation and configuration.

    [:octicons-arrow-right-24: Getting Started](getting-started/quickstart.md)

- :material-tools: **Tool Calling**

    ---

    Function calling support for building intelligent agents.

    [:octicons-arrow-right-24: Tool Calling Guide](guide/tool-calling.md)

- :material-lightning-bolt: **Streaming**

    ---

    Real-time token streaming for better user experience.

    [:octicons-arrow-right-24: Streaming Guide](guide/streaming.md)

- :material-code-braces: **API Reference**

    ---

    Complete documentation of all classes and methods.

    [:octicons-arrow-right-24: API Reference](api/chat-maritaca.md)

</div>

## What is langchain-maritaca?

`langchain-maritaca` is the **official integration** between [LangChain](https://langchain.com/) and [Maritaca AI](https://maritaca.ai/), the Brazilian artificial intelligence company that develops the **Sabia** model family - LLMs optimized for Brazilian Portuguese.

## Key Features

- **Native Brazilian Portuguese**: Sabia models deeply understand Brazilian Portuguese
- **Full LangChain Compatibility**: Works with all LangChain abstractions
- **Tool Calling**: Function calling support for intelligent agents
- **Streaming**: Real-time token streaming (sync and async)
- **Async Support**: Full support for async/await
- **Automatic Retry**: Retry with exponential backoff
- **Observability**: Native LangSmith integration

## Quick Installation

```bash
pip install langchain-maritaca
```

## Minimal Example

```python
from langchain_maritaca import ChatMaritaca

model = ChatMaritaca()
response = model.invoke("Hello! How are you?")
print(response.content)
```

## Available Models

| Model | Description | Use Case |
|-------|-------------|----------|
| `sabia-3.1` | Most powerful model | Complex tasks, analysis |
| `sabiazinho-3.1` | Faster, more economical | Simple tasks, chatbots |

## Production Use Cases

<div class="grid cards" markdown>

- :material-shield-check: **Cidadao.AI**

    ---

    Multi-agent transparency platform for fighting corruption in Brazil. Uses Maritaca AI as the primary LLM.

    [:octicons-arrow-right-24: cidadao.ai](https://github.com/anderson-ufrj/cidadao.ai-backend)

</div>

## Next Steps

<div class="grid cards" markdown>

- [:octicons-download-24: Installation](getting-started/installation.md)
- [:octicons-rocket-24: Quick Start](getting-started/quickstart.md)
- [:octicons-gear-24: Configuration](getting-started/configuration.md)
- [:octicons-book-24: Basic Usage](guide/basic-usage.md)

</div>
