"""Tests for EmbeddingConfig and EmbeddingProvider with custom headers support."""

import pytest
from agentic_ai.config import EmbeddingConfig
from agentic_ai.llm.embedding import EmbeddingProvider


class TestEmbeddingConfig:
    """Tests for EmbeddingConfig with default_headers."""

    def test_embedding_config_with_default_headers(self):
        """Test that EmbeddingConfig accepts default_headers."""
        config = EmbeddingConfig(
            provider="openai",
            model="bge-m3",
            endpoint="http://localhost:8443/aiplatform/llmplatformapimanagementaliyun/v1/lm-platform/llm/v1",
            api_key="dummy",
            dimension=1024,
            api_version="2024-02-01",
            default_headers={
                "apikey": "test-api-key-12345",
                "Authorization": "ACCESSCODE test-access-code-67890",
            },
            verify_ssl=False,
        )

        assert config.model == "bge-m3"
        assert config.default_headers is not None
        assert config.default_headers["apikey"] == "test-api-key-12345"
        assert config.default_headers["Authorization"] == "ACCESSCODE test-access-code-67890"
        assert config.verify_ssl is False

    def test_embedding_config_without_default_headers(self):
        """Test that default_headers is optional."""
        config = EmbeddingConfig(
            provider="openai",
            model="text-embedding-ada-002",
            endpoint="https://api.openai.com/v1",
            api_key="sk-test",
            dimension=1536,
        )

        assert config.default_headers is None
        assert config.verify_ssl is True  # Default value


class TestEmbeddingProviderHeaders:
    """Tests for EmbeddingProvider with custom headers support."""

    def test_embedding_provider_with_default_headers(self):
        """Test that EmbeddingProvider accepts default_headers."""
        provider = EmbeddingProvider(
            api_key="dummy",
            model="bge-m3",
            endpoint="http://localhost:8443/v1",
            default_headers={
                "apikey": "test-key",
                "Authorization": "ACCESSCODE test-code",
            },
            verify_ssl=False,
        )

        # Verify headers are set correctly
        assert "apikey" in provider._client.headers
        assert provider._client.headers["apikey"] == "test-key"
        assert provider._client.headers["Authorization"] == "ACCESSCODE test-code"
        # Standard headers should still be present
        assert "Content-Type" in provider._client.headers

        provider.close()

    def test_embedding_provider_without_default_headers(self):
        """Test that EmbeddingProvider works without default_headers."""
        provider = EmbeddingProvider(
            api_key="sk-test",
            model="text-embedding-ada-002",
        )

        # Standard Authorization header should be present
        assert "Authorization" in provider._client.headers
        assert provider._client.headers["Authorization"] == "Bearer sk-test"

        provider.close()

    def test_embedding_provider_custom_headers_override_defaults(self):
        """Test that custom headers can override default Authorization."""
        provider = EmbeddingProvider(
            api_key="sk-test",
            model="bge-m3",
            endpoint="http://localhost:8443/v1",
            default_headers={
                "Authorization": "ACCESSCODE custom-auth",
            },
        )

        # Custom Authorization should override the default Bearer token
        assert provider._client.headers["Authorization"] == "ACCESSCODE custom-auth"

        provider.close()

    def test_embedding_provider_url_construction(self):
        """Test that endpoint URL is correctly constructed with /embeddings suffix."""
        provider = EmbeddingProvider(
            api_key="dummy",
            model="bge-m3",
            endpoint="http://localhost:8443/aiplatform/llmplatformapimanagementaliyun/v1/lm-platform/llm/v1",
        )

        expected_url = "http://localhost:8443/aiplatform/llmplatformapimanagementaliyun/v1/lm-platform/llm/v1/embeddings"
        assert provider._url == expected_url

        provider.close()

    def test_embedding_provider_context_manager(self):
        """Test EmbeddingProvider as context manager."""
        with EmbeddingProvider(
            api_key="sk-test",
            model="text-embedding-ada-002",
            default_headers={"X-Custom": "value"},
        ) as provider:
            assert provider._client.headers["X-Custom"] == "value"
        # Client should be closed after exiting context
