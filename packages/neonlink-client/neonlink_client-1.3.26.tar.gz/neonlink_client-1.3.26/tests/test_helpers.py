"""Tests for NeonLink helpers."""

import json
import pytest
from unittest.mock import MagicMock

from neonlink import MessageBuilder


class TestMessageBuilder:
    """Tests for MessageBuilder."""

    def test_default_values(self):
        builder = MessageBuilder()
        assert builder._message_id is not None
        assert builder._correlation_id is not None
        assert builder._timestamp is not None
        assert builder._stream is None
        assert builder._message_type is None
        assert builder._payload == b""
        assert builder._headers == {}

    def test_with_stream(self):
        builder = MessageBuilder().with_stream("test-stream")
        assert builder._stream == "test-stream"

    def test_with_message_type(self):
        builder = MessageBuilder().with_message_type("TestMessage")
        assert builder._message_type == "TestMessage"

    def test_with_message_id(self):
        builder = MessageBuilder().with_message_id("custom-id")
        assert builder._message_id == "custom-id"

    def test_with_correlation_id(self):
        builder = MessageBuilder().with_correlation_id("corr-123")
        assert builder._correlation_id == "corr-123"

    def test_with_payload(self):
        builder = MessageBuilder().with_payload(b"raw bytes")
        assert builder._payload == b"raw bytes"

    def test_with_json_payload(self):
        builder = MessageBuilder().with_json_payload({"key": "value", "number": 42})
        payload = json.loads(builder._payload)
        assert payload == {"key": "value", "number": 42}

    def test_with_header(self):
        builder = MessageBuilder().with_header("x-custom", "value")
        assert builder._headers == {"x-custom": "value"}

    def test_with_headers(self):
        builder = MessageBuilder().with_headers({"key1": "value1", "key2": "value2"})
        assert builder._headers == {"key1": "value1", "key2": "value2"}

    def test_with_idempotency_key(self):
        builder = MessageBuilder().with_idempotency_key("idem-key-123")
        assert builder._idempotency_key == "idem-key-123"
        assert builder._headers["x-idempotency-key"] == "idem-key-123"

    def test_with_idempotency_fields(self):
        builder = MessageBuilder().with_idempotency_fields("user-123", "action-456")
        assert "x-idempotency-key" in builder._headers
        assert len(builder._headers["x-idempotency-key"]) == 32  # SHA256 truncated

    def test_with_idempotency_fields_with_prefix(self):
        builder = MessageBuilder().with_idempotency_fields(
            "user-123", "action-456", prefix="my-service"
        )
        assert "x-idempotency-key" in builder._headers

    def test_idempotency_fields_deterministic(self):
        """Same fields should produce same idempotency key."""
        builder1 = MessageBuilder().with_idempotency_fields("user-123", "action-456")
        builder2 = MessageBuilder().with_idempotency_fields("user-123", "action-456")
        assert builder1._headers["x-idempotency-key"] == builder2._headers["x-idempotency-key"]

    def test_idempotency_fields_different_for_different_inputs(self):
        """Different fields should produce different keys."""
        builder1 = MessageBuilder().with_idempotency_fields("user-123", "action-456")
        builder2 = MessageBuilder().with_idempotency_fields("user-123", "action-789")
        assert builder1._headers["x-idempotency-key"] != builder2._headers["x-idempotency-key"]

    def test_build_dict(self):
        result = (
            MessageBuilder()
            .with_stream("test-stream")
            .with_message_type("TestMessage")
            .with_json_payload({"key": "value"})
            .build_dict()
        )
        assert result["stream"] == "test-stream"
        assert result["message_type"] == "TestMessage"
        assert json.loads(result["payload"]) == {"key": "value"}

    def test_build_dict_missing_stream(self):
        with pytest.raises(ValueError, match="stream is required"):
            MessageBuilder().with_message_type("TestMessage").build_dict()

    def test_build_dict_missing_message_type(self):
        with pytest.raises(ValueError, match="message_type is required"):
            MessageBuilder().with_stream("test-stream").build_dict()

    def test_builder_is_chainable(self):
        builder = MessageBuilder()
        result = builder.with_stream("test")
        assert result is builder

        result = builder.with_message_type("Test")
        assert result is builder

        result = builder.with_payload(b"data")
        assert result is builder
