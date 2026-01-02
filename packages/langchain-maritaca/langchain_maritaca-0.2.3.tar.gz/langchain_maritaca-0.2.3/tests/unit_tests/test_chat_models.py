"""Unit tests for ChatMaritaca.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
GitHub: https://github.com/anderson-ufrj
"""

import os
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from pydantic import BaseModel, Field

from langchain_maritaca import ChatMaritaca
from langchain_maritaca.chat_models import (
    _convert_dict_to_message,
    _convert_message_to_dict,
    _create_usage_metadata,
)

if "MARITACA_API_KEY" not in os.environ:
    os.environ["MARITACA_API_KEY"] = "fake-key"


class TestChatMaritaca:
    """Test suite for ChatMaritaca."""

    def test_initialization_default(self) -> None:
        """Test default initialization."""
        with patch.dict("os.environ", {"MARITACA_API_KEY": "test-key"}):
            model = ChatMaritaca()
            assert model.model_name == "sabia-3.1"
            assert model.temperature == 0.7
            assert model.max_retries == 2

    def test_initialization_with_params(self) -> None:
        """Test initialization with custom parameters."""
        model = ChatMaritaca(
            api_key="test-key",  # type: ignore[arg-type]
            model="sabiazinho-3.1",
            temperature=0.5,
            max_tokens=1000,
            max_retries=3,
        )
        assert model.model_name == "sabiazinho-3.1"
        assert model.temperature == 0.5
        assert model.max_tokens == 1000
        assert model.max_retries == 3

    def test_initialization_with_alias(self) -> None:
        """Test initialization using parameter aliases."""
        model = ChatMaritaca(
            api_key="test-key",  # type: ignore[arg-type]
            model="sabia-3.1",
            timeout=30.0,
            base_url="https://custom.api.com",
        )
        assert model.request_timeout == 30.0
        assert model.maritaca_api_base == "https://custom.api.com"

    def test_llm_type(self) -> None:
        """Test _llm_type property."""
        model = ChatMaritaca(api_key="test-key")  # type: ignore[arg-type]
        assert model._llm_type == "maritaca-chat"

    def test_is_lc_serializable(self) -> None:
        """Test is_lc_serializable class method."""
        assert ChatMaritaca.is_lc_serializable() is True

    def test_lc_secrets(self) -> None:
        """Test lc_secrets property."""
        model = ChatMaritaca(api_key="test-key")  # type: ignore[arg-type]
        assert model.lc_secrets == {"maritaca_api_key": "MARITACA_API_KEY"}

    def test_default_params(self) -> None:
        """Test _default_params property."""
        model = ChatMaritaca(
            api_key="test-key",  # type: ignore[arg-type]
            model="sabia-3.1",
            temperature=0.8,
            max_tokens=500,
            top_p=0.95,
        )
        params = model._default_params
        assert params["model"] == "sabia-3.1"
        assert params["temperature"] == 0.8
        assert params["max_tokens"] == 500
        assert params["top_p"] == 0.95

    def test_temperature_zero_adjustment(self) -> None:
        """Test that temperature=0 is adjusted to avoid API issues."""
        model = ChatMaritaca(api_key="test-key", temperature=0)  # type: ignore[arg-type]
        assert model.temperature == 1e-8

    def test_n_validation(self) -> None:
        """Test that n must be at least 1."""
        with pytest.raises(ValueError, match="n must be at least 1"):
            ChatMaritaca(api_key="test-key", n=0)  # type: ignore[arg-type]

    def test_streaming_n_validation(self) -> None:
        """Test that n must be 1 when streaming."""
        with pytest.raises(ValueError, match="n must be 1 when streaming"):
            ChatMaritaca(api_key="test-key", n=2, streaming=True)  # type: ignore[arg-type]


