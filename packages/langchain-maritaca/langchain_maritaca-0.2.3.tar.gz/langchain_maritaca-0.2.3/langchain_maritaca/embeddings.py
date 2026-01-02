"""DeepInfra Embeddings for use with Maritaca AI workflows.

Maritaca AI recommends DeepInfra's multilingual-e5-large model for embeddings
in RAG (Retrieval-Augmented Generation) workflows with Sabiá models.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
GitHub: https://github.com/anderson-ufrj
"""

from __future__ import annotations

from typing import Any

import httpx
from langchain_core.embeddings import Embeddings
from langchain_core.utils import from_env, secret_from_env
from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator
from typing_extensions import Self

from langchain_maritaca.version import __version__

# Default embedding model recommended by Maritaca AI
DEFAULT_MODEL = "intfloat/multilingual-e5-large"
DEFAULT_API_BASE = "https://api.deepinfra.com/v1/openai"


class DeepInfraEmbeddings(BaseModel, Embeddings):
    """DeepInfra embeddings integration for Maritaca AI workflows.

    DeepInfra provides the multilingual-e5-large model, which is recommended
    by Maritaca AI for RAG workflows with their Sabiá models. This model
    supports 100 languages including Portuguese.

    To use, you should have the environment variable `DEEPINFRA_API_KEY`
    set with your API key, or pass it as a named parameter to the constructor.

    Setup:
        Install `langchain-maritaca` and set environment variable
        `DEEPINFRA_API_KEY`.

        ```bash
        pip install -U langchain-maritaca
        export DEEPINFRA_API_KEY="your-api-key"
        ```

    Key init args:
        model:
            Name of embedding model to use. Default is
            `intfloat/multilingual-e5-large`.
        api_key:
            DeepInfra API key. If not passed in will be read from
            env var `DEEPINFRA_API_KEY`.

    Instantiate:
        ```python
        from langchain_maritaca import DeepInfraEmbeddings

        embeddings = DeepInfraEmbeddings()
        ```

    Embed single text:
        ```python
        vector = embeddings.embed_query("Olá, como vai você?")
        print(len(vector))  # 1024
        ```

    Embed multiple texts:
        ```python
        vectors = embeddings.embed_documents(
            [
                "Primeiro documento",
                "Segundo documento",
            ]
        )
        print(len(vectors))  # 2
        print(len(vectors[0]))  # 1024
        ```

    Use with Maritaca for RAG:
        ```python
        from langchain_maritaca import ChatMaritaca, DeepInfraEmbeddings
        from langchain_community.vectorstores import FAISS

        embeddings = DeepInfraEmbeddings()
        vectorstore = FAISS.from_texts(documents, embeddings)

        llm = ChatMaritaca()
        # ... build your RAG chain
        ```
    """

    client: Any = Field(default=None, exclude=True)
    """Sync HTTP client."""

    async_client: Any = Field(default=None, exclude=True)
    """Async HTTP client."""

    model: str = Field(default=DEFAULT_MODEL)
    """Model name to use.

    Default is `intfloat/multilingual-e5-large`, which is optimized for
    multilingual text including Portuguese. Supports 100 languages.
    Embedding dimension: 1024, max tokens: 512.
    """

    deepinfra_api_key: SecretStr | None = Field(
        alias="api_key",
        default_factory=secret_from_env("DEEPINFRA_API_KEY", default=None),
    )
    """DeepInfra API key. Automatically inferred from env var `DEEPINFRA_API_KEY`."""

    deepinfra_api_base: str = Field(
        alias="base_url",
        default_factory=from_env("DEEPINFRA_API_BASE", default=DEFAULT_API_BASE),
    )
    """Base URL for DeepInfra API."""

    request_timeout: float | None = Field(default=60.0, alias="timeout")
    """Timeout for requests in seconds."""

    max_retries: int = 2
    """Maximum number of retries."""

    batch_size: int = 32
    """Maximum number of texts to embed in a single request."""

    model_config = ConfigDict(
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def validate_environment(self) -> Self:
        """Validate that API key exists and initialize HTTP clients."""
        api_key = (
            self.deepinfra_api_key.get_secret_value() if self.deepinfra_api_key else ""
        )
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"langchain-maritaca/{__version__}",
        }

        if not self.client:
            self.client = httpx.Client(
                base_url=self.deepinfra_api_base,
                headers=headers,
                timeout=httpx.Timeout(self.request_timeout),
            )

        if not self.async_client:
            self.async_client = httpx.AsyncClient(
                base_url=self.deepinfra_api_base,
                headers=headers,
                timeout=httpx.Timeout(self.request_timeout),
            )

        return self

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of documents using DeepInfra.

        Args:
            texts: The list of texts to embed.

        Returns:
            List of embeddings, one for each text.
        """
        embeddings: list[list[float]] = []

        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            batch_embeddings = self._embed_batch(batch)
            embeddings.extend(batch_embeddings)

        return embeddings

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query text.

        Args:
            text: The text to embed.

        Returns:
            Embedding for the text.
        """
        return self.embed_documents([text])[0]

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        """Async embed a list of documents using DeepInfra.

        Args:
            texts: The list of texts to embed.

        Returns:
            List of embeddings, one for each text.
        """
        embeddings: list[list[float]] = []

        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            batch_embeddings = await self._aembed_batch(batch)
            embeddings.extend(batch_embeddings)

        return embeddings

    async def aembed_query(self, text: str) -> list[float]:
        """Async embed a single query text.

        Args:
            text: The text to embed.

        Returns:
            Embedding for the text.
        """
        result = await self.aembed_documents([text])
        return result[0]

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts synchronously.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embeddings.
        """
        payload = {
            "input": texts,
            "model": self.model,
            "encoding_format": "float",
        }

        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.post("/embeddings", json=payload)
                response.raise_for_status()
                data = response.json()
                # Sort by index to ensure correct order
                sorted_data = sorted(data["data"], key=lambda x: x["index"])
                return [item["embedding"] for item in sorted_data]
            except httpx.TimeoutException:
                if attempt < self.max_retries:
                    continue
                raise
            except httpx.HTTPStatusError:
                if attempt < self.max_retries:
                    continue
                raise

        msg = f"Failed after {self.max_retries + 1} attempts"
        raise RuntimeError(msg)

    async def _aembed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts asynchronously.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embeddings.
        """
        payload = {
            "input": texts,
            "model": self.model,
            "encoding_format": "float",
        }

        for attempt in range(self.max_retries + 1):
            try:
                response = await self.async_client.post("/embeddings", json=payload)
                response.raise_for_status()
                data = response.json()
                # Sort by index to ensure correct order
                sorted_data = sorted(data["data"], key=lambda x: x["index"])
                return [item["embedding"] for item in sorted_data]
            except httpx.TimeoutException:
                if attempt < self.max_retries:
                    continue
                raise
            except httpx.HTTPStatusError:
                if attempt < self.max_retries:
                    continue
                raise

        msg = f"Failed after {self.max_retries + 1} attempts"
        raise RuntimeError(msg)
