"""Unit tests for DeepInfraEmbeddings.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
GitHub: https://github.com/anderson-ufrj
"""

import os
from typing import Any
from unittest.mock import MagicMock

import pytest

from langchain_maritaca import DeepInfraEmbeddings

if "DEEPINFRA_API_KEY" not in os.environ:
    os.environ["DEEPINFRA_API_KEY"] = "fake-key"


class TestDeepInfraEmbeddings:
    """Test suite for DeepInfraEmbeddings."""

    def test_initialization_default(self) -> None:
        """Test default initialization."""
        embeddings = DeepInfraEmbeddings()
        assert embeddings.model == "intfloat/multilingual-e5-large"
        assert embeddings.max_retries == 2
        assert embeddings.batch_size == 32

    def test_initialization_with_params(self) -> None:
        """Test initialization with custom parameters."""
        embeddings = DeepInfraEmbeddings(
            api_key="test-key",  # type: ignore[arg-type]
            model="intfloat/multilingual-e5-large-instruct",
            timeout=30.0,
            max_retries=3,
            batch_size=16,
        )
        assert embeddings.model == "intfloat/multilingual-e5-large-instruct"
        assert embeddings.request_timeout == 30.0
        assert embeddings.max_retries == 3
        assert embeddings.batch_size == 16

    def test_initialization_with_alias(self) -> None:
        """Test initialization using parameter aliases."""
        embeddings = DeepInfraEmbeddings(
            api_key="test-key",  # type: ignore[arg-type]
            base_url="https://custom.api.com",
            timeout=45.0,
        )
        assert embeddings.deepinfra_api_base == "https://custom.api.com"
        assert embeddings.request_timeout == 45.0


class TestDeepInfraEmbeddingsIntegration:
    """Integration-style unit tests using mocked HTTP responses."""

    @pytest.fixture
    def mock_embedding_response(self) -> dict[str, Any]:
        """Create a mock API response for embeddings."""
        return {
            "object": "list",
            "data": [
                {
                    "object": "embedding",
                    "index": 0,
                    "embedding": [0.1] * 1024,
                }
            ],
            "model": "intfloat/multilingual-e5-large",
            "usage": {
                "prompt_tokens": 5,
                "total_tokens": 5,
            },
        }

    @pytest.fixture
    def mock_batch_embedding_response(self) -> dict[str, Any]:
        """Create a mock API response for batch embeddings."""
        return {
            "object": "list",
            "data": [
                {
                    "object": "embedding",
                    "index": 0,
                    "embedding": [0.1] * 1024,
                },
                {
                    "object": "embedding",
                    "index": 1,
                    "embedding": [0.2] * 1024,
                },
            ],
            "model": "intfloat/multilingual-e5-large",
            "usage": {
                "prompt_tokens": 10,
                "total_tokens": 10,
            },
        }

    def test_embed_query(self, mock_embedding_response: dict[str, Any]) -> None:
        """Test embed_query method with mocked HTTP client."""
        embeddings = DeepInfraEmbeddings(api_key="test-key")  # type: ignore[arg-type]

        # Mock the HTTP client
        mock_http_response = MagicMock()
        mock_http_response.json.return_value = mock_embedding_response
        mock_http_response.raise_for_status = MagicMock()

        embeddings.client = MagicMock()
        embeddings.client.post.return_value = mock_http_response

        result = embeddings.embed_query("Olá, mundo!")

        assert isinstance(result, list)
        assert len(result) == 1024
        assert result[0] == 0.1

        # Verify the API was called correctly
        embeddings.client.post.assert_called_once()
        call_args = embeddings.client.post.call_args
        assert call_args[0][0] == "/embeddings"
        assert call_args[1]["json"]["input"] == ["Olá, mundo!"]
        assert call_args[1]["json"]["model"] == "intfloat/multilingual-e5-large"

    def test_embed_documents(
        self, mock_batch_embedding_response: dict[str, Any]
    ) -> None:
        """Test embed_documents method with mocked HTTP client."""
        embeddings = DeepInfraEmbeddings(api_key="test-key")  # type: ignore[arg-type]

        # Mock the HTTP client
        mock_http_response = MagicMock()
        mock_http_response.json.return_value = mock_batch_embedding_response
        mock_http_response.raise_for_status = MagicMock()

        embeddings.client = MagicMock()
        embeddings.client.post.return_value = mock_http_response

        result = embeddings.embed_documents(["Primeiro", "Segundo"])

        assert isinstance(result, list)
        assert len(result) == 2
        assert len(result[0]) == 1024
        assert len(result[1]) == 1024
        assert result[0][0] == 0.1
        assert result[1][0] == 0.2

    def test_embed_documents_respects_order(
        self, mock_batch_embedding_response: dict[str, Any]
    ) -> None:
        """Test that embed_documents returns embeddings in correct order."""
        embeddings = DeepInfraEmbeddings(api_key="test-key")  # type: ignore[arg-type]

        # Return embeddings in reversed order to test sorting
        reversed_response = {
            "object": "list",
            "data": [
                {
                    "object": "embedding",
                    "index": 1,
                    "embedding": [0.2] * 1024,
                },
                {
                    "object": "embedding",
                    "index": 0,
                    "embedding": [0.1] * 1024,
                },
            ],
            "model": "intfloat/multilingual-e5-large",
        }

        mock_http_response = MagicMock()
        mock_http_response.json.return_value = reversed_response
        mock_http_response.raise_for_status = MagicMock()

        embeddings.client = MagicMock()
        embeddings.client.post.return_value = mock_http_response

        result = embeddings.embed_documents(["Primeiro", "Segundo"])

        # Should be sorted by index, not by response order
        assert result[0][0] == 0.1  # index 0
        assert result[1][0] == 0.2  # index 1

    def test_embed_documents_batching(self) -> None:
        """Test that embed_documents respects batch_size."""
        embeddings = DeepInfraEmbeddings(
            api_key="test-key",  # type: ignore[arg-type]
            batch_size=2,
        )

        # Create response for each batch
        def create_batch_response(texts: list[str]) -> dict[str, Any]:
            return {
                "object": "list",
                "data": [
                    {"object": "embedding", "index": i, "embedding": [0.1] * 1024}
                    for i in range(len(texts))
                ],
            }

        call_count = 0

        def mock_post(endpoint: str, json: dict[str, Any]) -> MagicMock:
            nonlocal call_count
            call_count += 1
            response = MagicMock()
            response.json.return_value = create_batch_response(json["input"])
            response.raise_for_status = MagicMock()
            return response

        embeddings.client = MagicMock()
        embeddings.client.post.side_effect = mock_post

        # 5 texts with batch_size=2 should result in 3 API calls
        result = embeddings.embed_documents(["a", "b", "c", "d", "e"])

        assert len(result) == 5
        assert call_count == 3  # ceil(5/2) = 3


