"""Retry logic with exponential backoff for flaky tests."""

import asyncio
import random
import logging
from typing import Callable, TypeVar, Optional, Tuple, List, Any, Awaitable
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Exceptions that are safe to retry (transient errors)
RETRYABLE_EXCEPTIONS = (
    httpx.TimeoutException,
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.PoolTimeout,
)


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_retries: int = 0  # 0 = no retries (default)
    base_delay: float = 1.0  # seconds
    max_delay: float = 30.0  # seconds
    exponential: bool = True
    jitter: bool = True

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number (0-indexed)."""
        if self.exponential:
            delay = min(self.base_delay * (2**attempt), self.max_delay)
        else:
            delay = self.base_delay

        if self.jitter:
            # Add 0-50% random jitter to prevent thundering herd
            delay = delay * (1 + random.random() * 0.5)

        return delay


@dataclass
class RetryResult:
    """Result of a retry operation."""

    success: bool
    result: Any = None  # Use Any instead of T for dataclass compatibility
    exception: Optional[Exception] = None
    attempts: int = 0
    total_delay: float = 0.0
    retry_history: List[Tuple[int, str, float]] = field(default_factory=list)


def is_retryable_exception(exc: Exception) -> bool:
    """Check if an exception is retryable."""
    # Retryable HTTP exceptions
    if isinstance(exc, RETRYABLE_EXCEPTIONS):
        return True

    # HTTP 5xx errors are retryable
    if isinstance(exc, httpx.HTTPStatusError):
        return 500 <= exc.response.status_code < 600

    return False


async def with_retry(
    fn: Callable[[], Awaitable[T]],
    config: RetryConfig,
    on_retry: Optional[Callable[[int, float, Exception], None]] = None,
) -> RetryResult:
    """
    Execute async function with retry logic.

    Args:
        fn: Async function to execute
        config: Retry configuration
        on_retry: Optional callback called before each retry (attempt, delay, exception)

    Returns:
        RetryResult with success status, result/exception, and retry history
    """
    result = RetryResult(success=False, attempts=0)
    last_exception: Optional[Exception] = None

    for attempt in range(config.max_retries + 1):
        result.attempts = attempt + 1

        try:
            value = await fn()
            result.success = True
            result.result = value
            return result

        except Exception as e:
            last_exception = e

            # Check if we should retry
            if attempt >= config.max_retries:
                # No more retries
                result.exception = e
                return result

            if not is_retryable_exception(e):
                # Non-retryable exception
                logger.debug(f"Non-retryable exception: {type(e).__name__}: {e}")
                result.exception = e
                return result

            # Calculate delay and retry
            delay = config.calculate_delay(attempt)
            result.total_delay += delay
            result.retry_history.append((attempt + 1, type(e).__name__, delay))

            logger.info(
                f"Retry {attempt + 1}/{config.max_retries} after {delay:.2f}s "
                f"(error: {type(e).__name__}: {e})"
            )

            if on_retry:
                on_retry(attempt + 1, delay, e)

            await asyncio.sleep(delay)

    # Should not reach here, but just in case
    result.exception = last_exception
    return result


class RetryableAdapter:
    """Wrapper that adds retry logic to an adapter."""

    def __init__(self, adapter: Any, config: RetryConfig):
        """
        Initialize retryable adapter wrapper.

        Args:
            adapter: The underlying adapter to wrap
            config: Retry configuration
        """
        self.adapter = adapter
        self.config = config
        self._retry_stats: dict[str, Any] = {"total_retries": 0, "total_delay": 0.0}

    async def execute(self, query: str, **kwargs: Any) -> Any:
        """Execute with retry logic."""

        async def _execute() -> Any:
            return await self.adapter.execute(query, **kwargs)

        def _on_retry(attempt: int, delay: float, exc: Exception) -> None:
            self._retry_stats["total_retries"] += 1
            self._retry_stats["total_delay"] += delay

        result = await with_retry(_execute, self.config, on_retry=_on_retry)

        if result.success:
            return result.result
        else:
            if result.exception is not None:
                raise result.exception
            raise RuntimeError("Retry failed without exception")

    async def health_check(self) -> bool:
        """Delegate health check to underlying adapter."""
        return await self.adapter.health_check()

    @property
    def retry_stats(self) -> dict[str, Any]:
        """Get retry statistics."""
        return self._retry_stats.copy()
