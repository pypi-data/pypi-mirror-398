import asyncio
from typing import Any

import httpx
from langchain_core.embeddings import Embeddings
from loguru import logger


class CustomEmbeddings(Embeddings):
    """Custom embeddings using custom API format (similar to Ollama but with different request/response format)."""

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str | None = None,
        batch_size: int = 50,  # Not used, kept for compatibility
    ):
        """Initialize CustomEmbeddings.

        Args:
            base_url: Base URL for the custom embeddings API
            model: Model name to use for embeddings
            api_key: Optional API key for authentication
            batch_size: Not used (kept for compatibility), model doesn't support batching
        """
        # Clean base_url: remove trailing slashes and any invisible characters
        self.base_url = base_url.rstrip("/").strip()
        self.model = model
        self.api_key = api_key
        # Increased timeout for large texts and slow APIs (5 minutes)
        # Disable keepalive to avoid connection issues with parallel requests
        # Each connection will be closed after use
        limits = httpx.Limits(max_connections=100, max_keepalive_connections=0)
        # Separate timeouts: connect=10s, read=300s (5 min) for large responses
        timeout = httpx.Timeout(10.0, read=300.0)
        self._client = httpx.AsyncClient(timeout=timeout, limits=limits)

    def _get_headers(self) -> dict[str, str]:
        """Get headers for API requests."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        # Add ngrok header if using ngrok URL
        if "ngrok" in self.base_url.lower():
            headers["ngrok-skip-browser-warning"] = "true"
        return headers

    def _is_runpod_api(self) -> bool:
        """Check if this is a RunPod API endpoint."""
        return "runpod.ai" in self.base_url.lower()

    def _is_ollama_api(self) -> bool:
        """Check if this is an Ollama-compatible API endpoint."""
        return ":11434" in self.base_url or "ollama" in self.base_url.lower()

    def _get_runpod_status_url(self, job_id: str) -> str:
        """Get RunPod status endpoint URL for polling."""
        # Extract base URL without /run
        base = self.base_url.rstrip("/")
        if base.endswith("/run"):
            base = base[:-4]  # Remove /run
        return f"{base}/status/{job_id}"

    async def _poll_runpod_status(
        self, job_id: str, request_id: str, max_wait: int = 300
    ) -> dict[str, Any]:
        """Poll RunPod API status until job is completed.

        Args:
            job_id: RunPod job ID
            request_id: Request ID for logging
            max_wait: Maximum time to wait in seconds (default: 5 minutes)

        Returns:
            Final status response with output
        """
        status_url = self._get_runpod_status_url(job_id)
        start_time = asyncio.get_event_loop().time()
        poll_interval = 1.0  # Start with 1 second polling

        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > max_wait:
                raise TimeoutError(
                    f"RunPod job {job_id} did not complete within {max_wait}s"
                )

            logger.debug(
                f"CustomEmbeddings[{request_id}]: Polling RunPod status for job {job_id}..."
            )
            try:
                response = await self._client.get(
                    status_url,
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                status_result = response.json()
            except Exception as e:
                logger.error(
                    f"CustomEmbeddings[{request_id}]: Error polling status: {e}"
                )
                raise

            status = status_result.get("status", "").upper()
            elapsed_time = int(asyncio.get_event_loop().time() - start_time)
            logger.info(
                f"CustomEmbeddings[{request_id}]: Job {job_id} status: {status} (elapsed: {elapsed_time}s)"
            )

            if status == "COMPLETED":
                logger.info(
                    f"CustomEmbeddings[{request_id}]: Job {job_id} completed successfully"
                )
                return status_result
            elif status in ("FAILED", "CANCELLED"):
                error_msg = status_result.get("error", "Unknown error")
                logger.error(
                    f"CustomEmbeddings[{request_id}]: Job {job_id} failed with status {status}: {error_msg}"
                )
                raise Exception(f"RunPod job {job_id} failed: {error_msg}")

            # Exponential backoff: increase polling interval up to 5 seconds
            await asyncio.sleep(min(poll_interval, 5.0))
            poll_interval = min(poll_interval * 1.2, 5.0)

    async def _embed_single(
        self, text: str, request_id: str | None = None
    ) -> list[float]:
        """Embed a single text using the custom API format.

        Args:
            text: Text to embed
            request_id: Optional request ID for logging

        Returns:
            Embedding vector
        """
        # Replace empty texts with placeholder
        prompt = text or "EMPTY"
        req_id = request_id or "unknown"

        try:
            # Log text length for debugging large texts
            text_length = len(prompt)
            if text_length > 10000:
                logger.warning(
                    f"CustomEmbeddings[{req_id}]: Large text detected ({text_length} chars), "
                    f"may cause server disconnection"
                )

            # Check API type
            is_runpod = self._is_runpod_api()
            is_ollama = self._is_ollama_api()

            if is_ollama:
                # Ollama API format: POST /api/embed with {"model": "...", "input": "..."}
                # Note: Ollama uses "input" (not "prompt") and returns {"embeddings": [[...]]}
                payload = {
                    "model": self.model,
                    "input": prompt,
                }

                # Clean base_url and determine endpoint
                # Ollama can use either /api/embed or /api/embeddings
                ollama_url = self.base_url.strip().rstrip("/")
                # Remove any non-printable characters
                ollama_url = "".join(
                    char
                    for char in ollama_url
                    if char.isprintable() or char in ["/", ":", "-", "."]
                )

                # Check which endpoint is already in the URL
                if (
                    "/api/embed" in ollama_url.lower()
                    and "/api/embeddings" not in ollama_url.lower()
                ):
                    # Use /api/embed endpoint (newer format)
                    idx = ollama_url.lower().find("/api/embed")
                    ollama_url = ollama_url[: idx + len("/api/embed")]
                elif "/api/embeddings" in ollama_url.lower():
                    # Use /api/embeddings endpoint (older format)
                    idx = ollama_url.lower().find("/api/embeddings")
                    ollama_url = ollama_url[: idx + len("/api/embeddings")]
                    # For /api/embeddings, use "prompt" instead of "input"
                    payload = {
                        "model": self.model,
                        "prompt": prompt,
                    }
                elif ollama_url.endswith("/api"):
                    # Default to /api/embed (newer format)
                    ollama_url = f"{ollama_url}/embed"
                else:
                    # Add /api/embed if not present
                    ollama_url = f"{ollama_url}/api/embed"

                logger.info(
                    f"CustomEmbeddings[{req_id}]: Sending POST request to Ollama API\n"
                    f"  URL: {ollama_url}\n"
                    f"  Payload: {payload}"
                )

                try:
                    response = await self._client.post(
                        ollama_url,
                        json=payload,
                        headers=self._get_headers(),
                    )
                    logger.info(
                        f"CustomEmbeddings[{req_id}]: Got response status {response.status_code}"
                    )
                    response.raise_for_status()
                    result = response.json()
                    logger.info(
                        f"CustomEmbeddings[{req_id}]: Ollama response received: {str(result)[:500]}"
                    )

                    # Extract embedding from Ollama response
                    # Format 1 (newer /api/embed): {"embeddings": [[...]]}
                    embedding = None
                    if "embeddings" in result and isinstance(
                        result["embeddings"], list
                    ):
                        if len(result["embeddings"]) > 0:
                            embedding = result["embeddings"][0]

                    # Format 2 (older /api/embeddings): {"embedding": [...]}
                    if not embedding and "embedding" in result:
                        embedding = result["embedding"]

                    if not embedding:
                        logger.error(f"Unexpected Ollama response format: {result}")
                        raise ValueError(f"No embedding in Ollama response: {result}")

                    logger.debug(
                        f"CustomEmbeddings[{req_id}]: Embedding extracted from Ollama, length={len(embedding) if embedding else 0}"
                    )
                    return embedding
                except Exception as e:
                    logger.error(
                        f"CustomEmbeddings[{req_id}]: Error calling Ollama API: {e}"
                    )
                    raise

            elif is_runpod:
                # RunPod API format: POST /run with {"input": {"text": "..."}}
                # Then poll /status/{job_id} until completion
                payload = {"input": {"text": prompt}}
                headers = self._get_headers()

                logger.info(
                    f"CustomEmbeddings[{req_id}]: Sending POST request to RunPod API\n"
                    f"  URL: {self.base_url}\n"
                    f"  Payload: {payload}\n"
                    f"  Headers: {dict((k, v if k != 'Authorization' else '***') for k, v in headers.items())}"
                )

                try:
                    # Submit job
                    response = await self._client.post(
                        self.base_url,
                        json=payload,
                        headers=headers,
                    )
                    logger.info(
                        f"CustomEmbeddings[{req_id}]: Got response status {response.status_code}"
                    )
                    response.raise_for_status()
                    job_result = response.json()
                    logger.info(
                        f"CustomEmbeddings[{req_id}]: RunPod job submitted: {str(job_result)[:500]}"
                    )

                    # Extract job ID
                    job_id = job_result.get("id")
                    if not job_id:
                        logger.error(
                            f"CustomEmbeddings[{req_id}]: No job ID in RunPod response: {job_result}"
                        )
                        raise ValueError(f"No job ID in RunPod response: {job_result}")

                    status = job_result.get("status", "").upper()
                    logger.info(
                        f"CustomEmbeddings[{req_id}]: Job {job_id} initial status: {status}"
                    )

                    # If already completed, return result
                    if status == "COMPLETED":
                        result = job_result
                    else:
                        # Poll for completion
                        result = await self._poll_runpod_status(job_id, req_id)

                except httpx.RemoteProtocolError as e:
                    logger.error(
                        f"CustomEmbeddings[{req_id}]: RemoteProtocolError connecting to RunPod API: {e}\n"
                        f"  URL: {self.base_url}\n"
                        f"  This may indicate the endpoint doesn't exist or server closed connection"
                    )
                    raise
                except httpx.ConnectError as e:
                    logger.error(
                        f"CustomEmbeddings[{req_id}]: ConnectError connecting to RunPod API: {e}\n"
                        f"  URL: {self.base_url}"
                    )
                    raise
                except httpx.NetworkError as e:
                    logger.error(
                        f"CustomEmbeddings[{req_id}]: NetworkError connecting to RunPod API: {e}\n"
                        f"  URL: {self.base_url}"
                    )
                    raise

                # Extract embedding from RunPod output
                # RunPod response format: {"output": {...}}
                # Try multiple possible formats
                logger.info(
                    f"CustomEmbeddings[{req_id}]: Extracting embedding from RunPod result..."
                )
                output = result.get("output")

                if not output:
                    # Maybe the response is directly the output?
                    if "embedding" in result:
                        embedding = result.get("embedding")
                        if embedding:
                            logger.debug(
                                f"CustomEmbeddings[{req_id}]: Embedding found directly in response"
                            )
                            return embedding
                    logger.error(f"Unexpected RunPod response format: {result}")
                    raise ValueError(f"No output in RunPod response: {result}")

                # Try different output formats
                embedding = None

                # Format 1: {"output": {"embedding": [...]}}
                if isinstance(output, dict):
                    embedding = output.get("embedding")
                    if embedding:
                        logger.debug(
                            f"CustomEmbeddings[{req_id}]: Embedding found in output.embedding"
                        )

                # Format 2: {"output": {"data": [{"embedding": [...]}]}}
                if not embedding and isinstance(output, dict) and "data" in output:
                    data = output.get("data")
                    if isinstance(data, list) and len(data) > 0:
                        if isinstance(data[0], dict):
                            embedding = data[0].get("embedding")
                            if embedding:
                                logger.debug(
                                    f"CustomEmbeddings[{req_id}]: Embedding found in output.data[0].embedding"
                                )

                # Format 3: {"output": [{"embedding": [...]}]}
                if not embedding and isinstance(output, list) and len(output) > 0:
                    if isinstance(output[0], dict):
                        embedding = output[0].get("embedding")
                        if embedding:
                            logger.debug(
                                f"CustomEmbeddings[{req_id}]: Embedding found in output[0].embedding"
                            )

                # Format 4: {"output": [...]} - direct list of numbers
                if not embedding and isinstance(output, list) and len(output) > 0:
                    if isinstance(output[0], (int, float)):
                        embedding = output
                        logger.debug(
                            f"CustomEmbeddings[{req_id}]: Embedding found as direct list in output"
                        )

                if not embedding:
                    logger.error(
                        f"Unexpected RunPod output format. Full output: {output}"
                    )
                    raise ValueError(
                        f"No embedding found in RunPod output. Output structure: {type(output).__name__}, keys: {list(output.keys()) if isinstance(output, dict) else 'N/A'}"
                    )

                logger.debug(
                    f"CustomEmbeddings[{req_id}]: Embedding extracted from RunPod, length={len(embedding) if embedding else 0}"
                )
                return embedding
            else:
                # Standard API format
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                }

                logger.debug(
                    f"CustomEmbeddings[{req_id}]: Sending POST request, payload_size={len(str(payload))}"
                )
                response = await self._client.post(
                    self.base_url,
                    json=payload,
                    headers=self._get_headers(),
                )
                logger.debug(
                    f"CustomEmbeddings[{req_id}]: Got response status {response.status_code}, content_length={response.headers.get('content-length', 'unknown')}"
                )
                response.raise_for_status()

                logger.debug(
                    f"CustomEmbeddings[{req_id}]: About to read response body (content_length={response.headers.get('content-length', 'unknown')})..."
                )
                try:
                    result = response.json()
                    logger.debug(
                        f"CustomEmbeddings[{req_id}]: Response body read and parsed successfully"
                    )
                except Exception as e:
                    logger.error(
                        f"CustomEmbeddings[{req_id}]: Error reading/parsing response body: {e}"
                    )
                    raise
                logger.debug(
                    f"CustomEmbeddings[{req_id}]: Extracting embedding from result..."
                )

                # Extract embedding from response
                # Format: {"embedding": [...], "model": "..."}
                # Also check for alternative formats
                embedding = result.get("embedding")
                if not embedding:
                    # Try alternative response formats
                    if "data" in result and isinstance(result["data"], list):
                        embedding = (
                            result["data"][0].get("embedding")
                            if result["data"]
                            else None
                        )
                    if not embedding:
                        logger.error(f"Unexpected response format: {result}")
                        raise ValueError(f"No embedding in response: {result}")

                logger.debug(
                    f"CustomEmbeddings[{req_id}]: Embedding extracted, length={len(embedding) if embedding else 0}"
                )
                return embedding
        except httpx.HTTPStatusError as e:
            # Get error details from response
            error_detail = "Unknown error"
            try:
                error_response = e.response.json()
                error_detail = str(error_response)
            except Exception:
                error_detail = e.response.text or str(e)
            raise Exception(
                f"CustomEmbeddings[{req_id}]: Failed to embed text '{prompt[:50]}...': HTTP {e.response.status_code} - {error_detail}"
            ) from e
        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.TimeoutException) as e:
            # Timeout errors should be retried by the caller
            logger.warning(
                f"CustomEmbeddings[{req_id}]: Timeout error (length={len(prompt)}): {e}"
            )
            raise Exception(f"Timeout embedding text '{prompt[:50]}...': {e}") from e
        except (httpx.ConnectError, httpx.NetworkError, httpx.RemoteProtocolError) as e:
            # Connection errors - server disconnected, network issues, etc.
            error_msg = str(e).lower()
            if "disconnected" in error_msg or "connection" in error_msg:
                logger.warning(
                    f"CustomEmbeddings[{req_id}]: Server disconnected error "
                    f"(length={len(prompt)}): {e}. This may be due to large text size or server timeout."
                )
            raise Exception(
                f"Connection error embedding text '{prompt[:50]}...' (length={len(prompt)}): {e}"
            ) from e
        except Exception as e:
            error_msg = str(e).lower()
            if "disconnected" in error_msg:
                logger.warning(
                    f"CustomEmbeddings[{req_id}]: Server disconnected error "
                    f"(length={len(prompt)}): {e}"
                )
            raise Exception(
                f"Failed to embed text '{prompt[:50]}...' (length={len(prompt)}): {e}"
            ) from e

    def embed_documents(
        self, texts: list[str], batch_size: int | None = None
    ) -> list[list[float]]:
        """Embed a list of documents.

        Args:
            texts: List of texts to embed
            batch_size: Not used (kept for compatibility), model doesn't support batching

        Returns:
            List of embeddings
        """
        return asyncio.run(self.aembed_documents(texts, batch_size))

    async def aembed_documents(
        self, texts: list[str], batch_size: int | None = None
    ) -> list[list[float]]:
        """Async version of embed_documents.

        Note: Model doesn't support batching, so texts are processed sequentially.

        Args:
            texts: List of texts to embed
            batch_size: Not used (kept for compatibility)

        Returns:
            List of embeddings
        """
        total = len(texts)
        logger.info(
            f"CustomEmbeddings: Processing {total} texts sequentially "
            f"(batching not supported)"
        )

        embeddings = []
        for idx, text in enumerate(texts, 1):
            if idx % 10 == 0 or idx == 1:
                logger.info(f"CustomEmbeddings: Processing {idx}/{total} texts...")

            try:
                embedding = await self._embed_single(text, request_id=f"text{idx}")
                embeddings.append(embedding)

                if idx % 100 == 0 or idx == total:
                    logger.info(f"CustomEmbeddings: Completed {idx}/{total} texts")
            except Exception as e:
                logger.error(
                    f"CustomEmbeddings: Error embedding text {idx}/{total}: {e}"
                )
                raise

        logger.info(
            f"CustomEmbeddings: Successfully embedded {len(embeddings)}/{total} texts"
        )
        return embeddings

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        return asyncio.run(self.aembed_query(text))

    async def aembed_query(self, text: str) -> list[float]:
        """Async version of embed_query."""
        return await self._embed_single(text, request_id="query")

    def __del__(self):
        """Clean up client on deletion.

        Note: httpx.AsyncClient will be automatically closed by garbage collector.
        Explicit cleanup should be done via async context manager or explicit aclose() call.
        """
        # httpx.AsyncClient handles cleanup automatically, no need to close in __del__
        pass
