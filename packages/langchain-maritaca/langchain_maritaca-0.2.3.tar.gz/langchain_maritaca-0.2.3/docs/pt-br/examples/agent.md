# Agente com Ferramentas

Exemplo de agente que pode usar ferramentas para realizar ações no mundo real.

!!! note "Dependências"
    Este exemplo requer dependências adicionais:
    ```bash
    pip install langchain langgraph
    ```

## Agente Básico com Ferramentas

```python
from langchain_maritaca import ChatMaritaca
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage

# 1. Definir ferramentas
@tool
def calcular(expressao: str) -> str:
    """Calcula uma expressão matemática."""
    try:
        resultado = eval(expressao)
        return f"Resultado: {resultado}"
    except Exception as e:
        return f"Erro: {e}"

@tool
def obter_hora_atual() -> str:
    """Retorna a hora atual."""
    from datetime import datetime
    return datetime.now().strftime("%H:%M:%S")

@tool
def buscar_cep(cep: str) -> str:
    """Busca informações de um CEP brasileiro."""
    import httpx
    response = httpx.get(f"https://viacep.com.br/ws/{cep}/json/")
    if response.status_code == 200:
        data = response.json()
        return f"{data.get('logradouro', '')}, {data.get('bairro', '')}, {data.get('localidade', '')}-{data.get('uf', '')}"
    return "CEP não encontrado"

# 2. Criar modelo com ferramentas
modelo = ChatMaritaca()
tools = [calcular, obter_hora_atual, buscar_cep]
modelo_com_tools = modelo.bind_tools(tools)

# 3. Loop de execução do agente
def executar_agente(pergunta: str, max_iteracoes: int = 5) -> str:
    """Executa o agente até obter resposta final."""
    mensagens = [HumanMessage(content=pergunta)]

    for _ in range(max_iteracoes):
        resposta = modelo_com_tools.invoke(mensagens)
        mensagens.append(resposta)

        # Se não há tool calls, retorna a resposta
        if not resposta.tool_calls:
            return resposta.content

        # Executa cada tool call
        for tool_call in resposta.tool_calls:
            # Encontra a ferramenta
            ferramenta = next(
                (t for t in tools if t.name == tool_call["name"]),
                None
            )

            if ferramenta:
                resultado = ferramenta.invoke(tool_call["args"])
                mensagens.append(ToolMessage(
                    content=str(resultado),
                    tool_call_id=tool_call["id"]
                ))

    return "Máximo de iterações atingido"

# 4. Usar o agente
print(executar_agente("Quanto é 15% de 250?"))
print(executar_agente("Que horas são?"))
print(executar_agente("Qual o endereço do CEP 01310-100?"))
```

## Agente com LangGraph

```python
from typing import Annotated, TypedDict
from langchain_maritaca import ChatMaritaca
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

# Definir estado
class EstadoAgente(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# Ferramentas
@tool
def pesquisar_web(query: str) -> str:
    """Pesquisa informações na web."""
    # Simula pesquisa
    return f"Resultados para '{query}': informação relevante encontrada."

@tool
def enviar_email(destinatario: str, assunto: str, corpo: str) -> str:
    """Envia um email."""
    # Simula envio
    return f"Email enviado para {destinatario} com assunto '{assunto}'"

tools = [pesquisar_web, enviar_email]
tools_dict = {t.name: t for t in tools}

# Modelo
modelo = ChatMaritaca().bind_tools(tools)

# Nós do grafo
def chamar_modelo(estado: EstadoAgente) -> dict:
    """Chama o modelo."""
    resposta = modelo.invoke(estado["messages"])
    return {"messages": [resposta]}

def executar_tools(estado: EstadoAgente) -> dict:
    """Executa as ferramentas chamadas."""
    ultima_mensagem = estado["messages"][-1]
    resultados = []

    for tool_call in ultima_mensagem.tool_calls:
        ferramenta = tools_dict[tool_call["name"]]
        resultado = ferramenta.invoke(tool_call["args"])
        resultados.append(ToolMessage(
            content=str(resultado),
            tool_call_id=tool_call["id"]
        ))

    return {"messages": resultados}

def deve_continuar(estado: EstadoAgente) -> str:
    """Decide se continua ou termina."""
    ultima_mensagem = estado["messages"][-1]
    if ultima_mensagem.tool_calls:
        return "tools"
    return END

# Construir grafo
grafo = StateGraph(EstadoAgente)
grafo.add_node("modelo", chamar_modelo)
grafo.add_node("tools", executar_tools)

grafo.set_entry_point("modelo")
grafo.add_conditional_edges("modelo", deve_continuar, {
    "tools": "tools",
    END: END
})
grafo.add_edge("tools", "modelo")

# Compilar
agente = grafo.compile()

# Usar
resultado = agente.invoke({
    "messages": [HumanMessage(content="Pesquise sobre Maritaca AI")]
})
print(resultado["messages"][-1].content)
```

