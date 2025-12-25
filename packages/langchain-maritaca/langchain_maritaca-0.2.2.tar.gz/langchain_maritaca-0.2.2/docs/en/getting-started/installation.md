# Installation

## Requirements

- Python 3.9 or higher
- Maritaca AI API key

## Installation via pip

```bash
pip install langchain-maritaca
```

## Installation via uv (recommended)

```bash
uv add langchain-maritaca
```

## Installation via poetry

```bash
poetry add langchain-maritaca
```

## Installation from source

```bash
git clone https://github.com/anderson-ufrj/langchain-maritaca.git
cd langchain-maritaca
pip install -e .
```

## API Key

### Option 1: Environment Variable (recommended)

```bash
export MARITACA_API_KEY="your-api-key"
```

### Option 2: .env File

Create a `.env` file:

```env
MARITACA_API_KEY=your-api-key
```

And load with python-dotenv:

```python
from dotenv import load_dotenv
load_dotenv()
```

### Option 3: Direct in Code

```python
from langchain_maritaca import ChatMaritaca

model = ChatMaritaca(api_key="your-api-key")
```

!!! warning "Security"
    Never commit API keys to version control. Use environment variables or secret managers.

## Verifying Installation

```python
from langchain_maritaca import ChatMaritaca

model = ChatMaritaca()
response = model.invoke("Say hello!")
print(response.content)
```

## Optional Dependencies

For specific examples, you may need:

```bash
# RAG with FAISS
pip install langchain langchain-community faiss-cpu

# HuggingFace Embeddings
pip install sentence-transformers

# Web interface with Gradio
pip install gradio

# API with FastAPI
pip install fastapi uvicorn
```

## Next Steps

- [Quick Start](quickstart.md) - Your first example
- [Configuration](configuration.md) - Advanced options
