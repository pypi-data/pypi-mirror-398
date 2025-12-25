"""TokenTally client for tracking AI API usage."""

import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Generator

import httpx

from tokentally._version import __version__
from tokentally.types import UsageData, UsageResponse


class TokenTallyError(Exception):
    """Base exception for TokenTally errors."""

    pass


class RateLimitError(TokenTallyError):
    """Raised when rate limit is exceeded."""

    pass


class AuthenticationError(TokenTallyError):
    """Raised when authentication fails."""

    pass


class TokenTally:
    """Client for tracking AI API usage with TokenTally.

    Example:
        >>> from tokentally import TokenTally
        >>> tt = TokenTally(api_key="your_api_key")
        >>>
        >>> # Track usage manually
        >>> tt.track(
        ...     tokens_in=100,
        ...     tokens_out=200,
        ...     model="claude-3-sonnet-20240229",
        ... )
        >>>
        >>> # Or use context manager for automatic timing
        >>> with tt.track_usage(model="claude-3-sonnet", metadata={"feature": "chat"}):
        ...     response = anthropic.messages.create(...)
    """

    DEFAULT_BASE_URL = "https://api.tokentally.io"

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """Initialize TokenTally client.

        Args:
            api_key: Your TokenTally API key (starts with 'tt_').
            base_url: Optional custom API base URL.
            timeout: Request timeout in seconds.
        """
        if not api_key or not api_key.startswith("tt_"):
            raise ValueError("Invalid API key. Must start with 'tt_'")

        self.api_key = api_key
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout

        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "X-API-Key": self.api_key,
                "Content-Type": "application/json",
                "User-Agent": f"tokentally-python/{__version__}",
            },
            timeout=timeout,
        )

    def __del__(self):
        """Cleanup HTTP client."""
        if hasattr(self, "_client"):
            self._client.close()

    def track(
        self,
        tokens_in: int,
        tokens_out: int,
        model: str,
        provider: str = "anthropic",
        runtime_ms: Optional[int] = None,
        stop_reason: Optional[str] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UsageResponse:
        """Record usage data.

        Args:
            tokens_in: Number of input tokens.
            tokens_out: Number of output tokens.
            model: The model name (e.g., 'claude-3-sonnet-20240229').
            provider: The AI provider ('anthropic', 'openai', etc.).
            runtime_ms: Optional runtime in milliseconds.
            stop_reason: Optional stop reason from API.
            error_message: Optional error message if request failed.
            metadata: Optional custom metadata dict.

        Returns:
            UsageResponse with record ID and calculated cost.

        Raises:
            RateLimitError: If rate limit is exceeded.
            AuthenticationError: If API key is invalid.
            TokenTallyError: For other errors.
        """
        usage = UsageData(
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            model=model,
            provider=provider,
            runtime_ms=runtime_ms,
            stop_reason=stop_reason,
            error_message=error_message,
            metadata=metadata or {},
            timestamp=datetime.now(timezone.utc),
        )

        return self._send_usage(usage)

    def track_usage_data(self, usage: UsageData) -> UsageResponse:
        """Record usage from a UsageData object.

        Args:
            usage: UsageData object with usage details.

        Returns:
            UsageResponse with record ID and calculated cost.
        """
        if usage.timestamp is None:
            usage.timestamp = datetime.now(timezone.utc)
        return self._send_usage(usage)

    @contextmanager
    def track_usage(
        self,
        model: str,
        provider: str = "anthropic",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Generator["UsageContext", None, None]:
        """Context manager for tracking usage with automatic timing.

        Example:
            >>> with tt.track_usage(model="claude-3-sonnet", metadata={"feature": "chat"}) as ctx:
            ...     response = anthropic.messages.create(...)
            ...     ctx.set_usage(
            ...         tokens_in=response.usage.input_tokens,
            ...         tokens_out=response.usage.output_tokens,
            ...         stop_reason=response.stop_reason,
            ...     )

        Args:
            model: The model name.
            provider: The AI provider.
            metadata: Optional custom metadata.

        Yields:
            UsageContext for setting usage details.
        """
        ctx = UsageContext(
            client=self,
            model=model,
            provider=provider,
            metadata=metadata or {},
        )

        start_time = time.perf_counter()

        try:
            yield ctx
        except Exception as e:
            ctx.error_message = str(e)
            raise
        finally:
            end_time = time.perf_counter()
            ctx.runtime_ms = int((end_time - start_time) * 1000)

            # Only send if usage was set
            if ctx.tokens_in is not None and ctx.tokens_out is not None:
                ctx._send()

    def _send_usage(self, usage: UsageData) -> UsageResponse:
        """Send usage data to API."""
        try:
            response = self._client.post("/api/usage", json=usage.to_dict())

            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            if response.status_code == 429:
                data = response.json()
                raise RateLimitError(data.get("error", "Rate limit exceeded"))

            response.raise_for_status()
            return UsageResponse.from_dict(response.json())

        except httpx.HTTPError as e:
            raise TokenTallyError(f"Request failed: {e}") from e


class UsageContext:
    """Context for tracking usage within a context manager."""

    def __init__(
        self,
        client: TokenTally,
        model: str,
        provider: str,
        metadata: Dict[str, Any],
    ):
        self._client = client
        self.model = model
        self.provider = provider
        self.metadata = metadata

        self.tokens_in: Optional[int] = None
        self.tokens_out: Optional[int] = None
        self.stop_reason: Optional[str] = None
        self.error_message: Optional[str] = None
        self.runtime_ms: Optional[int] = None

        self._response: Optional[UsageResponse] = None

    def set_usage(
        self,
        tokens_in: int,
        tokens_out: int,
        stop_reason: Optional[str] = None,
    ) -> None:
        """Set usage data from API response.

        Args:
            tokens_in: Number of input tokens.
            tokens_out: Number of output tokens.
            stop_reason: Optional stop reason.
        """
        self.tokens_in = tokens_in
        self.tokens_out = tokens_out
        self.stop_reason = stop_reason

    @property
    def response(self) -> Optional[UsageResponse]:
        """Get the usage response after context exits."""
        return self._response

    def _send(self) -> None:
        """Send usage data to API."""
        if self.tokens_in is None or self.tokens_out is None:
            return

        usage = UsageData(
            tokens_in=self.tokens_in,
            tokens_out=self.tokens_out,
            model=self.model,
            provider=self.provider,
            runtime_ms=self.runtime_ms,
            stop_reason=self.stop_reason,
            error_message=self.error_message,
            metadata=self.metadata,
            timestamp=datetime.now(timezone.utc),
        )

        self._response = self._client._send_usage(usage)
