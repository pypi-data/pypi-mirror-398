# langchain-maritaca

<p align="center">
  <strong>Integração LangChain para Maritaca AI - Modelos de linguagem otimizados para Português Brasileiro</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/langchain-maritaca/">
    <img src="https://img.shields.io/pypi/v/langchain-maritaca.svg" alt="Versão PyPI">
  </a>
  <a href="https://pypi.org/project/langchain-maritaca/">
    <img src="https://img.shields.io/pypi/pyversions/langchain-maritaca.svg" alt="Versões Python">
  </a>
  <a href="https://github.com/anderson-ufrj/langchain-maritaca/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/anderson-ufrj/langchain-maritaca.svg" alt="Licença">
  </a>
</p>

---

## O que é langchain-maritaca?

**langchain-maritaca** é a integração oficial do LangChain para a [Maritaca AI](https://www.maritaca.ai/), fornecendo acesso aos modelos de linguagem otimizados para Português Brasileiro, como o **Sabiá-3.1**.

Os modelos da Maritaca AI são treinados especificamente com dados em Português Brasileiro, oferecendo desempenho superior para geração, análise e compreensão de textos em português comparado a modelos multilíngues genéricos.

## Principais Funcionalidades

<div class="grid cards" markdown>

-   :material-chat-processing:{ .lg .middle } **Chat Completions**

    ---

    Suporte completo para interações baseadas em chat com mensagens de sistema, usuário e assistente.

-   :material-function:{ .lg .middle } **Chamada de Ferramentas**

    ---

    Vincule funções Python, modelos Pydantic ou ferramentas customizadas para function calling.

-   :material-lightning-bolt:{ .lg .middle } **Streaming**

    ---

    Streaming de tokens em tempo real para melhor experiência em aplicações interativas.

-   :material-sync:{ .lg .middle } **Suporte Async**

    ---

    Suporte nativo a async/await para aplicações de alta concorrência.

-   :material-refresh:{ .lg .middle } **Lógica de Retry**

    ---

    Retentativas automáticas com backoff exponencial e tratamento de rate limit.

-   :material-chart-line:{ .lg .middle } **Integração LangSmith**

    ---

    Tracing e observabilidade integrados com LangSmith.

</div>

## Exemplo Rápido

```python
from langchain_maritaca import ChatMaritaca
from langchain_core.messages import HumanMessage

# Inicializa o modelo
modelo = ChatMaritaca(
    model="sabia-3.1",
    temperature=0.7,
)

# Invocação simples
resposta = modelo.invoke([
    HumanMessage(content="Qual é a capital do Brasil?")
])

print(resposta.content)
# Saída: A capital do Brasil é Brasília.
```

## Modelos Disponíveis

| Modelo | Descrição | Melhor Para |
|--------|-----------|-------------|
| `sabia-3.1` | Modelo mais capaz | Tarefas complexas, análise, geração |
| `sabiazinho-3.1` | Rápido e econômico | Tarefas simples, operações de alto volume |

## Pronto para Produção

langchain-maritaca é usado em produção por:

- **[Cidadão.AI](https://cidadao-ai-frontend.vercel.app/)** - Plataforma brasileira de transparência governamental alimentada por agentes de IA, processando mais de 331 mil requisições mensais.

## Próximos Passos

<div class="grid cards" markdown>

-   :material-download:{ .lg .middle } **[Instalação](getting-started/installation.md)**

    ---

    Comece com pip install

-   :material-rocket-launch:{ .lg .middle } **[Início Rápido](getting-started/quickstart.md)**

    ---

    Sua primeira resposta em 5 minutos

-   :material-tools:{ .lg .middle } **[Chamada de Ferramentas](guide/tool-calling.md)**

    ---

    Aprenda a usar function calling

-   :material-api:{ .lg .middle } **[Referência da API](api/chat-maritaca.md)**

    ---

    Documentação completa da API

</div>