class TestDeepInfraEmbeddingsAsync:
    """Test async methods for DeepInfraEmbeddings."""

    @pytest.fixture
    def mock_embedding_response(self) -> dict[str, Any]:
        """Create a mock API response for embeddings."""
        return {
            "object": "list",
            "data": [
                {
                    "object": "embedding",
                    "index": 0,
                    "embedding": [0.5] * 1024,
                }
            ],
            "model": "intfloat/multilingual-e5-large",
        }

    @pytest.mark.asyncio
    async def test_aembed_query(self, mock_embedding_response: dict[str, Any]) -> None:
        """Test aembed_query method with mocked async HTTP client."""
        embeddings = DeepInfraEmbeddings(api_key="test-key")  # type: ignore[arg-type]

        # Mock the async HTTP client
        mock_http_response = MagicMock()
        mock_http_response.json.return_value = mock_embedding_response
        mock_http_response.raise_for_status = MagicMock()

        embeddings.async_client = MagicMock()
        embeddings.async_client.post = MagicMock(return_value=mock_http_response)

        # Make it awaitable
        async def mock_post(*args: Any, **kwargs: Any) -> MagicMock:
            return mock_http_response

        embeddings.async_client.post = mock_post

        result = await embeddings.aembed_query("Teste assíncrono")

        assert isinstance(result, list)
        assert len(result) == 1024
        assert result[0] == 0.5

    @pytest.mark.asyncio
    async def test_aembed_documents(
        self, mock_embedding_response: dict[str, Any]
    ) -> None:
        """Test aembed_documents method with mocked async HTTP client."""
        batch_response = {
            "object": "list",
            "data": [
                {"object": "embedding", "index": 0, "embedding": [0.3] * 1024},
                {"object": "embedding", "index": 1, "embedding": [0.4] * 1024},
            ],
        }

        embeddings = DeepInfraEmbeddings(api_key="test-key")  # type: ignore[arg-type]

        mock_http_response = MagicMock()
        mock_http_response.json.return_value = batch_response
        mock_http_response.raise_for_status = MagicMock()

        async def mock_post(*args: Any, **kwargs: Any) -> MagicMock:
            return mock_http_response

        embeddings.async_client.post = mock_post

        result = await embeddings.aembed_documents(["Doc 1", "Doc 2"])

        assert len(result) == 2
        assert result[0][0] == 0.3
        assert result[1][0] == 0.4


class TestDeepInfraEmbeddingsImport:
    """Test that DeepInfraEmbeddings can be imported correctly."""

    def test_import_from_package(self) -> None:
        """Test importing DeepInfraEmbeddings from main package."""
        from langchain_maritaca import DeepInfraEmbeddings

        assert DeepInfraEmbeddings is not None

    def test_import_from_module(self) -> None:
        """Test importing DeepInfraEmbeddings from embeddings module."""
        from langchain_maritaca.embeddings import DeepInfraEmbeddings

        assert DeepInfraEmbeddings is not None
