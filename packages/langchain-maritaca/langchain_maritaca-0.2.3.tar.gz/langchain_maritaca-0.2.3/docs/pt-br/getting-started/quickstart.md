# Início Rápido

Obtenha sua primeira resposta em menos de 5 minutos.

## 1. Configure sua Chave de API

=== "Variável de Ambiente"

    ```bash
    export MARITACA_API_KEY="sua-chave-api-aqui"
    ```

=== "Python"

    ```python
    import os
    os.environ["MARITACA_API_KEY"] = "sua-chave-api-aqui"
    ```

=== "Parâmetro Direto"

    ```python
    modelo = ChatMaritaca(api_key="sua-chave-api-aqui")
    ```

!!! tip "Obtendo uma Chave de API"
    Obtenha sua chave de API em [plataforma.maritaca.ai](https://plataforma.maritaca.ai/)

## 2. Uso Básico

```python
from langchain_maritaca import ChatMaritaca
from langchain_core.messages import HumanMessage, SystemMessage

# Inicializa o modelo
modelo = ChatMaritaca(
    model="sabia-3.1",      # Modelo mais capaz
    temperature=0.7,         # Nível de criatividade (0.0-2.0)
)

# Cria as mensagens
mensagens = [
    SystemMessage(content="Você é um assistente prestativo que responde em português."),
    HumanMessage(content="O que é inteligência artificial?"),
]

# Obtém a resposta
resposta = modelo.invoke(mensagens)
print(resposta.content)
```

## 3. Usando Tuplas de String (Atalho)

O LangChain suporta um formato conveniente de tuplas:

```python
resposta = modelo.invoke([
    ("system", "Você é um poeta brasileiro."),
    ("human", "Escreva um haiku sobre o Rio de Janeiro."),
])

print(resposta.content)
```

## 4. Streaming de Respostas

Para saída em tempo real:

```python
for chunk in modelo.stream([("human", "Conte uma história curta.")]):
    print(chunk.content, end="", flush=True)
```

## 5. Verificar Uso de Tokens

```python
resposta = modelo.invoke([("human", "Olá!")])

print(f"Tokens de entrada: {resposta.usage_metadata['input_tokens']}")
print(f"Tokens de saída: {resposta.usage_metadata['output_tokens']}")
print(f"Total de tokens: {resposta.usage_metadata['total_tokens']}")
```

## Exemplo Completo

```python
from langchain_maritaca import ChatMaritaca

# Inicializa
modelo = ChatMaritaca(model="sabia-3.1")

# Conversa simples
conversa = [
    ("system", "Você é um especialista em história do Brasil."),
    ("human", "Quem foi Tiradentes?"),
]

# Obtém resposta
resposta = modelo.invoke(conversa)
print(resposta.content)

# Continua a conversa
conversa.append(("assistant", resposta.content))
conversa.append(("human", "E qual foi sua importância?"))

resposta = modelo.invoke(conversa)
print(resposta.content)
```

## Próximos Passos

- [Configuração](configuration.md) - Opções avançadas de configuração
- [Uso Básico](../guide/basic-usage.md) - Mais padrões de uso
- [Chamada de Ferramentas](../guide/tool-calling.md) - Function calling com tools
