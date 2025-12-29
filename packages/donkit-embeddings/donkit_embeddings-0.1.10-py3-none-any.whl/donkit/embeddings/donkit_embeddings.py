"""Embeddings implementation using DonkitModel."""

import asyncio

from langchain_core.embeddings import Embeddings

from donkit.llm import DonkitModel, EmbeddingRequest


class DonkitEmbeddings(Embeddings):
    """Embeddings using DonkitModel."""

    def __init__(
        self,
        base_url: str,
        api_token: str,
        provider: str,
        model_name: str | None = None,
        project_id: str | None = None,
        batch_size: int = 100,
        dimensions: int | None = None,
    ) -> None:
        """Initialize RagopsEmbeddings.

        Args:
            base_url: Base URL for the Ragops API Gateway
            api_token: API token for authentication
            provider: Provider name (e.g., "openai", "vertex", etc.)
            model_name: Model name to use for embeddings
            project_id: Project ID for tracking
            batch_size: Batch size for embedding documents
            dimensions: Output dimensionality (if supported by provider)
        """
        self.model = DonkitModel(
            base_url=base_url,
            api_token=api_token,
            provider=provider,
            model_name=model_name,
            project_id=project_id,
        )
        self.batch_size = batch_size
        self.dimensions = dimensions

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
        try:
            loop = asyncio.get_running_loop()
            # We're in a running event loop, use run_until_complete
            return loop.run_until_complete(self.aembed_documents(texts, batch_size))
        except RuntimeError:
            # No running loop, safe to use asyncio.run
            return asyncio.run(self.aembed_documents(texts, batch_size))

    async def aembed_documents(
        self, texts: list[str], batch_size: int | None = None
    ) -> list[list[float]]:
        """Async version of embed_documents.

        Args:
            texts: List of texts to embed
            batch_size: Batch size (uses default if None)

        Returns:
            List of embeddings
        """
        batch_size = batch_size or self.batch_size

        async def embed_batch(batch: list[str]) -> list[list[float]]:
            # batch = [text or "EMPTY" for text in batch]
            request = EmbeddingRequest(
                input=batch,
                dimensions=self.dimensions,
            )
            try:
                response = await self.model.embed(request)
                return response.embeddings
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
        try:
            loop = asyncio.get_running_loop()
            # We're in a running event loop, use run_until_complete
            return loop.run_until_complete(self.aembed_query(text))
        except RuntimeError:
            # No running loop, safe to use asyncio.run
            return asyncio.run(self.aembed_query(text))

    async def aembed_query(self, text: str) -> list[float]:
        """Async version of embed_query.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        request = EmbeddingRequest(
            input=text,
            dimensions=self.dimensions,
        )

        try:
            response = await self.model.embed(request)
            if not response.embeddings:
                raise Exception("No embeddings returned from API")
            return response.embeddings[0]
        except Exception as e:
            raise Exception(f"Failed to embed query: {text}") from e
