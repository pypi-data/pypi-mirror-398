# Pipeline RAG

Retrieval-Augmented Generation (RAG) combina busca de documentos com geração de texto para respostas mais precisas e atualizadas.

!!! note "Dependências"
    Este exemplo requer dependências adicionais:
    ```bash
    pip install langchain langchain-community faiss-cpu
    ```

## Exemplo Básico

```python
from langchain_maritaca import ChatMaritaca
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# 1. Documentos de exemplo
documentos = [
    "A Maritaca AI é uma empresa brasileira de inteligência artificial.",
    "O modelo Sabiá-3.1 é otimizado para português brasileiro.",
    "O langchain-maritaca é a integração oficial com LangChain.",
    "A Maritaca AI foi fundada para democratizar a IA no Brasil.",
    "O modelo Sabiazinho-3.1 é mais rápido e econômico.",
]

# 2. Criar embeddings e vector store
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
vectorstore = FAISS.from_texts(documentos, embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# 3. Configurar modelo
modelo = ChatMaritaca()

# 4. Prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", """Você é um assistente que responde perguntas com base no contexto fornecido.
Use apenas as informações do contexto para responder.
Se não souber a resposta, diga que não tem essa informação.

Contexto:
{contexto}"""),
    ("human", "{pergunta}")
])

# 5. Função para formatar documentos
def formatar_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# 6. Criar chain RAG
chain = (
    {"contexto": retriever | formatar_docs, "pergunta": RunnablePassthrough()}
    | prompt
    | modelo
    | StrOutputParser()
)

# 7. Usar
resposta = chain.invoke("O que é a Maritaca AI?")
print(resposta)
```

## RAG com Documentos PDF

```python
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Carregar PDF
loader = PyPDFLoader("documento.pdf")
paginas = loader.load()

# Dividir em chunks
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)
chunks = splitter.split_documents(paginas)

# Criar vector store
vectorstore = FAISS.from_documents(chunks, embeddings)
```

## RAG com Histórico de Conversa

```python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

prompt = ChatPromptTemplate.from_messages([
    ("system", """Você é um assistente que responde perguntas com base no contexto.

Contexto:
{contexto}"""),
    MessagesPlaceholder(variable_name="historico"),
    ("human", "{pergunta}")
])

historico = []

def chat_rag(pergunta: str) -> str:
    # Busca documentos
    docs = retriever.invoke(pergunta)
    contexto = formatar_docs(docs)

    # Gera resposta
    resposta = modelo.invoke(
        prompt.format_messages(
            contexto=contexto,
            historico=historico,
            pergunta=pergunta
        )
    )

    # Atualiza histórico
    historico.append(HumanMessage(content=pergunta))
    historico.append(AIMessage(content=resposta.content))

    return resposta.content

# Conversa
print(chat_rag("O que é Maritaca AI?"))
print(chat_rag("E quais modelos ela oferece?"))
```

## RAG com Fontes

```python
from langchain_core.runnables import RunnableParallel

# Chain que retorna resposta e fontes
chain_com_fontes = RunnableParallel({
    "resposta": chain,
    "fontes": retriever
})

resultado = chain_com_fontes.invoke("O que é o Sabiá?")
print(f"Resposta: {resultado['resposta']}")
print(f"\nFontes:")
for doc in resultado['fontes']:
    print(f"- {doc.page_content[:100]}...")
```

## RAG Avançado com Reranking

```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain_community.document_compressors import CohereRerank

# Adiciona reranking aos resultados
compressor = CohereRerank(top_n=3)
retriever_com_rerank = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=vectorstore.as_retriever(search_kwargs={"k": 10})
)

chain_avancado = (
    {"contexto": retriever_com_rerank | formatar_docs, "pergunta": RunnablePassthrough()}
    | prompt
    | modelo
    | StrOutputParser()
)
```

## Dicas de Performance

1. **Chunk size**: Ajuste baseado no tipo de documento
2. **Overlap**: 10-20% do chunk size
3. **Top-K**: Comece com 3-5 documentos
4. **Embeddings**: Use modelos multilíngues para português

## Próximos Passos

- [Agente com Ferramentas](agent.md) - Combine RAG com ações
- [Chamada de Ferramentas](../guide/tool-calling.md) - Function calling
