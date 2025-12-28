"""LLM client creation and configuration utilities for Deep Agent framework."""
from __future__ import annotations

import logging
from typing import Any, Optional

import httpx
from agent_framework.openai import OpenAIChatClient
from openai import AsyncOpenAI, AsyncAzureOpenAI

from .config import LLMConfig

LOGGER = logging.getLogger("agentic_ai.llm_client")


def _create_http_event_hooks(
    llm_name: str, 
    enable_logging: bool = True, 
    enable_legacy_format: bool = False,
    inject_extra_body: dict[str, Any] | None = None
):
    """Create httpx event hooks for logging HTTP requests and responses, and optionally converting to legacy format.
    
    Args:
        llm_name: Name of the LLM for logging purposes.
        enable_logging: Whether to log HTTP requests and responses.
        enable_legacy_format: Whether to convert content arrays to legacy string format.
        inject_extra_body: Extra body parameters to inject into request (e.g., enable_thinking for reasoning models).
    """
    import json
    
    async def log_and_transform_request(request: httpx.Request):
        # Read and potentially modify request body
        body_modified = False
        
        try:
            # Ensure content is loaded
            await request.aread()
            
            if request.content and (enable_legacy_format or inject_extra_body):
                # Parse JSON body
                try:
                    body_data = json.loads(request.content.decode('utf-8'))
                    
                    # Check if this is a chat completions request with messages
                    if "messages" in body_data and isinstance(body_data["messages"], list):
                        # Transform each message's content from array to string
                        for msg in body_data["messages"]:
                            if "content" in msg and isinstance(msg["content"], list):
                                # Extract text from content array and merge into single string
                                text_parts = []
                                for part in msg["content"]:
                                    if isinstance(part, dict) and part.get("type") == "text" and "text" in part:
                                        text_parts.append(part["text"])
                                
                                if text_parts:
                                    # Replace content array with merged string
                                    msg["content"] = "".join(text_parts)
                                    body_modified = True
                        
                        # Inject extra_body parameters if provided
                        if inject_extra_body and isinstance(inject_extra_body, dict):
                            for key, value in inject_extra_body.items():
                                if key not in body_data:  # Don't override existing parameters
                                    body_data[key] = value
                                    body_modified = True
                            if body_modified:
                                LOGGER.debug(
                                    "LLM [%s]: Injected extra_body parameters: %s",
                                    llm_name,
                                    list(inject_extra_body.keys())
                                )
                        
                        if body_modified:
                            # Calculate original length before modification
                            original_length = len(request.content)
                            
                            # Properly update request with modified body
                            new_body_bytes = json.dumps(body_data).encode('utf-8')
                            new_length = len(new_body_bytes)
                            
                            # Update both _content and stream to ensure consistency
                            request._content = new_body_bytes
                            # Recreate the stream with new content
                            import httpx
                            request.stream = httpx.ByteStream(new_body_bytes)
                            
                            # Update Content-Length header
                            request.headers["content-length"] = str(new_length)
                            
                            if enable_legacy_format and not inject_extra_body:
                                LOGGER.debug(
                                    "LLM [%s]: Converted message content arrays to legacy string format (original: %d bytes, new: %d bytes, delta: %+d)",
                                    llm_name,
                                    original_length,
                                    new_length,
                                    new_length - original_length
                                )
                except (json.JSONDecodeError, AttributeError) as e:
                    LOGGER.debug("Could not parse/modify request body: %s", e)
        except Exception as e:
            LOGGER.debug("Error processing request body: %s", e)
        
        # Log request if enabled
        if enable_logging:
            masked_headers = dict(request.headers)
            if "authorization" in masked_headers:
                masked_headers["authorization"] = "Bearer ***masked***"
            if "api-key" in masked_headers:
                masked_headers["api-key"] = "***masked***"

            body_preview = ""
            try:
                if request.content:
                    body_text = request.content.decode('utf-8', errors='replace')
                    body_preview = body_text[:5000] + ("..." if len(body_text) > 5000 else "")
                else:
                    body_preview = "<empty>"
            except Exception as e:
                body_preview = f"<unreadable: {e}>"

            LOGGER.debug(
                "llm_http_request",
                extra={
                    "event": "llm.http.request",
                    "llm_name": llm_name,
                    "method": request.method.decode() if isinstance(request.method, bytes) else request.method,
                    "url": str(request.url),
                    "headers": masked_headers,
                    "body_preview": body_preview,
                },
            )
    
    async def log_response(response: httpx.Response):
        if not enable_logging:
            return
            
        # For streaming responses, we can only log headers and status
        # Reading the body would consume the stream and break streaming
        is_streaming = False
        content_type = response.headers.get("content-type", "")
        
        # Check if this is a streaming response
        if "text/event-stream" in content_type or response.headers.get("transfer-encoding") == "chunked":
            is_streaming = True
        
        body_preview = ""
        if is_streaming:
            # For streaming responses, just log that it's streaming
            body_preview = "<streaming response - body not captured to preserve streaming>"
        else:
            try:
                # Only read body for non-streaming responses
                await response.aread()
                body_text = response.text
                body_preview = body_text[:5000] + ("..." if len(body_text) > 5000 else "")
            except Exception as e:
                body_preview = f"<unreadable: {e}>"
        
        # HTTP response logging is always DEBUG level (detailed diagnostic info)
        LOGGER.debug(
            "llm_http_response",
            extra={
                "event": "llm.http.response",
                "llm_name": llm_name,
                "method": response.request.method.decode()
                if isinstance(response.request.method, bytes)
                else response.request.method,
                "url": str(response.request.url),
                "status_code": response.status_code,
                "is_streaming": is_streaming,
                "body_preview": body_preview,
            },
        )
    
    return {
        "request": [log_and_transform_request],
        "response": [log_response],
    }


