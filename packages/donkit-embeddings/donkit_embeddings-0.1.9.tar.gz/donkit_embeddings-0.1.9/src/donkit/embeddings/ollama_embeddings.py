import httpx
from loguru import logger
from langchain_core.embeddings import Embeddings


class OllamaEmbeddings(Embeddings):
    """Ollama embeddings using native async HTTP requests."""

    def __init__(
        self,
        model: str = "embeddinggemma",
        host: str = "http://127.0.0.1:11434",
        batch_size: int = 50,
        max_concurrent_batches: int = 4,
        timeout: float = 120.0,
    ):
        self.model = model
        self.host = host.rstrip("/").removesuffix("/v1")
        logger.info(f"embeddings_host: {self.host}")
        self._batch_size = batch_size
        self._max_concurrent_batches = max(1, max_concurrent_batches)
        self._timeout = timeout

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query (sync)."""
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(
                f"{self.host}/api/embeddings",
                json={"model": self.model, "prompt": text},
            )
            response.raise_for_status()
            return response.json()["embedding"]

    async def aembed_query(self, text: str) -> list[float]:
        """Embed a single query (async)."""
        url = f"{self.host}/api/embeddings"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                url,
                json={"model": self.model, "prompt": text},
            )
            response.raise_for_status()
            return response.json()["embedding"]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple documents (sync)."""
        url = f"{self.host}/api/embed"
        all_embeddings: list[list[float]] = []
        with httpx.Client(timeout=self._timeout) as client:
            for i in range(0, len(texts), self._batch_size):
                batch = [t or "EMPTY" for t in texts[i : i + self._batch_size]]
                response = client.post(
                    url,
                    json={"model": self.model, "input": batch},
                )
                response.raise_for_status()
                all_embeddings.extend(response.json()["embeddings"])
        return all_embeddings

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple documents (async) in batches."""
        import asyncio

        url = f"{self.host}/api/embed"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            batches = [
                [t or "EMPTY" for t in texts[i : i + self._batch_size]]
                for i in range(0, len(texts), self._batch_size)
            ]

            semaphore = asyncio.Semaphore(self._max_concurrent_batches)

            async def _embed_batch(batch: list[str]) -> list[list[float]]:
                async with semaphore:
                    response = await client.post(
                        url,
                        json={"model": self.model, "input": batch},
                    )
                    response.raise_for_status()
                    return response.json()["embeddings"]

            batch_results = await asyncio.gather(
                *(_embed_batch(batch) for batch in batches)
            )
            return [emb for batch in batch_results for emb in batch]
