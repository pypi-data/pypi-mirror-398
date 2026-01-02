"""Tests for NeonLink client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from neonlink import ConfigBuilder, MessageBuilder, NeonLinkClient
from neonlink.errors import ConnectionError


class TestNeonLinkClient:
    """Tests for NeonLinkClient."""

    def test_init(self, config):
        client = NeonLinkClient(config)
        assert client.config == config
        assert client._channel is None
        assert client._stub is None
        assert client._connected is False

    def test_init_with_middlewares(self, config):
        middlewares = [MagicMock(), MagicMock()]
        client = NeonLinkClient(config, middlewares=middlewares)
        assert len(client._middleware_chain.middlewares) == 2

    @pytest.mark.asyncio
    async def test_publish_not_connected(self, config):
        client = NeonLinkClient(config)

        with pytest.raises(ConnectionError, match="Not connected"):
            await client.publish(MagicMock())

    @pytest.mark.asyncio
    async def test_publish_success(self, mock_client):
        mock_response = MagicMock()
        mock_response.message_id = "msg-123"
        mock_client._stub.Publish = AsyncMock(return_value=mock_response)

        request = MagicMock()
        response = await mock_client.publish(request)

        assert response.message_id == "msg-123"
        mock_client._stub.Publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_ack_not_connected(self, config):
        client = NeonLinkClient(config)

        with pytest.raises(ConnectionError, match="Not connected"):
            await client.ack(MagicMock())

    @pytest.mark.asyncio
    async def test_ack_success(self, mock_client):
        mock_response = MagicMock()
        mock_client._stub.AcknowledgeMessage = AsyncMock(return_value=mock_response)

        request = MagicMock()
        response = await mock_client.ack(request)

        assert response == mock_response
        mock_client._stub.AcknowledgeMessage.assert_called_once()

    @pytest.mark.asyncio
    async def test_nack_not_connected(self, config):
        client = NeonLinkClient(config)

        with pytest.raises(ConnectionError, match="Not connected"):
            await client.nack(MagicMock())

    @pytest.mark.asyncio
    async def test_nack_success(self, mock_client):
        mock_response = MagicMock()
        mock_client._stub.NegativeAcknowledge = AsyncMock(return_value=mock_response)

        request = MagicMock()
        response = await mock_client.nack(request)

        assert response == mock_response
        mock_client._stub.NegativeAcknowledge.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_stream_health_not_connected(self, config):
        client = NeonLinkClient(config)

        with pytest.raises(ConnectionError, match="Not connected"):
            await client.get_stream_health("test-stream")

    @pytest.mark.asyncio
    async def test_health_check_not_connected(self, config):
        client = NeonLinkClient(config)
        result = await client.health_check()
        assert result is False

    @pytest.mark.asyncio
    async def test_context_manager(self, config):
        with patch.object(NeonLinkClient, "connect", new_callable=AsyncMock) as mock_connect:
            with patch.object(NeonLinkClient, "close", new_callable=AsyncMock) as mock_close:
                async with NeonLinkClient(config) as client:
                    assert client is not None

                mock_connect.assert_called_once()
                mock_close.assert_called_once()

    def test_is_connected_property(self, config):
        client = NeonLinkClient(config)
        assert client.is_connected is False

        client._connected = True
        assert client.is_connected is True

    def test_get_metadata(self, config):
        client = NeonLinkClient(config)
        metadata = client._get_metadata()

        assert ("x-service-name", "test-service") in metadata

    def test_get_metadata_with_custom(self):
        config = (
            ConfigBuilder()
            .with_service_name("test-service")
            .with_metadata("x-custom", "value")
            .build()
        )
        client = NeonLinkClient(config)
        metadata = client._get_metadata()

        assert ("x-service-name", "test-service") in metadata
        assert ("x-custom", "value") in metadata

    def test_enable_disable_auto_reconnect(self, config):
        client = NeonLinkClient(config)

        assert client._reconnect_task is None

        # Can't enable without event loop in sync context
        # Just verify the methods exist and don't crash
        client.disable_auto_reconnect()
        assert client._reconnect_task is None


class TestNeonLinkClientConnection:
    """Tests for NeonLink client connection handling."""

    @pytest.mark.asyncio
    async def test_connect_insecure(self, config):
        with patch("grpc.aio.insecure_channel") as mock_channel:
            mock_channel.return_value = MagicMock()
            
            # Patch the import location in the client module 
            with patch.dict("sys.modules", {"messaging.v1.messaging_pb2_grpc": MagicMock()}):
                import sys
                sys.modules["messaging.v1.messaging_pb2_grpc"].MessageBrokerStub = MagicMock()

                client = NeonLinkClient(config)
                await client.connect()

                assert client._connected is True
                # Verify channel was called with address and options
                mock_channel.assert_called_once()
                call_args = mock_channel.call_args
                assert call_args[0][0] == config.address

    @pytest.mark.asyncio
    async def test_close(self, mock_client):
        mock_client._channel.close = AsyncMock()

        await mock_client.close()

        assert mock_client._connected is False
        mock_client._channel.close.assert_called_once()


class TestNeonLinkClientTLS:
    """Tests for NeonLink client TLS handling."""

    def test_create_credentials_no_tls_config(self, config):
        client = NeonLinkClient(config)

        with pytest.raises(ValueError, match="TLS config required"):
            client._create_credentials()

    def test_create_credentials_with_ca_only(self, config, tmp_path):
        """Test TLS with only CA certificate."""
        ca_file = tmp_path / "ca.pem"
        ca_file.write_bytes(b"fake-ca-cert")

        config_with_tls = (
            ConfigBuilder()
            .with_service_name("test-service")
            .with_address("localhost:9090")
            .with_tls(ca_path=str(ca_file))
            .build()
        )

        client = NeonLinkClient(config_with_tls)

        with patch("grpc.ssl_channel_credentials") as mock_ssl:
            mock_ssl.return_value = MagicMock()
            creds = client._create_credentials()

            mock_ssl.assert_called_once()
            call_args = mock_ssl.call_args
            assert call_args.kwargs["root_certificates"] == b"fake-ca-cert"
            assert call_args.kwargs["private_key"] is None
            assert call_args.kwargs["certificate_chain"] is None

    def test_create_credentials_mtls(self, config, tmp_path):
        """Test mTLS with all certificates."""
        ca_file = tmp_path / "ca.pem"
        cert_file = tmp_path / "cert.pem"
        key_file = tmp_path / "key.pem"

        ca_file.write_bytes(b"fake-ca-cert")
        cert_file.write_bytes(b"fake-client-cert")
        key_file.write_bytes(b"fake-client-key")

        config_with_tls = (
            ConfigBuilder()
            .with_service_name("test-service")
            .with_address("localhost:9090")
            .with_tls(
                cert_path=str(cert_file),
                key_path=str(key_file),
                ca_path=str(ca_file),
            )
            .build()
        )

        client = NeonLinkClient(config_with_tls)

        with patch("grpc.ssl_channel_credentials") as mock_ssl:
            mock_ssl.return_value = MagicMock()
            creds = client._create_credentials()

            mock_ssl.assert_called_once()
            call_args = mock_ssl.call_args
            assert call_args.kwargs["root_certificates"] == b"fake-ca-cert"
            assert call_args.kwargs["private_key"] == b"fake-client-key"
            assert call_args.kwargs["certificate_chain"] == b"fake-client-cert"


class TestNeonLinkClientSubscribe:
    """Tests for NeonLink client subscribe functionality."""

    @pytest.mark.asyncio
    async def test_subscribe_not_connected(self, config):
        """Test subscribe raises error when not connected."""
        client = NeonLinkClient(config)

        with pytest.raises(ConnectionError, match="Not connected"):
            async for _ in client.subscribe(MagicMock()):
                pass

    @pytest.mark.asyncio
    async def test_subscribe_yields_messages(self, mock_client):
        """Test subscribe yields messages from stream."""
        # Create mock messages
        mock_messages = [
            MagicMock(message_id="msg-1"),
            MagicMock(message_id="msg-2"),
            MagicMock(message_id="msg-3"),
        ]

        # Create async iterator mock
        async def mock_subscribe(*args, **kwargs):
            for msg in mock_messages:
                yield msg

        mock_client._stub.Subscribe = mock_subscribe

        request = MagicMock()
        received = []

        async for message in mock_client.subscribe(request):
            received.append(message)

        assert len(received) == 3
        assert received[0].message_id == "msg-1"
        assert received[1].message_id == "msg-2"
        assert received[2].message_id == "msg-3"


class TestNeonLinkClientHealthCheck:
    """Tests for NeonLink client health check functionality."""

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, mock_client):
        """Test health check returns True when channel is ready."""
        # Mock channel_ready to complete immediately
        async def mock_channel_ready():
            return None

        mock_client._channel.channel_ready = mock_channel_ready

        result = await mock_client.health_check()
        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, mock_client):
        """Test health check returns False on timeout."""
        async def mock_channel_ready():
            import asyncio
            await asyncio.sleep(10)  # Will timeout

        mock_client._channel.channel_ready = mock_channel_ready

        result = await mock_client.health_check()
        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_exception(self, mock_client):
        """Test health check returns False on exception."""
        async def mock_channel_ready():
            raise Exception("Connection failed")

        mock_client._channel.channel_ready = mock_channel_ready

        result = await mock_client.health_check()
        assert result is False

    @pytest.mark.asyncio
    async def test_get_stream_health_success(self, mock_client):
        """Test get_stream_health returns health response."""
        mock_response = MagicMock()
        mock_response.stream_name = "test-stream"
        mock_response.length = 100
        mock_response.healthy = True

        mock_client._stub.GetStreamHealth = AsyncMock(return_value=mock_response)

        with patch("messaging.v1.messaging_pb2.StreamHealthRequest") as mock_request:
            mock_request.return_value = MagicMock()
            response = await mock_client.get_stream_health("test-stream")

        assert response.stream_name == "test-stream"
        assert response.length == 100
        assert response.healthy is True


class TestNeonLinkClientAutoReconnect:
    """Tests for NeonLink client auto-reconnection."""

    @pytest.mark.asyncio
    async def test_enable_auto_reconnect(self, mock_client):
        """Test enabling auto-reconnect creates task."""
        import asyncio

        # Need event loop for task creation
        mock_client.enable_auto_reconnect()

        assert mock_client._reconnect_task is not None
        assert isinstance(mock_client._reconnect_task, asyncio.Task)

        # Cleanup
        mock_client._reconnect_task.cancel()
        try:
            await mock_client._reconnect_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_disable_auto_reconnect(self, mock_client):
        """Test disabling auto-reconnect cancels task."""
        import asyncio

        mock_client.enable_auto_reconnect()
        assert mock_client._reconnect_task is not None

        mock_client.disable_auto_reconnect()
        assert mock_client._reconnect_task is None

    @pytest.mark.asyncio
    async def test_close_cancels_reconnect_task(self, mock_client):
        """Test close() cancels auto-reconnect task."""
        mock_client._channel.close = AsyncMock()

        mock_client.enable_auto_reconnect()
        assert mock_client._reconnect_task is not None

        await mock_client.close()

        assert mock_client._reconnect_task is None
        assert mock_client._connected is False


class TestNeonLinkClientMiddleware:
    """Tests for NeonLink client middleware integration."""

    @pytest.mark.asyncio
    async def test_publish_with_middleware(self, config):
        """Test publish goes through middleware chain."""
        from neonlink.middleware import LoggingMiddleware

        call_order = []

        class TrackingMiddleware:
            async def __call__(self, handler):
                call_order.append("before")
                result = await handler()
                call_order.append("after")
                return result

        middlewares = [TrackingMiddleware()]
        client = NeonLinkClient(config, middlewares=middlewares)

        # Setup mock
        mock_response = MagicMock()
        mock_response.message_id = "msg-123"

        client._stub = MagicMock()
        client._stub.Publish = AsyncMock(return_value=mock_response)
        client._connected = True

        request = MagicMock()
        response = await client.publish(request)

        assert response.message_id == "msg-123"
        assert call_order == ["before", "after"]

    @pytest.mark.asyncio
    async def test_publish_with_multiple_middlewares(self, config):
        """Test publish goes through multiple middlewares in order."""
        call_order = []

        class Middleware1:
            async def __call__(self, handler):
                call_order.append("m1_before")
                result = await handler()
                call_order.append("m1_after")
                return result

        class Middleware2:
            async def __call__(self, handler):
                call_order.append("m2_before")
                result = await handler()
                call_order.append("m2_after")
                return result

        middlewares = [Middleware1(), Middleware2()]
        client = NeonLinkClient(config, middlewares=middlewares)

        mock_response = MagicMock()
        client._stub = MagicMock()
        client._stub.Publish = AsyncMock(return_value=mock_response)
        client._connected = True

        await client.publish(MagicMock())

        # Middleware executes in order: m1 -> m2 -> handler -> m2 -> m1
        assert call_order == ["m1_before", "m2_before", "m2_after", "m1_after"]


class TestNeonLinkClientSecureConnection:
    """Tests for NeonLink client secure connections."""

    @pytest.mark.asyncio
    async def test_connect_with_tls(self, tmp_path):
        """Test connecting with TLS configuration."""
        ca_file = tmp_path / "ca.pem"
        ca_file.write_bytes(b"fake-ca-cert")

        config = (
            ConfigBuilder()
            .with_service_name("test-service")
            .with_address("localhost:9090")
            .with_tls(ca_path=str(ca_file))
            .build()
        )

        with patch("grpc.ssl_channel_credentials") as mock_ssl:
            with patch("grpc.aio.secure_channel") as mock_channel:
                mock_ssl.return_value = MagicMock()
                mock_channel.return_value = MagicMock()

                with patch("messaging.v1.messaging_pb2_grpc.MessageBrokerStub") as mock_stub:
                    mock_stub.return_value = MagicMock()

                    client = NeonLinkClient(config)
                    await client.connect()

                    assert client._connected is True
                    mock_ssl.assert_called_once()
                    mock_channel.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_with_insecure_tls(self):
        """Test connecting with insecure TLS (development mode)."""
        config = (
            ConfigBuilder()
            .with_service_name("test-service")
            .with_address("localhost:9090")
            .with_tls(insecure=True)
            .build()
        )

        with patch("grpc.aio.insecure_channel") as mock_channel:
            mock_channel.return_value = MagicMock()

            with patch("messaging.v1.messaging_pb2_grpc.MessageBrokerStub") as mock_stub:
                mock_stub.return_value = MagicMock()

                client = NeonLinkClient(config)
                await client.connect()

                assert client._connected is True
                # Verify channel was called with address and options
                mock_channel.assert_called_once()
                call_args = mock_channel.call_args
                assert call_args[0][0] == config.address


class TestNeonLinkClientTimeouts:
    """Tests for NeonLink client timeout handling."""

    @pytest.mark.asyncio
    async def test_publish_with_custom_timeout(self, mock_client):
        """Test publish uses custom timeout when provided."""
        mock_response = MagicMock()
        mock_client._stub.Publish = AsyncMock(return_value=mock_response)

        request = MagicMock()
        await mock_client.publish(request, timeout=60.0)

        call_kwargs = mock_client._stub.Publish.call_args.kwargs
        assert call_kwargs["timeout"] == 60.0

    @pytest.mark.asyncio
    async def test_publish_uses_default_timeout(self, mock_client):
        """Test publish uses config timeout by default."""
        mock_response = MagicMock()
        mock_client._stub.Publish = AsyncMock(return_value=mock_response)

        request = MagicMock()
        await mock_client.publish(request)

        call_kwargs = mock_client._stub.Publish.call_args.kwargs
        assert call_kwargs["timeout"] == mock_client.config.timeout
