# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.2] - 2025-12-22

### Added

- **Structured Output**: `with_structured_output()` method for ChatMaritaca
  - Returns Pydantic models or dicts directly from LLM responses
  - Supports `function_calling` (default) and `json_mode` methods
  - `include_raw` option to return raw response alongside parsed output
- **Embeddings Support**: `DeepInfraEmbeddings` class for RAG workflows
  - Uses `intfloat/multilingual-e5-large` model (recommended by Maritaca AI)
  - 1024-dimensional embeddings, supports 100 languages including Portuguese
  - Sync and async methods: `embed_query`, `embed_documents`, `aembed_query`, `aembed_documents`
  - Automatic batching with configurable `batch_size`

## [0.2.1] - 2025-12-21

### Fixed

- Fix PyPI metadata: author name and email now correctly displayed

## [0.2.0] - 2025-12-18

### Added

- **Tool Calling / Function Calling**: Full support for binding tools to the model
  - `bind_tools()` method for binding Pydantic models, functions, or tool schemas
  - `tool_choice` parameter to control tool selection ("auto", "required", or specific tool)
  - `ToolMessage` support for tool call responses
  - Full conversation loop support with tool execution
- **Message Conversion**: Extended to handle tool-related messages
  - `AIMessage` with `tool_calls` attribute
  - `ToolMessage` for returning tool execution results
- **Planning Documentation**: Added `docs/planning/future-improvements.md` roadmap

### Changed

- Enhanced `_convert_message_to_dict()` to support tool calls in AIMessage
- Enhanced `_convert_dict_to_message()` to parse tool calls from API response
- Updated `_default_params` to include `tools` and `tool_choice` when configured

## [0.1.1] - 2025-12-15

### Changed

- Update default model from `sabia-3` to `sabia-3.1`
- Update model references to use `sabia-3.1` and `sabiazinho-3.1`
- Sabiá 3.0 models have been discontinued by Maritaca AI

## [0.1.0] - 2025-12-15

### Added

- Initial release of `langchain-maritaca`
- `ChatMaritaca` class for interacting with Maritaca AI models
- Support for `sabia-3.1` and `sabiazinho-3.1` models
- Synchronous and asynchronous generation
- Streaming support (sync and async)
- Automatic retry logic with exponential backoff
- Rate limiting handling
- LangSmith tracing integration
- Usage metadata tracking
- Full type hints and documentation
- Comprehensive test suite

### Features

- **Chat Completions**: Full support for chat-based interactions
- **Streaming**: Real-time token streaming for better UX
- **Async Support**: Native async/await support
- **Retry Logic**: Automatic retries with configurable backoff
- **Rate Limiting**: Graceful handling of API rate limits
- **Tracing**: Built-in LangSmith integration for observability

[Unreleased]: https://github.com/anderson-ufrj/langchain-maritaca/compare/v0.2.2...HEAD
[0.2.2]: https://github.com/anderson-ufrj/langchain-maritaca/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/anderson-ufrj/langchain-maritaca/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/anderson-ufrj/langchain-maritaca/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/anderson-ufrj/langchain-maritaca/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/anderson-ufrj/langchain-maritaca/releases/tag/v0.1.0