def _create_logging_transport(base_transport, llm_name: str):
    """Wrap httpx transport to log connection errors with details."""
    from httpx import AsyncBaseTransport, Request, Response
    
    class LoggingTransport(AsyncBaseTransport):
        """Wrapper around httpx transport to log connection errors."""
        
        def __init__(self, base_transport: AsyncBaseTransport):
            self._base_transport = base_transport
        
        async def handle_async_request(self, request: Request) -> Response:
            try:
                return await self._base_transport.handle_async_request(request)
            except Exception as e:
                # Log detailed error information
                error_type = type(e).__name__
                error_msg = str(e)
                
                # Extract root cause if available
                cause_info = ""
                if hasattr(e, '__cause__') and e.__cause__:
                    cause = e.__cause__
                    cause_info = f" | Root Cause: {type(cause).__name__}: {cause}"
                
                LOGGER.error(
                    "llm_http_error",
                    extra={
                        "event": "llm.http.error",
                        "llm_name": llm_name,
                        "method": request.method.decode() if isinstance(request.method, bytes) else request.method,
                        "url": str(request.url),
                        "error_type": error_type,
                        "error_message": error_msg,
                        "root_cause": cause_info.strip(" |") if cause_info else None,
                    },
                    exc_info=True,
                )
                
                # Re-raise the exception
                raise
        
        async def aclose(self) -> None:
            """Close the underlying transport."""
            await self._base_transport.aclose()
    
    return LoggingTransport(base_transport)


