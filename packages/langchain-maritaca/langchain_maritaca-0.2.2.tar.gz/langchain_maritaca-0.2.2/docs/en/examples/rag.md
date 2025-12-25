# RAG Pipeline

Retrieval-Augmented Generation (RAG) combines document retrieval with text generation for more accurate and up-to-date responses.

!!! note "Dependencies"
    This example requires additional dependencies:
    ```bash
    pip install langchain langchain-community faiss-cpu
    ```

## Basic Example

```python
from langchain_maritaca import ChatMaritaca
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# 1. Sample documents
documents = [
    "Maritaca AI is a Brazilian artificial intelligence company.",
    "The Sabia-3.1 model is optimized for Brazilian Portuguese.",
    "langchain-maritaca is the official integration with LangChain.",
    "Maritaca AI was founded to democratize AI in Brazil.",
    "The Sabiazinho-3.1 model is faster and more economical.",
]

# 2. Create embeddings and vector store
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
vectorstore = FAISS.from_texts(documents, embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# 3. Configure model
model = ChatMaritaca()

# 4. Prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an assistant that answers questions based on the provided context.
Use only the information from the context to answer.
If you don't know the answer, say you don't have that information.

Context:
{context}"""),
    ("human", "{question}")
])

# 5. Function to format documents
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# 6. Create RAG chain
chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | model
    | StrOutputParser()
)

# 7. Use
response = chain.invoke("What is Maritaca AI?")
print(response)
```

## RAG with PDF Documents

```python
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Load PDF
loader = PyPDFLoader("document.pdf")
pages = loader.load()

# Split into chunks
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)
chunks = splitter.split_documents(pages)

# Create vector store
vectorstore = FAISS.from_documents(chunks, embeddings)
```

## RAG with Conversation History

```python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an assistant that answers questions based on the context.

Context:
{context}"""),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}")
])

history = []

def chat_rag(question: str) -> str:
    # Retrieve documents
    docs = retriever.invoke(question)
    context = format_docs(docs)

    # Generate response
    response = model.invoke(
        prompt.format_messages(
            context=context,
            history=history,
            question=question
        )
    )

    # Update history
    history.append(HumanMessage(content=question))
    history.append(AIMessage(content=response.content))

    return response.content

# Conversation
print(chat_rag("What is Maritaca AI?"))
print(chat_rag("And what models does it offer?"))
```

## RAG with Sources

```python
from langchain_core.runnables import RunnableParallel

# Chain that returns response and sources
chain_with_sources = RunnableParallel({
    "response": chain,
    "sources": retriever
})

result = chain_with_sources.invoke("What is Sabia?")
print(f"Response: {result['response']}")
print(f"\nSources:")
for doc in result['sources']:
    print(f"- {doc.page_content[:100]}...")
```

## Advanced RAG with Reranking

```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain_community.document_compressors import CohereRerank

# Add reranking to results
compressor = CohereRerank(top_n=3)
retriever_with_rerank = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=vectorstore.as_retriever(search_kwargs={"k": 10})
)

advanced_chain = (
    {"context": retriever_with_rerank | format_docs, "question": RunnablePassthrough()}
    | prompt
    | model
    | StrOutputParser()
)
```

## Performance Tips

1. **Chunk size**: Adjust based on document type
2. **Overlap**: 10-20% of chunk size
3. **Top-K**: Start with 3-5 documents
4. **Embeddings**: Use multilingual models for Portuguese

## Next Steps

- [Agent with Tools](agent.md) - Combine RAG with actions
- [Tool Calling](../guide/tool-calling.md) - Function calling
