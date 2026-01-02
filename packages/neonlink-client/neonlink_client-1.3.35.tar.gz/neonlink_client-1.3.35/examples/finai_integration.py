"""
FinAI Service Integration with NeonLink.

This example shows how FinAI can use NeonLink to:
1. Receive prediction requests
2. Publish prediction results
3. Communicate with other services
"""

import asyncio
import json
from typing import Any, Dict

from neonlink import (
    ConfigBuilder,
    LoggingMiddleware,
    MessageBuilder,
    MetricsMiddleware,
    NeonLinkClient,
    RetryMiddleware,
)
from messaging.v1 import messaging_pb2


class FinAIService:
    """FinAI service that communicates via NeonLink."""

    def __init__(self, neonlink_address: str = "neonlink:9090") -> None:
        self.config = (
            ConfigBuilder()
            .with_service_name("finai")
            .with_address(neonlink_address)
            .with_timeout(60.0)  # AI predictions may take longer
            .with_retry_policy(max_retries=3, initial_backoff=1.0)
            .build()
        )

        self.middlewares = [
            LoggingMiddleware(),
            RetryMiddleware(max_retries=3),
            MetricsMiddleware(),
        ]

        self.client: NeonLinkClient | None = None

    async def start(self) -> None:
        """Start the FinAI service."""
        self.client = NeonLinkClient(self.config, self.middlewares)
        await self.client.connect()
        self.client.enable_auto_reconnect()

    async def stop(self) -> None:
        """Stop the FinAI service."""
        if self.client:
            await self.client.close()

    async def run_prediction_worker(self) -> None:
        """Run the prediction worker loop."""
        if not self.client:
            raise RuntimeError("Service not started")

        request = messaging_pb2.SubscribeRequest(
            stream="finai.requests",
            consumer_group="finai-prediction-workers",
        )

        async for message in self.client.subscribe(request):
            await self._handle_prediction_request(message)

    async def _handle_prediction_request(
        self,
        message: messaging_pb2.StreamMessage,
    ) -> None:
        """Handle a single prediction request."""
        if not self.client:
            return

        try:
            # Parse request
            request_data = json.loads(message.payload)

            # Run prediction (your ML model here)
            result = await self._run_prediction(request_data)

            # Publish result to response stream
            response_request = (
                MessageBuilder()
                .with_stream("finai.responses")
                .with_message_type("PredictionResponse")
                .with_correlation_id(message.correlation_id)
                .with_json_payload(result)
                .build()
            )

            await self.client.publish(response_request)

            # ACK the original message
            await self.client.ack(
                messaging_pb2.AckRequest(
                    message_id=message.message_id,
                    stream=message.stream,
                )
            )

        except Exception as e:
            # NACK for retry
            await self.client.nack(
                messaging_pb2.NackRequest(
                    message_id=message.message_id,
                    stream=message.stream,
                    reason=str(e),
                )
            )

    async def _run_prediction(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Run the ML prediction."""
        # Simulate prediction
        await asyncio.sleep(0.5)
        return {
            "prediction": "bullish",
            "confidence": 0.87,
            "model": request.get("model_id", "default"),
        }

    async def publish_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        idempotency_key: str | None = None,
    ) -> None:
        """Publish an event to other services."""
        if not self.client:
            raise RuntimeError("Service not started")

        builder = (
            MessageBuilder()
            .with_stream("finai.events")
            .with_message_type(event_type)
            .with_json_payload(payload)
        )

        if idempotency_key:
            builder.with_idempotency_key(idempotency_key)

        await self.client.publish(builder.build())


async def main() -> None:
    """Main entry point."""
    service = FinAIService()

    try:
        await service.start()
        print("FinAI service started, listening for predictions...")
        await service.run_prediction_worker()
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        await service.stop()


if __name__ == "__main__":
    asyncio.run(main())
