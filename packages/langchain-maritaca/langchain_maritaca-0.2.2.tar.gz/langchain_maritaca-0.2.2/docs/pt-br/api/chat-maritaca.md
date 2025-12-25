# ChatMaritaca

Classe principal para interação com os modelos de linguagem da Maritaca AI.

## Importação

```python
from langchain_maritaca import ChatMaritaca
```

## Inicialização

```python
modelo = ChatMaritaca(
    model="sabia-3.1",
    temperature=0.7,
    max_tokens=None,
    api_key=None,  # Usa MARITACA_API_KEY do ambiente
)
```

## Parâmetros

### Parâmetros do Modelo

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `model` | `str` | `"sabia-3.1"` | Nome do modelo a usar |
| `temperature` | `float` | `0.7` | Controla aleatoriedade (0.0-2.0) |
| `max_tokens` | `int \| None` | `None` | Máximo de tokens na resposta |
| `top_p` | `float` | `0.9` | Amostragem nucleus |
| `frequency_penalty` | `float` | `0.0` | Penalidade por frequência (-2.0 a 2.0) |
| `presence_penalty` | `float` | `0.0` | Penalidade por presença (-2.0 a 2.0) |
| `stop_sequences` | `list[str] \| None` | `None` | Tokens de parada |
| `n` | `int` | `1` | Número de completions |

### Parâmetros do Cliente

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `api_key` | `str \| None` | `None` | Chave da API (ou env var) |
| `base_url` | `str` | `"https://chat.maritaca.ai/api"` | URL base da API |
| `timeout` | `float` | `60.0` | Timeout em segundos |
| `max_retries` | `int` | `2` | Máximo de retentativas |
| `streaming` | `bool` | `False` | Habilita streaming por padrão |

### Parâmetros de Tools

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `tools` | `list[dict] \| None` | `None` | Lista de ferramentas disponíveis |
| `tool_choice` | `str \| dict \| None` | `None` | Controle de seleção de ferramenta |

## Métodos

### invoke()

Executa uma única chamada ao modelo.

```python
def invoke(
    messages: list[BaseMessage],
    stop: list[str] | None = None,
    **kwargs
) -> AIMessage
```

**Exemplo:**

```python
from langchain_core.messages import HumanMessage

resposta = modelo.invoke([HumanMessage(content="Olá!")])
print(resposta.content)
```

### ainvoke()

Versão assíncrona do `invoke()`.

```python
async def ainvoke(
    messages: list[BaseMessage],
    stop: list[str] | None = None,
    **kwargs
) -> AIMessage
```

**Exemplo:**

```python
resposta = await modelo.ainvoke([HumanMessage(content="Olá!")])
```

### stream()

Retorna um iterador de chunks da resposta.

```python
def stream(
    messages: list[BaseMessage],
    stop: list[str] | None = None,
    **kwargs
) -> Iterator[AIMessageChunk]
```

**Exemplo:**

```python
for chunk in modelo.stream([HumanMessage(content="Conte uma história.")]):
    print(chunk.content, end="")
```

### astream()

Versão assíncrona do `stream()`.

```python
async def astream(
    messages: list[BaseMessage],
    stop: list[str] | None = None,
    **kwargs
) -> AsyncIterator[AIMessageChunk]
```

**Exemplo:**

```python
async for chunk in modelo.astream([HumanMessage(content="...")]):
    print(chunk.content, end="")
```

### batch()

Processa múltiplas conversas.

```python
def batch(
    inputs: list[list[BaseMessage]],
    config: dict | None = None,
    **kwargs
) -> list[AIMessage]
```

**Exemplo:**

```python
respostas = modelo.batch([
    [HumanMessage(content="Pergunta 1")],
    [HumanMessage(content="Pergunta 2")],
])
```

### abatch()

Versão assíncrona do `batch()`.

### bind_tools()

Vincula ferramentas ao modelo para function calling.

```python
def bind_tools(
    tools: Sequence[dict | type | Callable | BaseTool],
    *,
    tool_choice: str | dict | None = None,
    **kwargs
) -> Runnable
```

**Parâmetros:**

- `tools`: Lista de ferramentas (Pydantic models, funções, ou dicts)
- `tool_choice`: Controle de seleção
  - `"auto"`: Modelo decide (padrão)
  - `"required"`: Força uso de ferramenta
  - `{"type": "function", "function": {"name": "..."}}`: Ferramenta específica

**Exemplo:**

```python
from pydantic import BaseModel, Field

class ObterClima(BaseModel):
    """Obtém o clima."""
    cidade: str = Field(description="Nome da cidade")

modelo_com_tools = modelo.bind_tools([ObterClima])
resposta = modelo_com_tools.invoke([HumanMessage(content="Clima em SP?")])
```

## Propriedades

### _llm_type

```python
@property
def _llm_type(self) -> str
```

Retorna `"maritaca-chat"`.

### _default_params

```python
@property
def _default_params(self) -> dict[str, Any]
```

Retorna os parâmetros padrão para chamadas de API.

### lc_secrets

```python
@property
def lc_secrets(self) -> dict[str, str]
```

Mapeia variáveis de ambiente secretas.

## Tipos de Retorno

### AIMessage

Resposta padrão do modelo:

```python
AIMessage(
    content="Texto da resposta",
    tool_calls=[...],  # Se houver chamadas de ferramentas
    usage_metadata={
        "input_tokens": 10,
        "output_tokens": 20,
        "total_tokens": 30,
    },
    response_metadata={
        "model": "sabia-3.1",
        "finish_reason": "stop",
    },
)
```

### AIMessageChunk

Chunk de streaming:

```python
AIMessageChunk(
    content="Token ",
    response_metadata={...},  # Apenas no último chunk
)
```

## Exceções

| Exceção | Causa |
|---------|-------|
| `httpx.HTTPStatusError` | Erro HTTP (401, 429, 500, etc.) |
| `httpx.TimeoutException` | Timeout na requisição |
| `ValueError` | Parâmetros inválidos |
| `RuntimeError` | Falha após retentativas |

## Variáveis de Ambiente

| Variável | Descrição |
|----------|-----------|
| `MARITACA_API_KEY` | Chave de autenticação |
| `MARITACA_API_BASE` | URL base customizada |
