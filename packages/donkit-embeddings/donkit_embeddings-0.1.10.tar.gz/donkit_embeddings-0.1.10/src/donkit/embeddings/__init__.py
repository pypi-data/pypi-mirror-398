"""Custom embeddings implementations for Donkit RagOps."""

from typing import Literal

from langchain_core.embeddings import Embeddings

from .azure_openai_embeddings import AzureOpenAIEmbeddings
from .openai_embedder import OpenAIEmbeddings
from .vertex_embeddings import VertexEmbeddings
from .ollama_embeddings import OllamaEmbeddings
from .donkit_embeddings import DonkitEmbeddings
from .custom_embeddings import CustomEmbeddings


try:
    from .llm_gate_embeddings import LLMGateEmbeddings
except ModuleNotFoundError:
    LLMGateEmbeddings = None


__all__ = [
    "OpenAIEmbeddings",
    "VertexEmbeddings",
    "OllamaEmbeddings",
    "AzureOpenAIEmbeddings",
    "DonkitEmbeddings",
    "CustomEmbeddings",
    "get_custom_embeddings_openai_api",
    "get_custom_embeddings",
    "get_vertexai_embeddings",
    "get_ollama_embeddings",
    "get_azure_openai_embeddings",
    "get_donkit_embeddings",
]


def get_custom_embeddings_openai_api(
    base_url: str, api_key: str, model: str
) -> Embeddings:
    """Factory function for CustomEmbeddings.

    Args:
        base_url: Base URL for the OpenAI-compatible API
        api_key: API key for authentication
        model: Model name to use for embeddings

    Returns:
        CustomEmbeddings instance
    """
    return OpenAIEmbeddings(
        base_url=base_url,
        api_key=api_key,
        model=model,
    )


def get_vertexai_embeddings(
    credentials_data: dict[str, str],
    *,
    model_name: Literal[
        "text-embedding-005",
        "text-multilingual-embedding-002",
    ] = "text-multilingual-embedding-002",
    vector_size: int = 768,
    batch_size: int = 100,
) -> Embeddings:
    """Factory function for VertexEmbeddings.

    Args:
        credentials_data: GCP service account credentials
        model_name: Vertex AI embedding model name
        vector_size: Output dimensionality for embeddings
        batch_size: Batch size for embedding documents

    Returns:
        VertexEmbeddings instance
    """
    return VertexEmbeddings(
        credentials_data=credentials_data,
        model_name=model_name,
        vector_size=vector_size,
        batch_size=batch_size,
    )


def get_ollama_embeddings(
    model: str = "embeddinggemma",
    host: str = "http://localhost:11434",
    batch_size: int = 50,
) -> Embeddings:
    """Factory function for OllamaEmbeddings.

    Args:
        model: Ollama model name
        host: Ollama host
        batch_size: Batch size for embedding documents

    Returns:
        OllamaEmbeddings instance
    """
    return OllamaEmbeddings(
        model=model,
        host=host,
        batch_size=batch_size,
    )


def get_azure_openai_embeddings(
    azure_endpoint: str,
    api_key: str,
    api_version: str,
    embedding_deployment_name: str,
    batch_size: int = 50,
    vector_size: int | None = None,
) -> Embeddings:
    """Factory function for AzureOpenAIEmbeddings.

    Args:
        azure_endpoint: Azure OpenAI endpoint URL
        api_key: API key for authentication
        api_version: API version (e.g., "2024-02-15-preview")
        embedding_deployment_name: Deployment name for the embedding model
        batch_size: Batch size for embedding documents
        vector_size: Vector size for embeddings (auto-detected if None)

    Returns:
        AzureOpenAIEmbeddings instance
    """
    return AzureOpenAIEmbeddings(
        azure_endpoint=azure_endpoint,
        api_key=api_key,
        api_version=api_version,
        embedding_deployment_name=embedding_deployment_name,
        batch_size=batch_size,
        vector_size=vector_size,
    )


def get_donkit_embeddings(
    base_url: str,
    api_token: str,
    provider: str,
    model_name: str | None = None,
    project_id: str | None = None,
    batch_size: int = 50,
    dimensions: int | None = None,
):
    return DonkitEmbeddings(
        base_url=base_url,
        api_token=api_token,
        provider=provider,
        model_name=model_name,
        project_id=project_id,
        batch_size=batch_size,
        dimensions=dimensions,
    )


def get_llm_gate_embeddings(
    base_url: str,
    provider: str,
    model_name: str | None = None,
    project_id: str | None = None,
    batch_size: int = 50,
    dimensions: int | None = None,
    user_id: str | None = None,
):
    if LLMGateEmbeddings is None:
        raise ImportError(
            "LLMGateEmbeddings requires optional dependency 'donkit-llm-gate-client'"
        )
    return LLMGateEmbeddings(
        base_url=base_url,
        provider=provider,
        model_name=model_name,
        project_id=project_id,
        user_id=user_id,
        batch_size=batch_size,
        dimensions=dimensions,
    )


if LLMGateEmbeddings is not None:
    __all__.append("LLMGateEmbeddings")
    __all__.append("get_llm_gate_embeddings")


def get_custom_embeddings(
    base_url: str,
    model: str,
    api_key: str | None = None,
    batch_size: int = 50,
) -> Embeddings:
    """Factory function for CustomEmbeddings.

    Args:
        base_url: Base URL for the custom embeddings API
        model: Model name to use for embeddings
        api_key: Optional API key for authentication
        batch_size: Batch size for embedding documents

    Returns:
        CustomEmbeddings instance
    """
    return CustomEmbeddings(
        base_url=base_url,
        model=model,
        api_key=api_key,
        batch_size=batch_size,
    )
