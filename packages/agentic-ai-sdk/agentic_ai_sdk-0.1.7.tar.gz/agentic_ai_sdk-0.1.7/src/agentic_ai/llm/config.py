"""LLM configuration for Deep Agent framework."""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, field_validator, model_validator

# Valid reasoning effort values
VALID_REASONING_EFFORTS = {"low", "medium", "high"}


class LLMConfig(BaseModel):
    """Runtime configuration for the LLM backend."""

    name: Optional[str] = None  # Unique identifier for this LLM configuration
    provider: Literal["openai", "azure"]
    api_key: str
    model: Optional[str] = None
    deployment: Optional[str] = None
    base_url: Optional[str] = None
    api_version: Optional[str] = None
    organization: Optional[str] = None
    temperature: Optional[float] = 0.0  # Default to 0.0 for most deterministic responses (tool calling)
    reasoning_effort: Optional[Literal["low", "medium", "high"]] = None
    default_headers: Optional[dict[str, str]] = None  # Custom headers for API requests
    extra_body: Optional[dict[str, Any]] = None  # Additional parameters to pass in the request body
    verify_ssl: bool = True  # Whether to verify SSL certificates for HTTPS requests
    enable_http_logging: bool = False  # Enable detailed HTTP request/response logging for debugging
    legacy_message_format: bool = False  # Convert new content array format to legacy string format for compatibility

    @field_validator("reasoning_effort", mode="before")
    @classmethod
    def _normalize_reasoning_effort(cls, value: Any) -> Optional[str]:
        """Normalize reasoning_effort: treat empty/invalid values as None."""
        if value is None or value == "":
            return None
        if isinstance(value, str):
            value_lower = value.lower().strip()
            if value_lower in VALID_REASONING_EFFORTS:
                return value_lower
            # Invalid value (e.g., "none") - treat as None
            return None
        return value

    @model_validator(mode="after")
    def _ensure_required_fields(self) -> "LLMConfig":
        if self.provider == "openai":
            if not self.model:
                raise ValueError("OpenAI provider requires `model` in LLMConfig.")
        elif self.provider == "azure":
            if not self.deployment:
                raise ValueError("Azure provider requires `deployment` in LLMConfig.")
            if not self.base_url:
                raise ValueError("Azure provider requires `base_url` in LLMConfig.")
            if not self.api_version:
                raise ValueError("Azure provider requires `api_version` in LLMConfig.")
        return self


__all__ = ["LLMConfig"]
