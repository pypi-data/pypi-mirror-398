"""Tests for NeonLink middleware."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from neonlink import (
    LoggingMiddleware,
    MetricsMiddleware,
    MiddlewareChain,
    RecoveryMiddleware,
    RetryMiddleware,
    TimeoutMiddleware,
)
from neonlink.errors import TimeoutError


class TestMiddlewareChain:
    """Tests for MiddlewareChain."""

    @pytest.mark.asyncio
    async def test_empty_chain(self):
        """Empty chain should execute handler directly."""
        chain = MiddlewareChain([])
        handler = AsyncMock(return_value="result")

        result = await chain.execute(handler)

        assert result == "result"
        handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_single_middleware(self):
        """Single middleware should wrap handler."""
        calls = []

        class TrackingMiddleware:
            async def __call__(self, handler):
                calls.append("before")
                result = await handler()
                calls.append("after")
                return result

        chain = MiddlewareChain([TrackingMiddleware()])
        handler = AsyncMock(return_value="result")

        result = await chain.execute(handler)

        assert result == "result"
        assert calls == ["before", "after"]

    @pytest.mark.asyncio
    async def test_middleware_order(self):
        """Middlewares should execute in order (first to last)."""
        calls = []

        class NumberedMiddleware:
            def __init__(self, num):
                self.num = num

            async def __call__(self, handler):
                calls.append(f"before-{self.num}")
                result = await handler()
                calls.append(f"after-{self.num}")
                return result

        chain = MiddlewareChain([
            NumberedMiddleware(1),
            NumberedMiddleware(2),
            NumberedMiddleware(3),
        ])
        handler = AsyncMock(return_value="result")

        await chain.execute(handler)

        assert calls == [
            "before-1", "before-2", "before-3",
            "after-3", "after-2", "after-1",
        ]


class TestLoggingMiddleware:
    """Tests for LoggingMiddleware."""

    @pytest.mark.asyncio
    async def test_logs_success(self):
        logger = MagicMock()
        middleware = LoggingMiddleware(logger)
        handler = AsyncMock(return_value="result")

        result = await middleware(handler)

        assert result == "result"
        logger.debug.assert_called_once()
        assert "completed" in logger.debug.call_args[0][0]

    @pytest.mark.asyncio
    async def test_logs_failure(self):
        logger = MagicMock()
        middleware = LoggingMiddleware(logger)
        handler = AsyncMock(side_effect=ValueError("test error"))

        with pytest.raises(ValueError):
            await middleware(handler)

        logger.error.assert_called_once()
        assert "failed" in logger.error.call_args[0][0]


class TestRetryMiddleware:
    """Tests for RetryMiddleware."""

    @pytest.mark.asyncio
    async def test_success_no_retry(self):
        middleware = RetryMiddleware(max_retries=3)
        handler = AsyncMock(return_value="result")

        result = await middleware(handler)

        assert result == "result"
        assert handler.call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        middleware = RetryMiddleware(max_retries=3, initial_backoff=0.01)
        handler = AsyncMock(side_effect=[ValueError("fail"), "result"])

        result = await middleware(handler)

        assert result == "result"
        assert handler.call_count == 2

    @pytest.mark.asyncio
    async def test_exhausted_retries(self):
        middleware = RetryMiddleware(max_retries=2, initial_backoff=0.01)
        handler = AsyncMock(side_effect=ValueError("always fails"))

        with pytest.raises(ValueError, match="always fails"):
            await middleware(handler)

        assert handler.call_count == 3  # 1 initial + 2 retries


class TestTimeoutMiddleware:
    """Tests for TimeoutMiddleware."""

    @pytest.mark.asyncio
    async def test_success_within_timeout(self):
        middleware = TimeoutMiddleware(timeout=1.0)
        handler = AsyncMock(return_value="result")

        result = await middleware(handler)

        assert result == "result"

    @pytest.mark.asyncio
    async def test_timeout_exceeded(self):
        middleware = TimeoutMiddleware(timeout=0.01)

        async def slow_handler():
            await asyncio.sleep(1.0)
            return "result"

        with pytest.raises(TimeoutError, match="timed out"):
            await middleware(slow_handler)


class TestRecoveryMiddleware:
    """Tests for RecoveryMiddleware."""

    @pytest.mark.asyncio
    async def test_success_passthrough(self):
        middleware = RecoveryMiddleware()
        handler = AsyncMock(return_value="result")

        result = await middleware(handler)

        assert result == "result"

    @pytest.mark.asyncio
    async def test_exception_logged_and_reraised(self):
        middleware = RecoveryMiddleware()
        handler = AsyncMock(side_effect=ValueError("test error"))

        with pytest.raises(ValueError):
            await middleware(handler)


class TestMetricsMiddleware:
    """Tests for MetricsMiddleware."""

    @pytest.mark.asyncio
    async def test_records_success(self):
        collector = MagicMock()
        middleware = MetricsMiddleware(collector)
        handler = AsyncMock(return_value="result")

        result = await middleware(handler)

        assert result == "result"
        collector.record_success.assert_called_once()
        collector.record_failure.assert_not_called()

    @pytest.mark.asyncio
    async def test_records_failure(self):
        collector = MagicMock()
        middleware = MetricsMiddleware(collector)
        handler = AsyncMock(side_effect=ValueError("error"))

        with pytest.raises(ValueError):
            await middleware(handler)

        collector.record_failure.assert_called_once()
        collector.record_success.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_collector(self):
        """Should work without a collector."""
        middleware = MetricsMiddleware()
        handler = AsyncMock(return_value="result")

        result = await middleware(handler)

        assert result == "result"
