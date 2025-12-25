# Uso Básico

Aprenda os fundamentos do uso do ChatMaritaca.

## Tipos de Mensagem

O LangChain usa mensagens tipadas para conversas:

```python
from langchain_core.messages import (
    SystemMessage,    # Instruções para o modelo
    HumanMessage,     # Entrada do usuário
    AIMessage,        # Resposta do modelo
    ToolMessage,      # Resultados de execução de ferramentas
)
```

### SystemMessage

Define o comportamento e contexto para o modelo:

```python
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_maritaca import ChatMaritaca

modelo = ChatMaritaca()

resposta = modelo.invoke([
    SystemMessage(content="Você é um chef brasileiro especializado em feijoada."),
    HumanMessage(content="Como fazer uma feijoada?"),
])
```

### HumanMessage

Representa a entrada do usuário:

```python
resposta = modelo.invoke([
    HumanMessage(content="Explique machine learning em termos simples.")
])
```

### AIMessage

Representa respostas do modelo (usado em conversas multi-turno):

```python
mensagens = [
    HumanMessage(content="Meu nome é Maria."),
    AIMessage(content="Olá Maria! Como posso ajudá-la?"),
    HumanMessage(content="Qual é o meu nome?"),
]

resposta = modelo.invoke(mensagens)
# Modelo lembra: "Seu nome é Maria."
```

## Atalho com Tuplas de String

Por conveniência, você pode usar tuplas ao invés de objetos de mensagem:

```python
resposta = modelo.invoke([
    ("system", "Você é um assistente prestativo."),
    ("human", "Olá!"),
    ("ai", "Olá! Como posso ajudar?"),
    ("human", "Conte uma piada."),
])
```

| Papel na Tupla | Tipo de Mensagem |
|----------------|------------------|
| `"system"` | SystemMessage |
| `"human"` / `"user"` | HumanMessage |
| `"ai"` / `"assistant"` | AIMessage |

## Invoke vs Generate

### invoke() - Resposta Única

Retorna uma única `AIMessage`:

```python
resposta = modelo.invoke([("human", "Olá!")])
print(resposta.content)
print(resposta.usage_metadata)
```

### generate() - Múltiplas Respostas

Retorna um `ChatResult` com metadados:

```python
resultado = modelo.generate([[("human", "Olá!")]])

for geracao in resultado.generations[0]:
    print(geracao.message.content)

print(resultado.llm_output)  # Uso de tokens, info do modelo
```

## Processamento em Lote

Processe múltiplas conversas de uma vez:

```python
conversas = [
    [("human", "O que é Python?")],
    [("human", "O que é JavaScript?")],
    [("human", "O que é Rust?")],
]

respostas = modelo.batch(conversas)

for resp in respostas:
    print(f"- {resp.content[:50]}...")
```

### Com Controle de Concorrência

```python
respostas = modelo.batch(
    conversas,
    config={"max_concurrency": 2}
)
```

## Metadados da Resposta

Toda resposta inclui metadados úteis:

```python
resposta = modelo.invoke([("human", "Olá!")])

# Uso de tokens
print(resposta.usage_metadata)
# {'input_tokens': 5, 'output_tokens': 12, 'total_tokens': 17}

# Metadados da resposta
print(resposta.response_metadata)
# {'model': 'sabia-3.1', 'finish_reason': 'stop'}

# ID da mensagem
print(resposta.id)
```

## Sequências de Parada

Para a geração em tokens específicos:

```python
# Método 1: No construtor
modelo = ChatMaritaca(stop_sequences=["FIM", "PARE"])

# Método 2: No momento do invoke
resposta = modelo.invoke(
    [("human", "Liste 5 frutas, termine com FIM")],
    stop=["FIM"]
)
```

## Controle de Temperature

Ajuste a criatividade/aleatoriedade:

```python
# Determinístico (mesma entrada = mesma saída)
modelo_preciso = ChatMaritaca(temperature=0.0)

# Criativo
modelo_criativo = ChatMaritaca(temperature=1.5)

prompt = [("human", "Invente um nome para uma startup de IA")]

# Preciso: Dará respostas consistentes
print(modelo_preciso.invoke(prompt).content)

# Criativo: Variará a cada vez
print(modelo_criativo.invoke(prompt).content)
```

## Max Tokens

Limita o tamanho da resposta:

```python
modelo = ChatMaritaca(max_tokens=50)

resposta = modelo.invoke([
    ("human", "Escreva um ensaio sobre a história do Brasil")
])
# Resposta será truncada para ~50 tokens
```

## Tratamento de Erros

```python
from langchain_maritaca import ChatMaritaca
import httpx

modelo = ChatMaritaca()

try:
    resposta = modelo.invoke([("human", "Olá!")])
except httpx.HTTPStatusError as e:
    if e.response.status_code == 401:
        print("Chave de API inválida")
    elif e.response.status_code == 429:
        print("Rate limit atingido - aguarde e tente novamente")
    else:
        print(f"Erro HTTP: {e}")
except httpx.TimeoutException:
    print("Timeout na requisição")
except Exception as e:
    print(f"Erro inesperado: {e}")
```

## Estado da Conversa

ChatMaritaca é stateless. Você gerencia o histórico da conversa:

```python
class Conversa:
    def __init__(self):
        self.modelo = ChatMaritaca()
        self.mensagens = []

    def adicionar_sistema(self, conteudo: str):
        self.mensagens.append(("system", conteudo))

    def conversar(self, entrada_usuario: str) -> str:
        self.mensagens.append(("human", entrada_usuario))
        resposta = self.modelo.invoke(self.mensagens)
        self.mensagens.append(("ai", resposta.content))
        return resposta.content

# Uso
conv = Conversa()
conv.adicionar_sistema("Você é um tutor de matemática.")
print(conv.conversar("O que é uma derivada?"))
print(conv.conversar("Me dê um exemplo prático."))
```

## Próximos Passos

- [Streaming](streaming.md) - Respostas em tempo real
- [Suporte Async](async.md) - Operações concorrentes
- [Chamada de Ferramentas](tool-calling.md) - Function calling
