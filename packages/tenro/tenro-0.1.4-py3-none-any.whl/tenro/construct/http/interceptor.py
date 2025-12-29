# Copyright 2025 Tenro.ai
# SPDX-License-Identifier: Apache-2.0

"""HTTP-level simulation using respx for SDK-agnostic LLM testing.

Provides HTTP interception for LLM API calls. The SDK's own JSON parsing
runs on simulated responses, producing real SDK types (`Message`, `TextBlock`, etc.).
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Any

import httpx
import respx

from tenro.construct.http.builders.factory import ProviderSchemaFactory
from tenro.core.context import get_current_agent_name

# Provider API endpoints
PROVIDER_ENDPOINTS: dict[str, str] = {
    "anthropic": "https://api.anthropic.com/v1/messages",
    "openai": "https://api.openai.com/v1/chat/completions",
    "gemini": "https://generativelanguage.googleapis.com/",  # Prefix for pattern match
}

# Type for call capture callback: (provider, messages, model, response_text, agent) -> None
# The agent parameter is the name of the @link_agent-decorated agent that made this call,
# or None if the call was made outside of an agent context.
CallCaptureCallback = Callable[[str, list[dict[str, Any]], str | None, str, str | None], None]


class HttpInterceptor:
    """Intercepts HTTP requests to LLM APIs using respx.

    When activated, HTTP requests to provider APIs are intercepted and
    return simulated responses. The SDK's JSON parsing still runs, so you
    get real SDK types (`Message`, `TextBlock`, `ChatCompletion`, etc.).

    Examples:
        >>> def test_llm(construct):
        ...     construct.simulate_llm(provider="anthropic", response="Hello!")
        ...     client = anthropic.Anthropic(api_key="test")
        ...     msg = client.messages.create(...)
        ...     isinstance(msg.content[0], TextBlock)  # True!
    """

    def __init__(
        self,
        on_call: CallCaptureCallback | None = None,
    ) -> None:
        """Initialize the HTTP interceptor.

        Args:
            on_call: Optional callback invoked for each intercepted request.
                Receives (`provider`, `messages`, `model`, `response_text`, `agent`).
                The `agent` parameter is the name of the @link_agent-decorated agent
                that made this call, or None if called outside of an agent context.
        """
        self._respx_router = respx.MockRouter(assert_all_called=False)
        self._routes: list[respx.Route] = []
        self._response_queue: dict[str, Iterator[tuple[dict[str, Any], str]]] = {}
        self._on_call = on_call

    def simulate_provider(
        self,
        provider: str,
        responses: str | list[str],
        **kwargs: Any,
    ) -> None:
        """Simulate a provider's API endpoint with the given responses.

        Args:
            provider: Provider name (`anthropic`, `openai`).
            responses: Single response text or list for multi-turn.
            **kwargs: Additional response metadata (model, token_usage, etc.).

        Raises:
            ValueError: If provider endpoint is not configured.
        """
        endpoint = PROVIDER_ENDPOINTS.get(provider)
        if not endpoint:
            raise ValueError(
                f"Unknown provider '{provider}'. Available: {', '.join(PROVIDER_ENDPOINTS.keys())}"
            )

        # Prevent duplicate simulation (would silently overwrite queue)
        if provider in self._response_queue:
            raise ValueError(
                f"Provider '{provider}' already simulated. "
                "Use a single simulate_llm() call for all responses"
            )

        # Normalize to list
        response_list = [responses] if isinstance(responses, str) else responses

        # Build response JSON for each response text, keeping original text
        response_pairs = [
            (self._build_response_json(provider, text, **kwargs), text) for text in response_list
        ]

        # Create iterator for multi-turn support
        self._response_queue[provider] = iter(response_pairs)

        # Set up route with side effect for sequential responses
        if provider == "gemini":
            # Pattern match for Gemini (model is in URL path)
            route = self._respx_router.post(url__startswith=endpoint).mock(
                side_effect=lambda request, p=provider: self._handle_request(request, p)
            )
        else:
            # Exact match for Anthropic/OpenAI
            route = self._respx_router.post(endpoint).mock(
                side_effect=lambda request, p=provider: self._handle_request(request, p)
            )
        self._routes.append(route)

    def _build_response_json(
        self,
        provider: str,
        content: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Build provider-specific response JSON.

        Uses existing ProviderSchemaFactory to get the correct JSON structure,
        then converts ProviderResponse to plain dict for HTTP response.
        """
        response = ProviderSchemaFactory.create_response(provider, content, **kwargs)
        # ProviderResponse wraps a dict, extract it
        return dict(response)

    def _handle_request(self, request: httpx.Request, provider: str) -> httpx.Response:
        """Handle intercepted request: parse, callback, return response."""
        try:
            response_json, response_text = next(self._response_queue[provider])
        except StopIteration:
            # Return 500 with clear error - SDK will surface this in its error
            return httpx.Response(
                500,
                json={
                    "error": {
                        "type": "test_error",
                        "message": (
                            f"No more simulated responses for provider '{provider}'. "
                            "Add more responses to simulate_llm() or check your test "
                            "makes the expected number of LLM calls."
                        ),
                    }
                },
            )

        # Parse request body for callback (protected - must not crash HTTP response)
        if self._on_call is not None:
            try:
                messages, model = self._parse_request(request, provider)
                # Get agent from span stack (AgentRun pushed by @link_agent)
                agent_name = get_current_agent_name()
                self._on_call(provider, messages, model, response_text, agent_name)
            except Exception:
                # Callback failure must not prevent HTTP response
                # Lifecycle tracking may fail, but test should still work
                pass

        return httpx.Response(200, json=response_json)

    def _parse_request(
        self, request: httpx.Request, provider: str
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Parse request body to extract messages and model."""
        import json

        try:
            body = json.loads(request.content)
        except (json.JSONDecodeError, TypeError):
            return [], None

        # Ensure body is a dict (JSON could be list, str, etc.)
        if not isinstance(body, dict):
            return [], None

        # Try both message keys (Anthropic/OpenAI use "messages", Gemini uses "contents")
        messages = body.get("messages") or body.get("contents", [])
        model = body.get("model")  # None for Gemini (model is in URL), that's OK

        return messages, model

    def start(self) -> None:
        """Start intercepting HTTP requests."""
        self._respx_router.start()

    def stop(self) -> None:
        """Stop intercepting HTTP requests and clean up routes."""
        self._respx_router.stop()
        self._respx_router.clear()
        self._routes.clear()
        self._response_queue.clear()

    def __enter__(self) -> HttpInterceptor:
        """Context manager entry - start intercepting."""
        self.start()
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: Any,
    ) -> None:
        """Context manager exit - stop intercepting."""
        self.stop()