def create_chat_client(llm_config: LLMConfig, override_model: Optional[str] = None):
    """
    Instantiate the appropriate chat client based on configuration.
    `override_model` acts as the OpenAI model id or Azure deployment override.
    
    Note: max_iterations should be set by the caller (agent_builder) after client creation.
    """
    model_id = override_model or llm_config.model

    # Create httpx client with SSL verification settings and optional HTTP logging/transformation
    # Always use logging transport to capture connection errors
    llm_name = llm_config.name or "unnamed"
    needs_custom_client = not llm_config.verify_ssl or llm_config.enable_http_logging or llm_config.legacy_message_format or llm_config.extra_body
    
    if needs_custom_client:
        if not llm_config.verify_ssl:
            LOGGER.warning("SSL certificate verification is disabled for LLM '%s'", llm_name)
        if llm_config.enable_http_logging:
            LOGGER.debug("HTTP request/response logging is enabled for LLM '%s'", llm_name)
        if llm_config.legacy_message_format:
            LOGGER.debug("Legacy message format conversion enabled for LLM '%s'", llm_name)
        if llm_config.extra_body:
            LOGGER.debug("Extra body injection enabled for LLM '%s': %s", llm_name, list(llm_config.extra_body.keys()))
        
        # Create custom httpx client with event hooks if HTTP logging, legacy format, or extra_body is enabled
        event_hooks = None
        if llm_config.enable_http_logging or llm_config.legacy_message_format or llm_config.extra_body:
            event_hooks = _create_http_event_hooks(
                llm_name,
                enable_logging=llm_config.enable_http_logging,
                enable_legacy_format=llm_config.legacy_message_format,
                inject_extra_body=llm_config.extra_body
            )
        
        # Wrap transport to log connection errors with details
        base_transport = httpx.AsyncHTTPTransport(verify=llm_config.verify_ssl)
        logging_transport = _create_logging_transport(base_transport, llm_name)
        http_client = httpx.AsyncClient(transport=logging_transport, event_hooks=event_hooks)
    else:
        # Even with default settings, wrap transport for connection error logging
        base_transport = httpx.AsyncHTTPTransport(verify=True)
        logging_transport = _create_logging_transport(base_transport, llm_name)
        http_client = httpx.AsyncClient(transport=logging_transport)

    if llm_config.provider == "azure":
        from agent_framework.azure import AzureOpenAIChatClient

        deployment_name = override_model or llm_config.deployment
        
        # Create AsyncAzureOpenAI client with custom http_client if needed
        async_client = None
        if http_client is not None and llm_config.base_url and llm_config.api_version:
            async_client = AsyncAzureOpenAI(
                api_key=llm_config.api_key,
                azure_deployment=deployment_name,
                azure_endpoint=llm_config.base_url,
                api_version=llm_config.api_version,
                default_headers=llm_config.default_headers,
                http_client=http_client,
            )
        
        client = AzureOpenAIChatClient(
            api_key=llm_config.api_key,
            deployment_name=deployment_name,
            model=model_id,
            base_url=llm_config.base_url,
            api_version=llm_config.api_version,
            default_headers=llm_config.default_headers,
            async_client=async_client,
        )
        return client

    # Create AsyncOpenAI client with custom http_client if needed
    async_client = None
    if http_client is not None:
        async_client = AsyncOpenAI(
            api_key=llm_config.api_key,
            base_url=llm_config.base_url,
            organization=llm_config.organization,
            default_headers=llm_config.default_headers,
            http_client=http_client,
        )

    client = OpenAIChatClient(
        model_id=model_id,
        api_key=llm_config.api_key,
        base_url=llm_config.base_url,
        org_id=llm_config.organization,
        default_headers=llm_config.default_headers,
        async_client=async_client,
    )
    return client


def resolve_temperature(
    llm_config: LLMConfig,
    *,
    requested: Optional[float] = None,
    model_override: Optional[str] = None,
) -> Optional[float]:
    """
    Determine a safe temperature value for the configured model.

    Some OpenAI GPT-5 family models only accept the service default temperature (1.0).
    For those models we ignore custom values and fall back to the service default.
    """
    value = requested if requested is not None else llm_config.temperature
    if value is None:
        return None

    model_name = (model_override or llm_config.model or "").lower()
    if model_name.startswith("gpt-5") and llm_config.provider == "openai":
        if abs(value - 1.0) > 1e-6:
            LOGGER.warning(
                "Model %s only supports the default temperature; ignoring configured value %s.",
                model_name,
                value,
            )
            return None
    return value


def build_agent_chat_options(
    llm_config: LLMConfig,
    *,
    model_override: Optional[str] = None,
) -> dict[str, Any]:
    """Build chat options for agent initialization (e.g., reasoning_effort, extra_body)."""
    options: dict[str, Any] = {}
    if llm_config.reasoning_effort:
        options["reasoning_effort"] = llm_config.reasoning_effort
    if llm_config.extra_body:
        options["extra_body"] = llm_config.extra_body
    return options


def build_chat_options(
    llm_config: LLMConfig,
    *,
    requested_temperature: Optional[float] = None,
    max_output_tokens: Optional[int] = None,
    model_override: Optional[str] = None,
) -> dict[str, Any]:
    """
    Construct chat completion keyword arguments compatible with the selected model.

    GPT-5 style models expect ``max_completion_tokens`` instead of ``max_tokens``.
    """
    options: dict[str, Any] = build_agent_chat_options(
        llm_config,
        model_override=model_override,
    )
    temperature = resolve_temperature(llm_config, requested=requested_temperature, model_override=model_override)
    if temperature is not None:
        options["temperature"] = temperature

    if max_output_tokens is not None:
        model_name = (model_override or llm_config.model or "").lower()
        if llm_config.provider == "openai" and model_name.startswith("gpt-5"):
            options["max_completion_tokens"] = max_output_tokens
        else:
            options["max_tokens"] = max_output_tokens

    return options


__all__ = [
    "build_agent_chat_options",
    "build_chat_options",
    "create_chat_client",
    "resolve_temperature",
]