class TestMessageConversion:
    """Test message conversion functions."""

    def test_convert_human_message(self) -> None:
        """Test converting HumanMessage."""
        msg = HumanMessage(content="Hello")
        result = _convert_message_to_dict(msg)
        assert result == {"role": "user", "content": "Hello"}

    def test_convert_ai_message(self) -> None:
        """Test converting AIMessage."""
        msg = AIMessage(content="Hi there")
        result = _convert_message_to_dict(msg)
        assert result == {"role": "assistant", "content": "Hi there"}

    def test_convert_system_message(self) -> None:
        """Test converting SystemMessage."""
        msg = SystemMessage(content="You are helpful")
        result = _convert_message_to_dict(msg)
        assert result == {"role": "system", "content": "You are helpful"}

    def test_convert_dict_to_human_message(self) -> None:
        """Test converting dict to HumanMessage."""
        msg_dict = {"role": "user", "content": "Hello"}
        result = _convert_dict_to_message(msg_dict)
        assert isinstance(result, HumanMessage)
        assert result.content == "Hello"

    def test_convert_dict_to_ai_message(self) -> None:
        """Test converting dict to AIMessage."""
        msg_dict = {"role": "assistant", "content": "Hi there"}
        result = _convert_dict_to_message(msg_dict)
        assert isinstance(result, AIMessage)
        assert result.content == "Hi there"

    def test_convert_dict_to_system_message(self) -> None:
        """Test converting dict to SystemMessage."""
        msg_dict = {"role": "system", "content": "You are helpful"}
        result = _convert_dict_to_message(msg_dict)
        assert isinstance(result, SystemMessage)
        assert result.content == "You are helpful"


class TestUsageMetadata:
    """Test usage metadata creation."""

    def test_create_usage_metadata(self) -> None:
        """Test creating usage metadata from token usage."""
        token_usage = {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30,
        }
        result = _create_usage_metadata(token_usage)
        assert result["input_tokens"] == 10
        assert result["output_tokens"] == 20
        assert result["total_tokens"] == 30

    def test_create_usage_metadata_missing_total(self) -> None:
        """Test creating usage metadata when total is missing."""
        token_usage = {
            "prompt_tokens": 10,
            "completion_tokens": 20,
        }
        result = _create_usage_metadata(token_usage)
        assert result["total_tokens"] == 30


class TestChatMaritacaIntegration:
    """Integration-style unit tests using mocked HTTP responses."""

    @pytest.fixture
    def mock_response(self) -> dict[str, Any]:
        """Create a mock API response."""
        return {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "sabia-3.1",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "A capital do Brasil é Brasília.",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 15,
                "completion_tokens": 10,
                "total_tokens": 25,
            },
        }

    def test_invoke_with_mock(self, mock_response: dict[str, Any]) -> None:
        """Test invoke method with mocked HTTP client."""
        model = ChatMaritaca(api_key="test-key")  # type: ignore[arg-type]

        # Mock the HTTP client
        mock_http_response = MagicMock()
        mock_http_response.json.return_value = mock_response
        mock_http_response.raise_for_status = MagicMock()

        model.client = MagicMock()
        model.client.post.return_value = mock_http_response

        result = model.invoke([HumanMessage(content="Qual é a capital do Brasil?")])

        assert isinstance(result, AIMessage)
        assert result.content == "A capital do Brasil é Brasília."
        assert result.usage_metadata is not None
        assert result.usage_metadata["input_tokens"] == 15
        assert result.usage_metadata["output_tokens"] == 10

    def test_create_chat_result(self, mock_response: dict[str, Any]) -> None:
        """Test _create_chat_result method."""
        model = ChatMaritaca(api_key="test-key")  # type: ignore[arg-type]
        result = model._create_chat_result(mock_response)

        assert len(result.generations) == 1
        assert isinstance(result.generations[0].message, AIMessage)
        expected_content = "A capital do Brasil é Brasília."
        assert result.generations[0].message.content == expected_content
        assert result.llm_output is not None
        assert result.llm_output["model"] == "sabia-3.1"
        assert result.llm_output["token_usage"]["total_tokens"] == 25

    def test_create_message_dicts(self) -> None:
        """Test _create_message_dicts method."""
        model = ChatMaritaca(api_key="test-key")  # type: ignore[arg-type]
        messages = [
            SystemMessage(content="You are helpful"),
            HumanMessage(content="Hello"),
        ]

        message_dicts, params = model._create_message_dicts(messages, stop=["END"])

        assert len(message_dicts) == 2
        assert message_dicts[0] == {"role": "system", "content": "You are helpful"}
        assert message_dicts[1] == {"role": "user", "content": "Hello"}
        assert params["stop"] == ["END"]


class TestChatMaritacaLangSmith:
    """Test LangSmith integration."""

    def test_get_ls_params(self) -> None:
        """Test _get_ls_params method."""
        model = ChatMaritaca(
            api_key="test-key",  # type: ignore[arg-type]
            model="sabia-3.1",
            temperature=0.5,
            max_tokens=100,
        )

        ls_params = model._get_ls_params(stop=["END"])

        assert ls_params["ls_provider"] == "maritaca"
        assert ls_params["ls_model_name"] == "sabia-3.1"
        assert ls_params["ls_model_type"] == "chat"
        assert ls_params["ls_temperature"] == 0.5
        assert ls_params["ls_max_tokens"] == 100
        assert ls_params["ls_stop"] == ["END"]


