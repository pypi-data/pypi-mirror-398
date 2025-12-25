"""Example: Subscribing to streams with NeonLink."""

import asyncio
import json
from typing import Any, Dict

from neonlink import ConfigBuilder, NeonLinkClient
from messaging.v1 import messaging_pb2


async def process_prediction(payload: bytes) -> Dict[str, Any]:
    """Process prediction message."""
    data = json.loads(payload)
    return {"status": "processed", "data": data}


async def main() -> None:
    config = (
        ConfigBuilder()
        .with_service_name("finai-worker")
        .with_address("neonlink:9090")
        .build()
    )

    async with NeonLinkClient(config) as client:
        # Enable auto-reconnection for long-running workers
        client.enable_auto_reconnect()

        # Subscribe to stream
        request = messaging_pb2.SubscribeRequest(
            stream="finai.predictions",
            consumer_group="finai-workers",
        )

        async for message in client.subscribe(request):
            try:
                # Process message
                print(f"Received: {message.message_id}")
                result = await process_prediction(message.payload)
                print(f"Result: {result}")

                # Acknowledge success
                await client.ack(
                    messaging_pb2.AckRequest(
                        message_id=message.message_id,
                        stream=message.stream,
                    )
                )

            except Exception as e:
                # Negative acknowledge for retry
                await client.nack(
                    messaging_pb2.NackRequest(
                        message_id=message.message_id,
                        stream=message.stream,
                        reason=str(e),
                    )
                )


if __name__ == "__main__":
    asyncio.run(main())
