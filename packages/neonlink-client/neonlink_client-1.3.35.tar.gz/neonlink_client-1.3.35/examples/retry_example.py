"""Example: Retry behavior with NeonLink."""

import asyncio

from neonlink import (
    ConfigBuilder,
    MessageBuilder,
    NeonLinkClient,
    RetryMiddleware,
)


async def main() -> None:
    # Create configuration with custom retry policy
    config = (
        ConfigBuilder()
        .with_service_name("retry-example")
        .with_address("neonlink:9090")
        .with_retry_policy(
            max_retries=5,
            initial_backoff=0.5,
            max_backoff=10.0,
            backoff_multiplier=2.0,
        )
        .build()
    )

    # Use RetryMiddleware for application-level retries
    middlewares = [
        RetryMiddleware(
            max_retries=3,
            initial_backoff=0.1,
            max_backoff=5.0,
            backoff_multiplier=2.0,
        ),
    ]

    async with NeonLinkClient(config, middlewares=middlewares) as client:
        # This will retry up to 3 times if it fails
        request = (
            MessageBuilder()
            .with_stream("test.retry")
            .with_message_type("RetryTest")
            .with_json_payload({"test": "data"})
            .build()
        )

        try:
            response = await client.publish(request)
            print(f"Published successfully: {response.message_id}")
        except Exception as e:
            print(f"Failed after all retries: {e}")


if __name__ == "__main__":
    asyncio.run(main())
