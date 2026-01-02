"""Example: Basic message publishing with NeonLink."""

import asyncio

from neonlink import ConfigBuilder, MessageBuilder, NeonLinkClient


async def main() -> None:
    # Create configuration
    config = (
        ConfigBuilder()
        .with_service_name("finai-service")
        .with_address("neonlink:9090")
        .with_timeout(30.0)
        .build()
    )

    # Connect and publish
    async with NeonLinkClient(config) as client:
        # Build message with idempotency
        request = (
            MessageBuilder()
            .with_stream("finai.predictions")
            .with_message_type("PredictionRequest")
            .with_json_payload(
                {
                    "model_id": "gpt-4-turbo",
                    "input": "Analyze this financial data...",
                    "user_id": "user-123",
                }
            )
            .with_idempotency_fields("user-123", "prediction-001")
            .build()
        )

        response = await client.publish(request)
        print(f"Published message: {response.message_id}")


if __name__ == "__main__":
    asyncio.run(main())
