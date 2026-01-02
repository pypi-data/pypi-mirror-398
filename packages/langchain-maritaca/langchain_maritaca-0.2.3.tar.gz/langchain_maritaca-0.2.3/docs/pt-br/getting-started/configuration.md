# Configuração

## Chave de API

A chave de API pode ser configurada de várias formas (em ordem de precedência):

### 1. Parâmetro Direto

```python
modelo = ChatMaritaca(api_key="sua-chave-api")
```

### 2. Variável de Ambiente

```bash
export MARITACA_API_KEY="sua-chave-api"
```

```python
modelo = ChatMaritaca()  # Usa automaticamente a variável de ambiente
```

## Parâmetros do Modelo

### Modelos Disponíveis

| Modelo | Descrição | Caso de Uso |
|--------|-----------|-------------|
| `sabia-3.1` | Mais capaz | Raciocínio complexo, análise |
| `sabiazinho-3.1` | Rápido e barato | Tarefas simples, alto volume |

### Temperature

Controla a aleatoriedade nas respostas:

```python
# Determinístico (bom para consultas factuais)
modelo = ChatMaritaca(temperature=0.0)

# Balanceado (padrão)
modelo = ChatMaritaca(temperature=0.7)

# Criativo (bom para brainstorming)
modelo = ChatMaritaca(temperature=1.5)
```

!!! note "Intervalo de Temperature"
    O intervalo válido é de `0.0` a `2.0`. Valores mais próximos de 0 são mais determinísticos.

### Max Tokens

Limita o tamanho da resposta:

```python
modelo = ChatMaritaca(max_tokens=500)
```

### Top P (Amostragem Nucleus)

Alternativa à temperature para controlar aleatoriedade:

```python
modelo = ChatMaritaca(top_p=0.9)  # Padrão
```

### Penalidades

Controla repetição nas respostas:

```python
modelo = ChatMaritaca(
    frequency_penalty=0.5,   # Reduz repetição de palavras (-2.0 a 2.0)
    presence_penalty=0.5,    # Incentiva novos tópicos (-2.0 a 2.0)
)
```

### Sequências de Parada

Para a geração em tokens específicos:

```python
modelo = ChatMaritaca(stop_sequences=["FIM", "PARE"])
```

## Configuração do Cliente

### Timeout

Define o timeout da requisição (em segundos):

```python
modelo = ChatMaritaca(timeout=120.0)  # 2 minutos
```

### Retentativas

Configura o comportamento de retry:

```python
modelo = ChatMaritaca(max_retries=3)  # Padrão é 2
```

### URL Base Customizada

Para endpoints de API customizados:

```python
modelo = ChatMaritaca(base_url="https://api-customizada.exemplo.com")
```

## Exemplo de Configuração Completa

```python
from langchain_maritaca import ChatMaritaca

modelo = ChatMaritaca(
    # Seleção do modelo
    model="sabia-3.1",

    # Parâmetros de geração
    temperature=0.7,
    max_tokens=1000,
    top_p=0.9,
    frequency_penalty=0.0,
    presence_penalty=0.0,
    stop_sequences=None,

    # Configuração do cliente
    api_key="sua-chave-api",  # Ou use variável de ambiente
    timeout=60.0,
    max_retries=2,

    # Streaming
    streaming=False,
)
```

## Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `MARITACA_API_KEY` | Chave de autenticação da API | Obrigatório |
| `MARITACA_API_BASE` | URL base customizada da API | `https://chat.maritaca.ai/api` |

## Aliases de Parâmetros

Alguns parâmetros possuem aliases para conveniência:

| Parâmetro | Alias |
|-----------|-------|
| `model_name` | `model` |
| `api_key` | `maritaca_api_key` |
| `base_url` | `maritaca_api_base` |
| `timeout` | `request_timeout` |
| `stop_sequences` | `stop` |
