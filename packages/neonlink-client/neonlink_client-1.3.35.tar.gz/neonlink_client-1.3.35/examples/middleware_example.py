"""Example: Using middleware with NeonLink."""

import asyncio
import logging

from neonlink import (
    ConfigBuilder,
    LoggingMiddleware,
    MessageBuilder,
    MetricsMiddleware,
    NeonLinkClient,
    RetryMiddleware,
    TimeoutMiddleware,
)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class SimpleMetricsCollector:
    """Simple metrics collector for demonstration."""

    def __init__(self) -> None:
        self.success_count = 0
        self.failure_count = 0
        self.total_duration = 0.0

    def record_success(self, duration: float) -> None:
        self.success_count += 1
        self.total_duration += duration
        logger.info(f"Success recorded: {duration:.3f}s")

    def record_failure(self, duration: float) -> None:
        self.failure_count += 1
        self.total_duration += duration
        logger.warning(f"Failure recorded: {duration:.3f}s")

    def print_stats(self) -> None:
        total = self.success_count + self.failure_count
        if total > 0:
            avg = self.total_duration / total
            print(f"Total requests: {total}")
            print(f"Successes: {self.success_count}")
            print(f"Failures: {self.failure_count}")
            print(f"Average duration: {avg:.3f}s")


async def main() -> None:
    # Create metrics collector
    metrics = SimpleMetricsCollector()

    # Create configuration
    config = (
        ConfigBuilder()
        .with_service_name("middleware-example")
        .with_address("neonlink:9090")
        .with_timeout(30.0)
        .build()
    )

    # Create middleware chain
    middlewares = [
        LoggingMiddleware(logger),  # Log all requests
        RetryMiddleware(max_retries=3, initial_backoff=0.5),  # Retry failed requests
        TimeoutMiddleware(timeout=10.0),  # Enforce 10s timeout
        MetricsMiddleware(metrics),  # Collect metrics
    ]

    # Connect with middleware
    async with NeonLinkClient(config, middlewares=middlewares) as client:
        # Publish several messages
        for i in range(5):
            request = (
                MessageBuilder()
                .with_stream("test.middleware")
                .with_message_type("TestMessage")
                .with_json_payload({"iteration": i, "data": "test"})
                .with_idempotency_fields(f"test-{i}")
                .build()
            )

            try:
                response = await client.publish(request)
                print(f"Published message {i}: {response.message_id}")
            except Exception as e:
                print(f"Failed to publish message {i}: {e}")

    # Print metrics
    print("\n--- Metrics Summary ---")
    metrics.print_stats()


if __name__ == "__main__":
    asyncio.run(main())
