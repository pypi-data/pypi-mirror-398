import asyncio
import json
import os
import tempfile
from typing import Literal

from google import genai
from google.genai import types
from langchain_core.embeddings import Embeddings
from openai import AsyncOpenAI, OpenAI


class OpenAIEmbeddings(Embeddings):
    """Custom embeddings using OpenAI-compatible API."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        batch_size: int = 50,
        vector_size: int | None = None,
    ) -> None:
        """Initialize CustomEmbeddings.

        Args:
            base_url: Base URL for the OpenAI-compatible API
            api_key: API key for authentication
            model: Model name to use for embeddings
            batch_size: Batch size for embedding documents
            vector_size: Vector size for embeddings (auto-detected if None)
        """
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.async_client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        self.model = model
        self.__batch_size = batch_size
        self.vector_size = vector_size or self.set_vector_size()

    def set_vector_size(self) -> int:
        """Auto-detect vector size by embedding a test string."""
        text = "test"
        response = self.client.embeddings.create(
            model=self.model,
            input=[text],
        )
        return len(response.data[0].embedding)

    def embed_documents(
        self, texts: list[str], batch_size: int | None = None
    ) -> list[list[float]]:
        """Embed a list of documents.

        Args:
            texts: List of texts to embed
            batch_size: Batch size (uses default if None)

        Returns:
            List of embeddings
        """
        all_embeddings: list[list[float]] = []
        batch_size = batch_size or self.__batch_size
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch,
                )
            except Exception as e:
                raise Exception(f"Failed to embed documents: {batch}") from e
            embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(embeddings)
        return all_embeddings

    async def aembed_documents(
        self, texts: list[str], batch_size: int | None = None
    ) -> list[list[float]]:
        """Async version of embed_documents."""
        batch_size = batch_size or self.__batch_size

        async def embed_batch(batch: list[str]) -> list[list[float]]:
            try:
                response = await self.async_client.embeddings.create(
                    model=self.model,
                    input=batch,
                )
                return [item.embedding for item in response.data]
            except Exception as e:
                raise Exception(f"Failed to embed documents: {batch}") from e

        batches = [texts[i : i + batch_size] for i in range(0, len(texts), batch_size)]
        results = await asyncio.gather(*[embed_batch(batch) for batch in batches])

        all_embeddings: list[list[float]] = []
        for batch_embeddings in results:
            all_embeddings.extend(batch_embeddings)
        return all_embeddings

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        response = self.client.embeddings.create(
            model=self.model,
            input=[text],
        )
        return response.data[0].embedding

    async def aembed_query(self, text: str) -> list[float]:
        """Async version of embed_query."""
        response = await self.async_client.embeddings.create(
            model=self.model,
            input=[text],
        )
        return response.data[0].embedding


class VertexEmbeddings(Embeddings):
    """Vertex AI embeddings using google-genai SDK."""

    def __init__(
        self,
        credentials_data: dict,
        model_name: Literal[
            "text-embedding-005",
            "text-multilingual-embedding-002",
        ] = "text-multilingual-embedding-002",
        vector_size: int = 768,
        batch_size: int = 100,
    ):
        """Initialize VertexEmbeddings.

        Args:
            credentials_data: GCP service account credentials
            model_name: Vertex AI embedding model name
            vector_size: Output dimensionality for embeddings
            batch_size: Batch size for embedding documents
        """
        # Set up environment for Vertex AI with cross-platform temp file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as temp_file:
            json.dump(credentials_data, temp_file)
            temp_file_path = temp_file.name

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_file_path

        # Create client for Vertex AI
        self._client = genai.Client(
            vertexai=True,
            project=credentials_data.get("project_id"),
            location="us-central1",
        )
        self.model_name = model_name
        self.vector_size = vector_size
        self.__batch_size = batch_size

    def embed_documents(
        self, texts: list[str], batch_size: int | None = None
    ) -> list[list[float]]:
        """Embed a list of documents.

        Args:
            texts: List of texts to embed
            batch_size: Batch size (uses default if None)

        Returns:
            List of embeddings
        """
        all_embeddings: list[list[float]] = []
        batch_size = batch_size or self.__batch_size
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            # Replace empty texts with placeholder
            batch = [text or "EMPTY" for text in batch]

            try:
                # Use embed_content with the new SDK
                response = self._client.models.embed_content(
                    model=self.model_name,
                    contents=batch,
                    config=types.EmbedContentConfig(
                        task_type="RETRIEVAL_DOCUMENT",
                        output_dimensionality=self.vector_size,
                    ),
                )

                # Extract embeddings from response
                embeddings = [emb.values for emb in response.embeddings]
                all_embeddings.extend(embeddings)
            except Exception as e:
                raise Exception(f"Failed to embed documents {e} - {batch}") from e

        return all_embeddings
