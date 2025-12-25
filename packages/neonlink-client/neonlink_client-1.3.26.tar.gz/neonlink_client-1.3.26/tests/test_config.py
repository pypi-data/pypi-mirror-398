"""Tests for NeonLink configuration."""

import os
import pytest
from unittest.mock import patch

from neonlink import ConfigBuilder, NeonLinkConfig, RetryPolicy, TLSConfig


class TestTLSConfig:
    """Tests for TLSConfig dataclass."""

    def test_default_values(self):
        config = TLSConfig()
        assert config.cert_path is None
        assert config.key_path is None
        assert config.ca_path is None
        assert config.insecure is False

    def test_custom_values(self):
        config = TLSConfig(
            cert_path="/path/to/cert.pem",
            key_path="/path/to/key.pem",
            ca_path="/path/to/ca.pem",
            insecure=True,
        )
        assert config.cert_path == "/path/to/cert.pem"
        assert config.key_path == "/path/to/key.pem"
        assert config.ca_path == "/path/to/ca.pem"
        assert config.insecure is True


class TestRetryPolicy:
    """Tests for RetryPolicy dataclass."""

    def test_default_values(self):
        policy = RetryPolicy()
        assert policy.max_retries == 3
        assert policy.initial_backoff == 0.1
        assert policy.max_backoff == 30.0
        assert policy.backoff_multiplier == 2.0

    def test_custom_values(self):
        policy = RetryPolicy(
            max_retries=5,
            initial_backoff=0.5,
            max_backoff=60.0,
            backoff_multiplier=3.0,
        )
        assert policy.max_retries == 5
        assert policy.initial_backoff == 0.5
        assert policy.max_backoff == 60.0
        assert policy.backoff_multiplier == 3.0


class TestNeonLinkConfig:
    """Tests for NeonLinkConfig dataclass."""

    def test_required_fields(self):
        config = NeonLinkConfig(
            service_name="test-service",
            address="localhost:9090",
        )
        assert config.service_name == "test-service"
        assert config.address == "localhost:9090"
        assert config.tls is None
        assert config.timeout == 30.0

    def test_with_all_fields(self):
        tls = TLSConfig(cert_path="/path/to/cert.pem")
        policy = RetryPolicy(max_retries=5)
        config = NeonLinkConfig(
            service_name="test-service",
            address="localhost:9090",
            tls=tls,
            timeout=60.0,
            retry_policy=policy,
            metadata={"key": "value"},
        )
        assert config.tls == tls
        assert config.timeout == 60.0
        assert config.retry_policy == policy
        assert config.metadata == {"key": "value"}

    def test_from_env(self):
        env_vars = {
            "NEONLINK_SERVICE_NAME": "env-service",
            "NEONLINK_ADDRESS": "remote:9090",
            "NEONLINK_TIMEOUT": "60",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            config = NeonLinkConfig.from_env()
            assert config.service_name == "env-service"
            assert config.address == "remote:9090"
            assert config.timeout == 60.0
            assert config.tls is None

    def test_from_env_with_tls(self):
        env_vars = {
            "NEONLINK_SERVICE_NAME": "tls-service",
            "NEONLINK_ADDRESS": "secure:9090",
            "NEONLINK_TLS_CERT": "/path/to/cert.pem",
            "NEONLINK_TLS_KEY": "/path/to/key.pem",
            "NEONLINK_TLS_CA": "/path/to/ca.pem",
            "NEONLINK_TLS_INSECURE": "true",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            config = NeonLinkConfig.from_env()
            assert config.tls is not None
            assert config.tls.cert_path == "/path/to/cert.pem"
            assert config.tls.key_path == "/path/to/key.pem"
            assert config.tls.ca_path == "/path/to/ca.pem"
            assert config.tls.insecure is True

    def test_from_env_missing_service_name(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(KeyError):
                NeonLinkConfig.from_env()


class TestConfigBuilder:
    """Tests for ConfigBuilder."""

    def test_build_with_required_fields(self):
        config = (
            ConfigBuilder()
            .with_service_name("my-service")
            .with_address("localhost:9090")
            .build()
        )
        assert config.service_name == "my-service"
        assert config.address == "localhost:9090"

    def test_build_without_service_name_raises(self):
        with pytest.raises(ValueError, match="service_name is required"):
            ConfigBuilder().with_address("localhost:9090").build()

    def test_default_address(self):
        config = ConfigBuilder().with_service_name("test").build()
        assert config.address == "localhost:9090"

    def test_with_tls(self):
        config = (
            ConfigBuilder()
            .with_service_name("tls-service")
            .with_tls(
                cert_path="/path/to/cert.pem",
                key_path="/path/to/key.pem",
                ca_path="/path/to/ca.pem",
                insecure=False,
            )
            .build()
        )
        assert config.tls is not None
        assert config.tls.cert_path == "/path/to/cert.pem"
        assert config.tls.key_path == "/path/to/key.pem"
        assert config.tls.ca_path == "/path/to/ca.pem"
        assert config.tls.insecure is False

    def test_with_timeout(self):
        config = (
            ConfigBuilder()
            .with_service_name("test")
            .with_timeout(120.0)
            .build()
        )
        assert config.timeout == 120.0

    def test_with_retry_policy(self):
        config = (
            ConfigBuilder()
            .with_service_name("test")
            .with_retry_policy(
                max_retries=5,
                initial_backoff=0.5,
                max_backoff=60.0,
            )
            .build()
        )
        assert config.retry_policy.max_retries == 5
        assert config.retry_policy.initial_backoff == 0.5
        assert config.retry_policy.max_backoff == 60.0

    def test_with_metadata(self):
        config = (
            ConfigBuilder()
            .with_service_name("test")
            .with_metadata("key1", "value1")
            .with_metadata("key2", "value2")
            .build()
        )
        assert config.metadata == {"key1": "value1", "key2": "value2"}

    def test_builder_is_chainable(self):
        builder = ConfigBuilder()
        result = builder.with_service_name("test")
        assert result is builder

        result = builder.with_address("localhost:8080")
        assert result is builder

        result = builder.with_timeout(10.0)
        assert result is builder
