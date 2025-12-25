# Suporte Async

O ChatMaritaca oferece suporte nativo a operações assíncronas para aplicações de alta concorrência.

## Métodos Assíncronos

| Método Síncrono | Método Assíncrono |
|-----------------|-------------------|
| `invoke()` | `ainvoke()` |
| `stream()` | `astream()` |
| `batch()` | `abatch()` |
| `generate()` | `agenerate()` |

## Uso Básico

```python
import asyncio
from langchain_maritaca import ChatMaritaca

async def main():
    modelo = ChatMaritaca()

    resposta = await modelo.ainvoke([
        ("human", "Qual é a capital do Brasil?")
    ])

    print(resposta.content)

asyncio.run(main())
```

## Chamadas Concorrentes

```python
import asyncio
from langchain_maritaca import ChatMaritaca

async def processar_pergunta(modelo, pergunta):
    resposta = await modelo.ainvoke([("human", pergunta)])
    return resposta.content

async def main():
    modelo = ChatMaritaca()

    perguntas = [
        "O que é Python?",
        "O que é JavaScript?",
        "O que é Rust?",
    ]

    # Executa todas as perguntas concorrentemente
    tarefas = [processar_pergunta(modelo, p) for p in perguntas]
    respostas = await asyncio.gather(*tarefas)

    for pergunta, resposta in zip(perguntas, respostas):
        print(f"P: {pergunta}")
        print(f"R: {resposta[:100]}...\n")

asyncio.run(main())
```

## Streaming Assíncrono

```python
import asyncio
from langchain_maritaca import ChatMaritaca

async def main():
    modelo = ChatMaritaca()

    async for chunk in modelo.astream([
        ("human", "Conte uma história curta.")
    ]):
        print(chunk.content, end="", flush=True)

asyncio.run(main())
```

## Batch Assíncrono

```python
import asyncio
from langchain_maritaca import ChatMaritaca

async def main():
    modelo = ChatMaritaca()

    conversas = [
        [("human", "O que é IA?")],
        [("human", "O que é ML?")],
        [("human", "O que é DL?")],
    ]

    respostas = await modelo.abatch(conversas)

    for resp in respostas:
        print(f"- {resp.content[:50]}...")

asyncio.run(main())
```

## Com FastAPI

```python
from fastapi import FastAPI
from langchain_maritaca import ChatMaritaca
from pydantic import BaseModel

app = FastAPI()
modelo = ChatMaritaca()

class Pergunta(BaseModel):
    texto: str

@app.post("/chat")
async def chat(pergunta: Pergunta):
    resposta = await modelo.ainvoke([
        ("human", pergunta.texto)
    ])
    return {"resposta": resposta.content}
```

## Timeout e Tratamento de Erros

```python
import asyncio
from langchain_maritaca import ChatMaritaca

async def main():
    modelo = ChatMaritaca(timeout=30.0)

    try:
        resposta = await asyncio.wait_for(
            modelo.ainvoke([("human", "Pergunta complexa...")]),
            timeout=60.0  # Timeout adicional do asyncio
        )
        print(resposta.content)
    except asyncio.TimeoutError:
        print("Operação expirou!")
    except Exception as e:
        print(f"Erro: {e}")

asyncio.run(main())
```

## Semáforo para Controle de Concorrência

```python
import asyncio
from langchain_maritaca import ChatMaritaca

async def processar_com_limite(semaforo, modelo, pergunta):
    async with semaforo:
        resposta = await modelo.ainvoke([("human", pergunta)])
        return resposta.content

async def main():
    modelo = ChatMaritaca()
    semaforo = asyncio.Semaphore(3)  # Máximo 3 requisições simultâneas

    perguntas = [f"Pergunta {i}" for i in range(10)]

    tarefas = [
        processar_com_limite(semaforo, modelo, p)
        for p in perguntas
    ]

    respostas = await asyncio.gather(*tarefas)
    print(f"Processadas {len(respostas)} respostas")

asyncio.run(main())
```

## Boas Práticas

1. **Reutilize a instância do modelo** - Não crie uma nova instância para cada requisição
2. **Use semáforos** - Controle a concorrência para evitar rate limiting
3. **Trate exceções** - Sempre envolva chamadas async em try/except
4. **Configure timeouts** - Evite que requisições travem indefinidamente

## Próximos Passos

- [Integração LCEL](lcel.md) - Chains assíncronas
- [Chamada de Ferramentas](tool-calling.md) - Async com tools
