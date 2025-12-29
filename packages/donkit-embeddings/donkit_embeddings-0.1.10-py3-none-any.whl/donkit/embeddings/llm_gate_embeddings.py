import asyncio

from langchain_core.embeddings import Embeddings

from donkit.llm import EmbeddingRequest
from donkit.llm import LLMGateModel


class LLMGateEmbeddings(Embeddings):
    def __init__(
        self,
        base_url: str,
        provider: str,
        *,
        model_name: str | None = None,
        batch_size: int = 100,
        dimensions: int | None = None,
        project_id: str | None = None,
        user_id: str | None = None,
    ) -> None:
        if LLMGateModel is None:
            raise ImportError(
                "LLMGateEmbeddings requires optional dependency 'donkit-llm-gate-client'"
            )

        self.model = LLMGateModel(
            base_url=base_url,
            provider=provider,
            embedding_provider=provider,
            embedding_model_name=model_name,
            project_id=project_id,
            user_id=user_id,
        )
        self.batch_size = batch_size
        self.dimensions = dimensions

    def embed_documents(
        self, texts: list[str], batch_size: int | None = None
    ) -> list[list[float]]:
        try:
            loop = asyncio.get_running_loop()
            return loop.run_until_complete(self.aembed_documents(texts, batch_size))
        except RuntimeError:
            return asyncio.run(self.aembed_documents(texts, batch_size))

    async def aembed_documents(
        self, texts: list[str], batch_size: int | None = None
    ) -> list[list[float]]:
        batch_size = batch_size or self.batch_size

        async def embed_batch(batch: list[str]) -> list[list[float]]:
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
        try:
            loop = asyncio.get_running_loop()
            return loop.run_until_complete(self.aembed_query(text))
        except RuntimeError:
            return asyncio.run(self.aembed_query(text))

    async def aembed_query(self, text: str) -> list[float]:
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
