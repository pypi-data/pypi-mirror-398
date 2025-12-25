# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [0.2.0] - 2025-12-18

### Adicionado

- **Chamada de Ferramentas / Function Calling**: Suporte completo para vincular ferramentas ao modelo
  - Método `bind_tools()` para vincular modelos Pydantic, funções ou schemas de ferramentas
  - Parâmetro `tool_choice` para controlar seleção de ferramenta ("auto", "required", ou ferramenta específica)
  - Suporte a `ToolMessage` para respostas de chamadas de ferramentas
  - Suporte completo ao loop de conversa com execução de ferramentas
- **Conversão de Mensagens**: Estendida para lidar com mensagens relacionadas a ferramentas
  - `AIMessage` com atributo `tool_calls`
  - `ToolMessage` para retornar resultados de execução de ferramentas
- **Documentação de Planejamento**: Adicionado `docs/planning/future-improvements.md` com roadmap

### Alterado

- Melhorado `_convert_message_to_dict()` para suportar tool calls em AIMessage
- Melhorado `_convert_dict_to_message()` para parsear tool calls da resposta da API
- Atualizado `_default_params` para incluir `tools` e `tool_choice` quando configurados

## [0.1.1] - 2025-12-15

### Alterado

- Atualizado modelo padrão de `sabia-3` para `sabia-3.1`
- Atualizadas referências de modelo para usar `sabia-3.1` e `sabiazinho-3.1`
- Modelos Sabiá 3.0 foram descontinuados pela Maritaca AI

## [0.1.0] - 2025-12-15

### Adicionado

- Lançamento inicial do `langchain-maritaca`
- Classe `ChatMaritaca` para interação com modelos da Maritaca AI
- Suporte para modelos `sabia-3.1` e `sabiazinho-3.1`
- Geração síncrona e assíncrona
- Suporte a streaming (sync e async)
- Lógica de retry automático com backoff exponencial
- Tratamento de rate limiting
- Integração com LangSmith para tracing
- Rastreamento de metadados de uso
- Type hints completos e documentação
- Suite de testes abrangente

### Funcionalidades

- **Chat Completions**: Suporte completo para interações baseadas em chat
- **Streaming**: Streaming de tokens em tempo real para melhor UX
- **Suporte Async**: Suporte nativo a async/await
- **Lógica de Retry**: Retentativas automáticas com backoff configurável
- **Rate Limiting**: Tratamento gracioso de limites de taxa da API
- **Tracing**: Integração LangSmith integrada para observabilidade