class TestToolCalling:
    """Test tool calling functionality."""

    def test_bind_tools_with_pydantic_model(self) -> None:
        """Test bind_tools with a Pydantic model."""

        class GetWeather(BaseModel):
            """Get weather for a location."""

            location: str = Field(description="City name")

        model = ChatMaritaca(api_key="test-key")  # type: ignore[arg-type]
        model_with_tools = model.bind_tools([GetWeather])

        # Verify the tools are bound
        assert model_with_tools is not None

    def test_bind_tools_with_function(self) -> None:
        """Test bind_tools with a Python function."""

        def get_weather(location: str) -> str:
            """Get weather for a location.

            Args:
                location: City name
            """
            return f"Weather in {location}"

        model = ChatMaritaca(api_key="test-key")  # type: ignore[arg-type]
        model_with_tools = model.bind_tools([get_weather])

        assert model_with_tools is not None

    def test_bind_tools_with_tool_choice(self) -> None:
        """Test bind_tools with tool_choice parameter."""

        class GetWeather(BaseModel):
            """Get weather for a location."""

            location: str = Field(description="City name")

        model = ChatMaritaca(api_key="test-key")  # type: ignore[arg-type]
        model_with_tools = model.bind_tools([GetWeather], tool_choice="required")

        assert model_with_tools is not None

    def test_convert_tool_message_to_dict(self) -> None:
        """Test converting ToolMessage to dict."""
        msg = ToolMessage(content="Weather is sunny", tool_call_id="call_123")
        result = _convert_message_to_dict(msg)

        assert result["role"] == "tool"
        assert result["content"] == "Weather is sunny"
        assert result["tool_call_id"] == "call_123"

    def test_convert_ai_message_with_tool_calls(self) -> None:
        """Test converting AIMessage with tool_calls."""
        msg = AIMessage(
            content="",
            tool_calls=[
                {
                    "id": "call_123",
                    "name": "get_weather",
                    "args": {"location": "São Paulo"},
                }
            ],
        )
        result = _convert_message_to_dict(msg)

        assert result["role"] == "assistant"
        assert result["content"] == ""
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["id"] == "call_123"
        assert result["tool_calls"][0]["type"] == "function"
        assert result["tool_calls"][0]["function"]["name"] == "get_weather"
        assert (
            '"location": "S\\u00e3o Paulo"'
            in result["tool_calls"][0]["function"]["arguments"]
        )

    def test_convert_dict_with_tool_calls_to_ai_message(self) -> None:
        """Test converting dict with tool_calls to AIMessage."""
        msg_dict = {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_456",
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "arguments": '{"location": "Rio de Janeiro"}',
                    },
                }
            ],
        }
        result = _convert_dict_to_message(msg_dict)

        assert isinstance(result, AIMessage)
        assert result.content == ""
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0]["id"] == "call_456"
        assert result.tool_calls[0]["name"] == "get_weather"
        assert result.tool_calls[0]["args"] == {"location": "Rio de Janeiro"}

    def test_convert_dict_to_tool_message(self) -> None:
        """Test converting dict to ToolMessage."""
        msg_dict = {
            "role": "tool",
            "content": "The weather is sunny",
            "tool_call_id": "call_789",
        }
        result = _convert_dict_to_message(msg_dict)

        assert isinstance(result, ToolMessage)
        assert result.content == "The weather is sunny"
        assert result.tool_call_id == "call_789"

    def test_create_chat_result_with_tool_calls(self) -> None:
        """Test _create_chat_result with tool calls in response."""
        model = ChatMaritaca(api_key="test-key")  # type: ignore[arg-type]
        response = {
            "id": "chatcmpl-123",
            "model": "sabia-3.1",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call_abc",
                                "type": "function",
                                "function": {
                                    "name": "get_weather",
                                    "arguments": '{"location": "Belo Horizonte"}',
                                },
                            }
                        ],
                    },
                    "finish_reason": "tool_calls",
                }
            ],
            "usage": {"prompt_tokens": 20, "completion_tokens": 15, "total_tokens": 35},
        }

        result = model._create_chat_result(response)

        assert len(result.generations) == 1
        message = result.generations[0].message
        assert isinstance(message, AIMessage)
        assert len(message.tool_calls) == 1
        assert message.tool_calls[0]["name"] == "get_weather"
        assert message.tool_calls[0]["args"] == {"location": "Belo Horizonte"}
        assert result.generations[0].generation_info["finish_reason"] == "tool_calls"

    def test_default_params_with_tools(self) -> None:
        """Test _default_params includes tools when set."""
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "test_func",
                    "description": "A test function",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]
        model = ChatMaritaca(
            api_key="test-key",  # type: ignore[arg-type]
            tools=tools,
            tool_choice="auto",
        )
        params = model._default_params

        assert params["tools"] == tools
        assert params["tool_choice"] == "auto"


