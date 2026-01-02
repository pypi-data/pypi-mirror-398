# langchain-maritaca

[![PyPI version](https://img.shields.io/pypi/v/langchain-maritaca.svg)](https://pypi.org/project/langchain-maritaca/)
[![Python](https://img.shields.io/pypi/pyversions/langchain-maritaca.svg)](https://pypi.org/project/langchain-maritaca/)
[![Downloads](https://img.shields.io/pypi/dm/langchain-maritaca.svg)](https://pypi.org/project/langchain-maritaca/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/anderson-ufrj/langchain-maritaca/actions/workflows/ci.yml/badge.svg)](https://github.com/anderson-ufrj/langchain-maritaca/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/anderson-ufrj/langchain-maritaca/graph/badge.svg)](https://codecov.io/gh/anderson-ufrj/langchain-maritaca)

[🇺🇸 Read in English](README.md)

Pacote de integração conectando [Maritaca AI](https://www.maritaca.ai/) e [LangChain](https://langchain.com/) para modelos de linguagem otimizados para Português Brasileiro.

**Autor:** Anderson Henrique da Silva
**Localização:** Minas Gerais, Brasil
**GitHub:** [anderson-ufrj](https://github.com/anderson-ufrj)

## Visão Geral

A Maritaca AI oferece modelos de linguagem de última geração para Português Brasileiro, incluindo a família de modelos Sabiá. Esta integração permite usar os modelos da Maritaca de forma transparente dentro do ecossistema LangChain.

### Modelos Disponíveis

| Modelo | Descrição | Preço (por 1M tokens) |
|--------|-----------|----------------------|
| `sabia-3.1.1` | Modelo mais capaz, ideal para tarefas complexas | Consulte [Maritaca AI](https://www.maritaca.ai/) |
| `sabiazinho-3.1` | Rápido e econômico, ótimo para tarefas simples | Consulte [Maritaca AI](https://www.maritaca.ai/) |

## Instalação

```bash
pip install langchain-maritaca
```

## Configuração

Defina sua chave de API da Maritaca como variável de ambiente:

```bash
export MARITACA_API_KEY="sua-chave-api"
```

Ou passe diretamente para o modelo:

```python
from langchain_maritaca import ChatMaritaca

model = ChatMaritaca(api_key="sua-chave-api")
```

## Uso

### Uso Básico

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

### Uso Assíncrono

```python
import asyncio
from langchain_maritaca import ChatMaritaca

async def main():
    model = ChatMaritaca(model="sabia-3.1")
    response = await model.ainvoke("Qual é a receita de pão de queijo?")
    print(response.content)

asyncio.run(main())
```

### Com LangChain Expression Language (LCEL)

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

### Com Tool Calling (Chamada de Funções)

```python
from langchain_maritaca import ChatMaritaca
from langchain_core.tools import tool

@tool
def get_weather(city: str) -> str:
    """Obtém o clima atual para uma cidade."""
    return f"O clima em {city} está ensolarado, 25°C"

model = ChatMaritaca(model="sabia-3.1")
model_with_tools = model.bind_tools([get_weather])

response = model_with_tools.invoke("Como está o tempo em São Paulo?")
print(response)
```

### Com Saída Estruturada

```python
from langchain_maritaca import ChatMaritaca
from pydantic import BaseModel, Field

class Pessoa(BaseModel):
    """Informações sobre uma pessoa."""
    nome: str = Field(description="Nome da pessoa")
    idade: int = Field(description="Idade da pessoa")

model = ChatMaritaca(model="sabia-3.1")
structured_model = model.with_structured_output(Pessoa)

result = structured_model.invoke("João tem 25 anos e mora em São Paulo")
print(result)  # Pessoa(nome="João", idade=25)
```

### Com Embeddings para RAG

```python
from langchain_maritaca import ChatMaritaca, DeepInfraEmbeddings

# Embeddings para recuperação de documentos
embeddings = DeepInfraEmbeddings()
vectors = embeddings.embed_documents([
    "O Brasil foi descoberto em 1500",
    "A capital do Brasil é Brasília"
])

# Chat para geração de respostas
chat = ChatMaritaca(model="sabia-3.1")
```

## Por que Maritaca AI?

Os modelos da Maritaca AI são especificamente treinados para Português Brasileiro, oferecendo:

- **Compreensão Nativa do Português**: Melhor entendimento de expressões idiomáticas, gírias e contexto cultural brasileiro
- **Treinamento com Dados Locais**: Treinado em fontes diversas de dados em Português Brasileiro
- **Custo-Benefício**: Preços competitivos para tarefas em português
- **Baixa Latência**: Servidores localizados no Brasil para respostas mais rápidas

## Usado em Produção

**[Cidadão.AI](https://cidadao-ai-frontend.vercel.app/pt)** - Plataforma brasileira de transparência governamental alimentada por agentes de IA, processando mais de 331K requisições/mês.

- Frontend: [github.com/anderson-ufrj/cidadao.ai-frontend](https://github.com/anderson-ufrj/cidadao.ai-frontend)
- Backend: [github.com/anderson-ufrj/cidadao.ai-backend](https://github.com/anderson-ufrj/cidadao.ai-backend)

> *Usando este pacote em produção? [Abra uma issue](https://github.com/anderson-ufrj/langchain-maritaca/issues) para ser destacado!*

## Referência da API

### ChatMaritaca

Classe principal para interagir com os modelos da Maritaca AI.

**Parâmetros:**

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `model` | str | `"sabia-3.1"` | Nome do modelo a usar |
| `temperature` | float | `0.7` | Temperatura de amostragem (0.0-2.0) |
| `max_tokens` | int | None | Máximo de tokens a gerar |
| `top_p` | float | `0.9` | Parâmetro top-p de amostragem |
| `api_key` | str | None | Chave de API da Maritaca (ou use var de ambiente) |
| `base_url` | str | `"https://chat.maritaca.ai/api"` | URL base da API |
| `timeout` | float | `60.0` | Timeout da requisição em segundos |
| `max_retries` | int | `2` | Máximo de tentativas de retry |
| `retry_if_rate_limited` | bool | `True` | Auto-retry em rate limit (HTTP 429) |
| `retry_delay` | float | `1.0` | Delay inicial entre retries (segundos) |
| `retry_max_delay` | float | `60.0` | Delay máximo entre retries (segundos) |
| `retry_multiplier` | float | `2.0` | Multiplicador para backoff exponencial |
| `streaming` | bool | `False` | Habilitar respostas em streaming |

### DeepInfraEmbeddings

Classe para gerar embeddings usando DeepInfra (recomendado pela Maritaca AI).

**Parâmetros:**

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `model` | str | `"intfloat/multilingual-e5-large"` | Modelo de embeddings |
| `api_key` | str | None | Chave de API DeepInfra (ou use var de ambiente) |
| `batch_size` | int | `32` | Tamanho do lote para processamento |

## Desenvolvimento

### Configuração

```bash
# Clone o repositório
git clone https://github.com/anderson-ufrj/langchain-maritaca.git
cd langchain-maritaca

# Instale as dependências
pip install -e ".[dev]"

# Execute os testes
pytest

# Execute o linting
ruff check .
ruff format .

# Execute a verificação de tipos
mypy langchain_maritaca
```

### Executando Testes

```bash
# Apenas testes unitários
pytest tests/unit_tests/

# Testes de integração (requer MARITACA_API_KEY)
pytest tests/integration_tests/

# Com cobertura
pytest --cov=langchain_maritaca --cov-report=html
```

## Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para enviar um Pull Request.

1. Faça um fork do repositório
2. Crie sua branch de feature (`git checkout -b feature/feature-incrivel`)
3. Commit suas alterações (`git commit -m 'feat: adiciona feature incrível'`)
4. Push para a branch (`git push origin feature/feature-incrivel`)
5. Abra um Pull Request

## Changelog

Veja [CHANGELOG.md](CHANGELOG.md) para a lista de alterações.

## Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## Projetos Relacionados

- [LangChain](https://github.com/langchain-ai/langchain) - Construindo aplicações com LLMs através de composabilidade
- [Maritaca AI](https://www.maritaca.ai/) - Modelos de linguagem para Português Brasileiro
