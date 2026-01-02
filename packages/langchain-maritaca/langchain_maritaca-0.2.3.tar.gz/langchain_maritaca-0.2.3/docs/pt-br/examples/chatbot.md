# Chatbot Simples

Um exemplo completo de chatbot com memória de conversa.

## Código Completo

```python
from langchain_maritaca import ChatMaritaca
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


class ChatBot:
    """Chatbot simples com memória de conversa."""

    def __init__(
        self,
        system_prompt: str = "Você é um assistente prestativo.",
        model: str = "sabia-3.1",
        max_history: int = 10,
    ):
        self.modelo = ChatMaritaca(model=model, temperature=0.7)
        self.system_prompt = system_prompt
        self.historico: list = []
        self.max_history = max_history

    def _construir_mensagens(self, entrada: str) -> list:
        """Constrói lista de mensagens para o modelo."""
        mensagens = [SystemMessage(content=self.system_prompt)]
        mensagens.extend(self.historico)
        mensagens.append(HumanMessage(content=entrada))
        return mensagens

    def _atualizar_historico(self, entrada: str, resposta: str):
        """Atualiza o histórico mantendo o limite."""
        self.historico.append(HumanMessage(content=entrada))
        self.historico.append(AIMessage(content=resposta))

        # Mantém apenas as últimas N mensagens
        if len(self.historico) > self.max_history * 2:
            self.historico = self.historico[-(self.max_history * 2):]

    def chat(self, entrada: str) -> str:
        """Envia mensagem e retorna resposta."""
        mensagens = self._construir_mensagens(entrada)
        resposta = self.modelo.invoke(mensagens)
        self._atualizar_historico(entrada, resposta.content)
        return resposta.content

    def chat_stream(self, entrada: str):
        """Envia mensagem e retorna resposta em streaming."""
        mensagens = self._construir_mensagens(entrada)

        resposta_completa = ""
        for chunk in self.modelo.stream(mensagens):
            if chunk.content:
                resposta_completa += chunk.content
                yield chunk.content

        self._atualizar_historico(entrada, resposta_completa)

    def limpar_historico(self):
        """Limpa o histórico de conversa."""
        self.historico = []


# Exemplo de uso
if __name__ == "__main__":
    bot = ChatBot(
        system_prompt="Você é Sabiá, um assistente brasileiro simpático e prestativo."
    )

    print("ChatBot iniciado! Digite 'sair' para encerrar.\n")

    while True:
        entrada = input("Você: ").strip()

        if entrada.lower() == "sair":
            print("Até logo!")
            break

        if entrada.lower() == "limpar":
            bot.limpar_historico()
            print("Histórico limpo!\n")
            continue

        if not entrada:
            continue

        print("Sabiá: ", end="", flush=True)
        for chunk in bot.chat_stream(entrada):
            print(chunk, end="", flush=True)
        print("\n")
```

## Versão com FastAPI

```python
from fastapi import FastAPI, WebSocket
from langchain_maritaca import ChatMaritaca
from pydantic import BaseModel

app = FastAPI()
modelo = ChatMaritaca()

# Estado por sessão (em produção, use Redis/DB)
sessoes: dict[str, list] = {}


class MensagemRequest(BaseModel):
    sessao_id: str
    mensagem: str


class MensagemResponse(BaseModel):
    resposta: str


@app.post("/chat", response_model=MensagemResponse)
async def chat(request: MensagemRequest):
    # Recupera ou cria histórico da sessão
    if request.sessao_id not in sessoes:
        sessoes[request.sessao_id] = []

    historico = sessoes[request.sessao_id]

    # Constrói mensagens
    mensagens = [
        ("system", "Você é um assistente prestativo."),
        *historico,
        ("human", request.mensagem),
    ]

    # Obtém resposta
    resposta = await modelo.ainvoke(mensagens)

    # Atualiza histórico
    historico.append(("human", request.mensagem))
    historico.append(("assistant", resposta.content))

    # Limita histórico
    if len(historico) > 20:
        sessoes[request.sessao_id] = historico[-20:]

    return MensagemResponse(resposta=resposta.content)


@app.websocket("/ws/{sessao_id}")
async def websocket_chat(websocket: WebSocket, sessao_id: str):
    await websocket.accept()

    if sessao_id not in sessoes:
        sessoes[sessao_id] = []

    while True:
        mensagem = await websocket.receive_text()
        historico = sessoes[sessao_id]

        mensagens = [
            ("system", "Você é um assistente prestativo."),
            *historico,
            ("human", mensagem),
        ]

        # Streaming via WebSocket
        resposta_completa = ""
        async for chunk in modelo.astream(mensagens):
            if chunk.content:
                resposta_completa += chunk.content
                await websocket.send_text(chunk.content)

        # Marca fim do streaming
        await websocket.send_text("[FIM]")

        # Atualiza histórico
        historico.append(("human", mensagem))
        historico.append(("assistant", resposta_completa))
```

## Versão com Gradio

```python
import gradio as gr
from langchain_maritaca import ChatMaritaca

modelo = ChatMaritaca()


def responder(mensagem, historico):
    # Converte histórico do Gradio para formato LangChain
    mensagens = [("system", "Você é um assistente prestativo.")]

    for h in historico:
        mensagens.append(("human", h[0]))
        if h[1]:
            mensagens.append(("assistant", h[1]))

    mensagens.append(("human", mensagem))

    # Streaming
    resposta = ""
    for chunk in modelo.stream(mensagens):
        if chunk.content:
            resposta += chunk.content
            yield resposta


demo = gr.ChatInterface(
    responder,
    title="ChatBot Maritaca",
    description="Chat com o modelo Sabiá-3.1 da Maritaca AI",
    theme="soft",
)

if __name__ == "__main__":
    demo.launch()
```

## Próximos Passos

- [Pipeline RAG](rag.md) - Adicione conhecimento externo
- [Agente com Ferramentas](agent.md) - Adicione capacidades de ação