class TestStructuredOutput:
    """Test structured output functionality."""

    def test_with_structured_output_pydantic_function_calling(self) -> None:
        """Test with_structured_output with Pydantic model using function_calling."""

        class Person(BaseModel):
            """Information about a person."""

            name: str = Field(description="Person's name")
            age: int = Field(description="Person's age")

        model = ChatMaritaca(api_key="test-key")  # type: ignore[arg-type]
        structured_model = model.with_structured_output(Person)

        # Verify a runnable is returned
        assert structured_model is not None
        # Verify it's a chain (llm | parser)
        assert hasattr(structured_model, "invoke")

    def test_with_structured_output_dict_schema(self) -> None:
        """Test with_structured_output with dict schema."""
        schema = {
            "title": "Person",
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
            "required": ["name", "age"],
        }

        model = ChatMaritaca(api_key="test-key")  # type: ignore[arg-type]
        structured_model = model.with_structured_output(schema)

        assert structured_model is not None
        assert hasattr(structured_model, "invoke")

    def test_with_structured_output_json_mode(self) -> None:
        """Test with_structured_output with json_mode method."""

        class Person(BaseModel):
            """Information about a person."""

            name: str = Field(description="Person's name")
            age: int = Field(description="Person's age")

        model = ChatMaritaca(api_key="test-key")  # type: ignore[arg-type]
        structured_model = model.with_structured_output(Person, method="json_mode")

        assert structured_model is not None
        assert hasattr(structured_model, "invoke")

    def test_with_structured_output_include_raw(self) -> None:
        """Test with_structured_output with include_raw=True."""

        class Person(BaseModel):
            """Information about a person."""

            name: str = Field(description="Person's name")
            age: int = Field(description="Person's age")

        model = ChatMaritaca(api_key="test-key")  # type: ignore[arg-type]
        structured_model = model.with_structured_output(Person, include_raw=True)

        assert structured_model is not None
        assert hasattr(structured_model, "invoke")

    def test_with_structured_output_no_schema_raises(self) -> None:
        """Test that with_structured_output raises error without schema."""
        model = ChatMaritaca(api_key="test-key")  # type: ignore[arg-type]

        with pytest.raises(ValueError, match="schema must be specified"):
            model.with_structured_output(None)

    def test_with_structured_output_invalid_method_raises(self) -> None:
        """Test that with_structured_output raises error with invalid method."""

        class Person(BaseModel):
            """Information about a person."""

            name: str = Field(description="Person's name")

        model = ChatMaritaca(api_key="test-key")  # type: ignore[arg-type]

        with pytest.raises(ValueError, match="Unrecognized method argument"):
            model.with_structured_output(
                Person,
                method="invalid_method",  # type: ignore[arg-type]
            )


