# Integração LCEL

O LangChain Expression Language (LCEL) permite compor chains de forma declarativa com o ChatMaritaca.

## Conceitos Básicos

LCEL usa o operador `|` para encadear componentes:

```python
from langchain_maritaca import ChatMaritaca
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Componentes
prompt = ChatPromptTemplate.from_messages([
    ("system", "Você é um assistente especializado em {tema}."),
    ("human", "{pergunta}")
])

modelo = ChatMaritaca()
parser = StrOutputParser()

# Chain com LCEL
chain = prompt | modelo | parser

# Execução
resultado = chain.invoke({
    "tema": "história do Brasil",
    "pergunta": "Quem proclamou a República?"
})

print(resultado)
```

## Prompt Templates

### ChatPromptTemplate

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "Você é um tradutor de {origem} para {destino}."),
    ("human", "Traduza: {texto}")
])

chain = prompt | ChatMaritaca() | StrOutputParser()

resultado = chain.invoke({
    "origem": "português",
    "destino": "inglês",
    "texto": "Olá, mundo!"
})
```

### MessagesPlaceholder

```python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

prompt = ChatPromptTemplate.from_messages([
    ("system", "Você é um assistente prestativo."),
    MessagesPlaceholder(variable_name="historico"),
    ("human", "{pergunta}")
])

chain = prompt | ChatMaritaca() | StrOutputParser()

resultado = chain.invoke({
    "historico": [
        HumanMessage(content="Meu nome é João."),
        AIMessage(content="Olá João!")
    ],
    "pergunta": "Qual é o meu nome?"
})
```

## Output Parsers

### StrOutputParser

Extrai apenas o texto da resposta:

```python
from langchain_core.output_parsers import StrOutputParser

chain = prompt | modelo | StrOutputParser()
resultado = chain.invoke({"pergunta": "Olá!"})
# resultado é uma string
```

### JsonOutputParser

Parseia JSON da resposta:

```python
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel

class Pessoa(BaseModel):
    nome: str
    idade: int

parser = JsonOutputParser(pydantic_object=Pessoa)

prompt = ChatPromptTemplate.from_messages([
    ("system", "Extraia informações no formato JSON: {format_instructions}"),
    ("human", "{texto}")
])

chain = prompt | modelo | parser

resultado = chain.invoke({
    "texto": "João tem 25 anos.",
    "format_instructions": parser.get_format_instructions()
})
# resultado: {'nome': 'João', 'idade': 25}
```

## Streaming com LCEL

```python
chain = prompt | modelo | StrOutputParser()

for chunk in chain.stream({"pergunta": "Conte uma história."}):
    print(chunk, end="", flush=True)
```

## Async com LCEL

```python
import asyncio

async def main():
    chain = prompt | modelo | StrOutputParser()

    resultado = await chain.ainvoke({"pergunta": "O que é Python?"})
    print(resultado)

asyncio.run(main())
```

## Batch com LCEL

```python
chain = prompt | modelo | StrOutputParser()

resultados = chain.batch([
    {"pergunta": "O que é Python?"},
    {"pergunta": "O que é Java?"},
    {"pergunta": "O que é Go?"},
])

for r in resultados:
    print(f"- {r[:50]}...")
```

## RunnablePassthrough

Passa dados através da chain:

```python
from langchain_core.runnables import RunnablePassthrough

chain = (
    {"pergunta": RunnablePassthrough()}
    | prompt
    | modelo
    | StrOutputParser()
)

resultado = chain.invoke("O que é IA?")
```

## RunnableParallel

Executa múltiplas chains em paralelo:

```python
from langchain_core.runnables import RunnableParallel

chain1 = prompt1 | modelo | StrOutputParser()
chain2 = prompt2 | modelo | StrOutputParser()

parallel = RunnableParallel({
    "resumo": chain1,
    "traducao": chain2
})

resultado = parallel.invoke({"texto": "..."})
# resultado: {'resumo': '...', 'traducao': '...'}
```

## Com Ferramentas (Tools)

```python
from pydantic import BaseModel, Field

class Calculadora(BaseModel):
    """Realiza cálculos."""
    expressao: str = Field(description="Expressão matemática")

modelo_com_tools = ChatMaritaca().bind_tools([Calculadora])

chain = prompt | modelo_com_tools

resultado = chain.invoke({"pergunta": "Quanto é 10 + 5?"})
# resultado.tool_calls contém a chamada da ferramenta
```

## Exemplo Completo: Chatbot com Memória

```python
from langchain_maritaca import ChatMaritaca
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage

# Setup
prompt = ChatPromptTemplate.from_messages([
    ("system", "Você é um assistente prestativo chamado Sabiá."),
    MessagesPlaceholder(variable_name="historico"),
    ("human", "{entrada}")
])

chain = prompt | ChatMaritaca() | StrOutputParser()

# Gerencia histórico
historico = []

def chat(entrada_usuario: str) -> str:
    resposta = chain.invoke({
        "historico": historico,
        "entrada": entrada_usuario
    })

    # Atualiza histórico
    historico.append(HumanMessage(content=entrada_usuario))
    historico.append(AIMessage(content=resposta))

    return resposta

# Conversa
print(chat("Olá! Qual é o seu nome?"))
print(chat("O que você pode fazer?"))
print(chat("Qual foi minha primeira pergunta?"))
```

## Próximos Passos

- [Referência da API](../api/chat-maritaca.md) - Documentação completa
- [Exemplos](../examples/chatbot.md) - Mais exemplos práticos
