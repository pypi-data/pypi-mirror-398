# Streaming

Streaming permite receber tokens em tempo real conforme são gerados, melhorando a experiência do usuário em aplicações interativas.

## Streaming Básico

```python
from langchain_maritaca import ChatMaritaca

modelo = ChatMaritaca()

for chunk in modelo.stream([("human", "Conte uma história sobre o Brasil.")]):
    print(chunk.content, end="", flush=True)
```

## Com Callback Handler

```python
from langchain_core.callbacks import StreamingStdOutCallbackHandler

modelo = ChatMaritaca(
    streaming=True,
    callbacks=[StreamingStdOutCallbackHandler()]
)

# Tokens são impressos automaticamente pelo callback
resposta = modelo.invoke([("human", "Explique a fotossíntese.")])
```

## Streaming Assíncrono

```python
import asyncio
from langchain_maritaca import ChatMaritaca

async def streaming_async():
    modelo = ChatMaritaca()

    async for chunk in modelo.astream([("human", "Liste 5 pontos turísticos do Rio.")]):
        print(chunk.content, end="", flush=True)

asyncio.run(streaming_async())
```

## Coletando Chunks

```python
modelo = ChatMaritaca()

chunks = []
for chunk in modelo.stream([("human", "O que é Python?")]):
    chunks.append(chunk)

# Combina todos os chunks
resposta_completa = "".join(c.content for c in chunks if c.content)
print(resposta_completa)
```

## Metadados no Streaming

O último chunk contém metadados de finalização:

```python
for chunk in modelo.stream([("human", "Olá!")]):
    if chunk.response_metadata:
        print(f"\nFinish reason: {chunk.response_metadata.get('finish_reason')}")
    else:
        print(chunk.content, end="")
```

## Streaming em Aplicações Web

### FastAPI

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_maritaca import ChatMaritaca

app = FastAPI()
modelo = ChatMaritaca()

@app.get("/stream")
async def stream_response(pergunta: str):
    async def gerar():
        async for chunk in modelo.astream([("human", pergunta)]):
            if chunk.content:
                yield chunk.content

    return StreamingResponse(gerar(), media_type="text/plain")
```

### Flask

```python
from flask import Flask, Response
from langchain_maritaca import ChatMaritaca

app = Flask(__name__)
modelo = ChatMaritaca()

@app.route("/stream")
def stream_response():
    pergunta = request.args.get("pergunta", "Olá!")

    def gerar():
        for chunk in modelo.stream([("human", pergunta)]):
            if chunk.content:
                yield chunk.content

    return Response(gerar(), mimetype="text/plain")
```

## Streaming vs Non-Streaming

| Aspecto | Streaming | Non-Streaming |
|---------|-----------|---------------|
| Latência inicial | Baixa | Alta |
| UX | Melhor para chat | OK para background |
| Complexidade | Maior | Menor |
| Uso de memória | Menor | Maior (resposta completa) |

## Quando Usar Streaming

✅ **Use streaming quando:**

- Construindo interfaces de chat
- Respostas longas são esperadas
- Feedback em tempo real é importante

❌ **Evite streaming quando:**

- Processando em background
- Precisa da resposta completa antes de processar
- Integrando com APIs que não suportam streaming

## Próximos Passos

- [Suporte Async](async.md) - Operações assíncronas
- [Integração LCEL](lcel.md) - Streaming com chains