class TestRetryConfiguration:
    """Test retry configuration and logic."""

    def test_default_retry_parameters(self) -> None:
        """Test default retry parameter values."""
        model = ChatMaritaca(api_key="test-key")  # type: ignore[arg-type]
        assert model.max_retries == 2
        assert model.retry_if_rate_limited is True
        assert model.retry_delay == 1.0
        assert model.retry_max_delay == 60.0
        assert model.retry_multiplier == 2.0

    def test_custom_retry_parameters(self) -> None:
        """Test initialization with custom retry parameters."""
        model = ChatMaritaca(
            api_key="test-key",  # type: ignore[arg-type]
            max_retries=5,
            retry_if_rate_limited=False,
            retry_delay=0.5,
            retry_max_delay=30.0,
            retry_multiplier=3.0,
        )
        assert model.max_retries == 5
        assert model.retry_if_rate_limited is False
        assert model.retry_delay == 0.5
        assert model.retry_max_delay == 30.0
        assert model.retry_multiplier == 3.0

    def test_retry_delay_negative_raises(self) -> None:
        """Test that negative retry_delay raises ValueError."""
        with pytest.raises(ValueError, match="retry_delay must be non-negative"):
            ChatMaritaca(
                api_key="test-key",  # type: ignore[arg-type]
                retry_delay=-1.0,
            )

    def test_retry_max_delay_less_than_delay_raises(self) -> None:
        """Test that retry_max_delay < retry_delay raises ValueError."""
        with pytest.raises(
            ValueError,
            match="retry_max_delay must be greater than or equal to retry_delay",
        ):
            ChatMaritaca(
                api_key="test-key",  # type: ignore[arg-type]
                retry_delay=10.0,
                retry_max_delay=5.0,
            )

    def test_retry_multiplier_less_than_one_raises(self) -> None:
        """Test that retry_multiplier < 1.0 raises ValueError."""
        with pytest.raises(ValueError, match=r"retry_multiplier must be at least 1\.0"):
            ChatMaritaca(
                api_key="test-key",  # type: ignore[arg-type]
                retry_multiplier=0.5,
            )

    def test_calculate_retry_delay(self) -> None:
        """Test exponential backoff delay calculation."""
        model = ChatMaritaca(
            api_key="test-key",  # type: ignore[arg-type]
            retry_delay=1.0,
            retry_max_delay=60.0,
            retry_multiplier=2.0,
        )
        # attempt 0: 1.0 * 2^0 = 1.0
        assert model._calculate_retry_delay(0) == 1.0
        # attempt 1: 1.0 * 2^1 = 2.0
        assert model._calculate_retry_delay(1) == 2.0
        # attempt 2: 1.0 * 2^2 = 4.0
        assert model._calculate_retry_delay(2) == 4.0
        # attempt 3: 1.0 * 2^3 = 8.0
        assert model._calculate_retry_delay(3) == 8.0

    def test_calculate_retry_delay_capped_at_max(self) -> None:
        """Test that retry delay is capped at retry_max_delay."""
        model = ChatMaritaca(
            api_key="test-key",  # type: ignore[arg-type]
            retry_delay=10.0,
            retry_max_delay=30.0,
            retry_multiplier=2.0,
        )
        # attempt 0: 10.0 * 2^0 = 10.0
        assert model._calculate_retry_delay(0) == 10.0
        # attempt 1: 10.0 * 2^1 = 20.0
        assert model._calculate_retry_delay(1) == 20.0
        # attempt 2: 10.0 * 2^2 = 40.0 -> capped at 30.0
        assert model._calculate_retry_delay(2) == 30.0
        # attempt 3: 10.0 * 2^3 = 80.0 -> capped at 30.0
        assert model._calculate_retry_delay(3) == 30.0

    def test_retry_disabled_for_rate_limit(self) -> None:
        """Test that rate limit retry can be disabled."""
        import httpx

        model = ChatMaritaca(
            api_key="test-key",  # type: ignore[arg-type]
            retry_if_rate_limited=False,
            max_retries=3,
        )

        # Create a mock response that returns 429 Too Many Requests
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "1"}

        mock_client = MagicMock()
        mock_client.post.side_effect = httpx.HTTPStatusError(
            "Rate limited",
            request=MagicMock(),
            response=mock_response,
        )
        model.client = mock_client

        # Should raise immediately without retrying
        with pytest.raises(httpx.HTTPStatusError):
            model._make_request([], {})

        # Should only be called once (no retries)
        assert mock_client.post.call_count == 1

    @patch("langchain_maritaca.chat_models.time.sleep")
    def test_retry_with_exponential_backoff_on_timeout(
        self, mock_sleep: MagicMock
    ) -> None:
        """Test exponential backoff on timeout errors."""
        import httpx

        model = ChatMaritaca(
            api_key="test-key",  # type: ignore[arg-type]
            max_retries=2,
            retry_delay=1.0,
            retry_multiplier=2.0,
        )

        mock_client = MagicMock()
        mock_client.post.side_effect = httpx.TimeoutException("Timeout")
        model.client = mock_client

        with pytest.raises(httpx.TimeoutException):
            model._make_request([], {})

        # Should have retried max_retries times
        assert mock_client.post.call_count == 3  # 1 initial + 2 retries

        # Check exponential backoff delays
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(1.0)  # First retry: 1.0 * 2^0
        mock_sleep.assert_any_call(2.0)  # Second retry: 1.0 * 2^1