## Agente ReAct Manual

```python
from langchain_maritaca import ChatMaritaca
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool

@tool
def wikipedia(query: str) -> str:
    """Busca informações na Wikipedia."""
    # Simplificado para exemplo
    return f"Informação da Wikipedia sobre {query}: conteúdo relevante."

@tool
def calculadora(expressao: str) -> str:
    """Executa cálculos matemáticos."""
    return str(eval(expressao))

tools = [wikipedia, calculadora]
modelo = ChatMaritaca().bind_tools(tools)

SYSTEM_PROMPT = """Você é um assistente que pode usar ferramentas para responder perguntas.

Siga este processo:
1. Pense sobre a pergunta
2. Se precisar de informações externas, use as ferramentas
3. Analise os resultados
4. Forneça uma resposta completa

Seja conciso e preciso."""

def agente_react(pergunta: str) -> str:
    mensagens = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=pergunta)
    ]

    while True:
        resposta = modelo.invoke(mensagens)
        mensagens.append(resposta)

        if not resposta.tool_calls:
            return resposta.content

        for tool_call in resposta.tool_calls:
            ferramenta = next(t for t in tools if t.name == tool_call["name"])
            resultado = ferramenta.invoke(tool_call["args"])
            mensagens.append(ToolMessage(
                content=resultado,
                tool_call_id=tool_call["id"]
            ))

# Usar
resposta = agente_react("Quem foi Santos Dumont e em que ano ele nasceu?")
print(resposta)
```

## Agente com Memória

```python
from langchain_maritaca import ChatMaritaca
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool

@tool
def lembrar(informacao: str) -> str:
    """Salva uma informação importante."""
    return f"Informação salva: {informacao}"

@tool
def consultar_memoria(topico: str) -> str:
    """Consulta informações salvas sobre um tópico."""
    # Em produção, use um banco de dados real
    return f"Memória sobre {topico}: nenhuma informação encontrada."

tools = [lembrar, consultar_memoria]
modelo = ChatMaritaca().bind_tools(tools)

class AgenteComMemoria:
    def __init__(self):
        self.historico = []
        self.memoria = {}

    def processar(self, entrada: str) -> str:
        mensagens = [
            SystemMessage(content="Você é um assistente com memória persistente."),
            *self.historico,
            HumanMessage(content=entrada)
        ]

        while True:
            resposta = modelo.invoke(mensagens)

            if not resposta.tool_calls:
                self.historico.append(HumanMessage(content=entrada))
                self.historico.append(resposta)
                return resposta.content

            mensagens.append(resposta)

            for tool_call in resposta.tool_calls:
                if tool_call["name"] == "lembrar":
                    info = tool_call["args"]["informacao"]
                    self.memoria[info[:20]] = info
                    resultado = "Informação salva com sucesso."
                elif tool_call["name"] == "consultar_memoria":
                    topico = tool_call["args"]["topico"]
                    resultado = str(self.memoria) if self.memoria else "Memória vazia."

                mensagens.append(ToolMessage(
                    content=resultado,
                    tool_call_id=tool_call["id"]
                ))

# Usar
agente = AgenteComMemoria()
print(agente.processar("Lembre que meu nome é João"))
print(agente.processar("Qual é o meu nome?"))
```

## Boas Práticas

### 1. Tratamento de Erros

```python
def executar_ferramenta_seguro(ferramenta, args):
    """Executa ferramenta com tratamento de erros."""
    try:
        return ferramenta.invoke(args)
    except Exception as e:
        return f"Erro ao executar {ferramenta.name}: {str(e)}"
```

### 2. Timeout para Ferramentas

```python
import asyncio

async def executar_com_timeout(ferramenta, args, timeout=30):
    """Executa ferramenta com timeout."""
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(ferramenta.invoke, args),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        return f"Timeout ao executar {ferramenta.name}"
```

### 3. Logging de Ações

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def executar_com_log(ferramenta, args, tool_call_id):
    """Executa ferramenta com logging."""
    logger.info(f"Executando {ferramenta.name} com args: {args}")
    resultado = ferramenta.invoke(args)
    logger.info(f"Resultado de {ferramenta.name}: {resultado[:100]}...")
    return resultado
```

## Próximos Passos

- [Chamada de Ferramentas](../guide/tool-calling.md) - Detalhes sobre function calling
- [Pipeline RAG](rag.md) - Combine agentes com busca de documentos
