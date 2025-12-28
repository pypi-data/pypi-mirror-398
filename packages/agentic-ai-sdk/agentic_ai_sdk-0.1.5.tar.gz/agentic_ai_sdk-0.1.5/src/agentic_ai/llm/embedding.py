"""OpenAI-compatible embedding provider.

This module provides a lightweight embedding client that works with both:
- OpenAI API (api.openai.com)
- Azure OpenAI API (*.openai.azure.com)
- Any OpenAI-compatible API endpoint
"""

from __future__ import annotations

import logging
from typing import Iterable, List, Literal

import httpx

from ..observability.tracing import trace_http_request

LOGGER = logging.getLogger("agentic_ai.embedding")


class EmbeddingError(RuntimeError):
    """Raised when embedding generation fails."""


class EmbeddingProvider:
    """Synchronous embedding client compatible with OpenAI and Azure OpenAI APIs.
    
    Examples:
        # OpenAI API
        provider = EmbeddingProvider(
            api_key="sk-...",
            model="text-embedding-ada-002",
        )
        
        # Azure OpenAI API
        provider = EmbeddingProvider(
            endpoint="https://myresource.openai.azure.com",
            api_key="...",
            model="text-embedding-ada-002",
            api_type="azure",
            api_version="2024-02-01",
        )
        
        # Custom OpenAI-compatible endpoint
        provider = EmbeddingProvider(
            endpoint="https://my-llm-service.com/v1",
            api_key="...",
            model="custom-embedding",
        )
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        endpoint: str | None = None,
        api_type: Literal["openai", "azure"] | None = None,
        api_version: str = "2024-02-01",
        timeout: float = 15.0,
        default_headers: dict[str, str] | None = None,
        verify_ssl: bool = True,
    ) -> None:
        """Initialize the embedding provider.
        
        Args:
            api_key: API key for authentication
            model: Embedding model name (e.g., "text-embedding-ada-002")
            endpoint: Base URL. For OpenAI, defaults to "https://api.openai.com/v1".
                     For Azure, provide your resource endpoint.
            api_type: Either "openai" or "azure". If not provided, auto-detects
                     based on endpoint (Azure if contains "azure").
            api_version: API version for Azure OpenAI (ignored for standard OpenAI)
            timeout: Request timeout in seconds
            default_headers: Custom headers to include in all API requests (e.g., for custom auth)
            verify_ssl: Whether to verify SSL certificates for HTTPS requests
        """
        self.model = model
        self.api_version = api_version
        
        # Auto-detect API type if not specified
        if api_type is None:
            if endpoint and "azure" in endpoint.lower():
                api_type = "azure"
            else:
                api_type = "openai"
        
        self.api_type = api_type
        
        if api_type == "azure":
            if not endpoint:
                raise ValueError("endpoint is required for Azure OpenAI")
            self.endpoint = endpoint.rstrip("/")
            self._url = f"{self.endpoint}/openai/deployments/{model}/embeddings"
            headers = {
                "Content-Type": "application/json",
                "api-key": api_key,
            }
        else:
            self.endpoint = (endpoint or "https://api.openai.com/v1").rstrip("/")
            self._url = f"{self.endpoint}/embeddings"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            }
        
        # Merge default_headers (custom headers take precedence)
        if default_headers:
            headers.update(default_headers)
        
        if not verify_ssl:
            LOGGER.warning("SSL certificate verification is disabled for embedding provider")
        
        self._client = httpx.Client(headers=headers, timeout=timeout, verify=verify_ssl)

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> "EmbeddingProvider":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def embed(self, texts: Iterable[str]) -> List[List[float]]:
        """Generate embeddings for the given texts.
        
        Args:
            texts: Iterable of text strings to embed
            
        Returns:
            List of embedding vectors (one per input text)
            
        Raises:
            EmbeddingError: If the API request fails
        """
        clean_texts = [t if t else " " for t in texts]
        
        # Build request based on API type
        if self.api_type == "azure":
            params = {"api-version": self.api_version}
            payload = {"input": clean_texts, "model": self.model}
        else:
            params = {}
            payload = {"input": clean_texts, "model": self.model}

        LOGGER.debug(
            "Embedding request",
            extra={
                "embedding.model": self.model,
                "embedding.text_count": len(clean_texts),
                "embedding.api_type": self.api_type,
            },
        )

        service_name = "azure_openai_embedding" if self.api_type == "azure" else "openai_embedding"
        
        with trace_http_request(
            service_name=service_name,
            operation="embed",
            method="POST",
            url=self._url,
            attributes={
                "model": self.model,
                "text_count": len(clean_texts),
                "api_type": self.api_type,
            },
        ) as trace_ctx:
            try:
                resp = self._client.post(self._url, params=params, json=payload)
                trace_ctx["status_code"] = resp.status_code
                
                embedding_count = 0
                embedding_dim = 0
                items: list = []
                
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("data", []) if isinstance(data, dict) else []
                    embedding_count = len(items)
                    if items and items[0].get("embedding"):
                        embedding_dim = len(items[0]["embedding"])
                
                trace_ctx["result_count"] = embedding_count
                
                LOGGER.debug(
                    "Embedding response",
                    extra={
                        "embedding.status_code": resp.status_code,
                        "embedding.count": embedding_count,
                        "embedding.dimension": embedding_dim,
                    },
                )
                
                resp.raise_for_status()
                return [item.get("embedding", []) for item in items]
                
            except httpx.HTTPStatusError as exc:
                trace_ctx["error"] = exc
                LOGGER.warning(
                    "Embedding HTTP error: status=%s",
                    exc.response.status_code,
                    extra={
                        "embedding.status_code": exc.response.status_code,
                        "embedding.error": exc.response.text[:500],
                    },
                )
                raise EmbeddingError(
                    f"Embedding request failed ({exc.response.status_code}): {exc.response.text}"
                ) from exc
            except httpx.HTTPError as exc:
                trace_ctx["error"] = exc
                LOGGER.warning("Embedding network error: %s", exc)
                raise EmbeddingError(f"Embedding request failed: {exc}") from exc


__all__ = ["EmbeddingProvider", "EmbeddingError"]
