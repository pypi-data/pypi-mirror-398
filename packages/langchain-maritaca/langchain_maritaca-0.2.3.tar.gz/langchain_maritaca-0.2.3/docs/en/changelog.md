# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-12-18

### Added

- **Tool Calling / Function Calling**: Full support for binding tools to the model
  - `bind_tools()` method to bind Pydantic models, functions, or tool schemas
  - `tool_choice` parameter to control tool selection ("auto", "required", or specific tool)
  - Support for `ToolMessage` for tool call responses
  - Full support for conversation loop with tool execution
- **Message Conversion**: Extended to handle tool-related messages
  - `AIMessage` with `tool_calls` attribute
  - `ToolMessage` for returning tool execution results
- **Planning Documentation**: Added `docs/planning/future-improvements.md` with roadmap

### Changed

- Improved `_convert_message_to_dict()` to support tool calls in AIMessage
- Improved `_convert_dict_to_message()` to parse tool calls from API response
- Updated `_default_params` to include `tools` and `tool_choice` when configured

## [0.1.1] - 2025-12-15

### Changed

- Updated default model from `sabia-3` to `sabia-3.1`
- Updated model references to use `sabia-3.1` and `sabiazinho-3.1`
- Sabia 3.0 models have been deprecated by Maritaca AI

## [0.1.0] - 2025-12-15

### Added

- Initial release of `langchain-maritaca`
- `ChatMaritaca` class for interacting with Maritaca AI models
- Support for `sabia-3.1` and `sabiazinho-3.1` models
- Synchronous and asynchronous generation
- Streaming support (sync and async)
- Automatic retry logic with exponential backoff
- Rate limiting handling
- LangSmith integration for tracing
- Usage metadata tracking
- Complete type hints and documentation
- Comprehensive test suite

### Features

- **Chat Completions**: Full support for chat-based interactions
- **Streaming**: Real-time token streaming for better UX
- **Async Support**: Native async/await support
- **Retry Logic**: Automatic retries with configurable backoff
- **Rate Limiting**: Graceful handling of API rate limits
- **Tracing**: Built-in LangSmith integration for observability
