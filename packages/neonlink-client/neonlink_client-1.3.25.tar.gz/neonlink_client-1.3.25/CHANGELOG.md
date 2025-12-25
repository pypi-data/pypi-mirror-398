# Changelog

All notable changes to the NeonLink Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Nothing yet

## [1.0.0] - 2025-12-06

### Added
- Initial release of NeonLink Python SDK
- **Core Client** (`NeonLinkClient`)
  - Async/await support with `grpcio`
  - Context manager support (`async with`)
  - Connection management with auto-reconnection
  - TLS/mTLS support for secure connections
- **Configuration** (`ConfigBuilder`, `NeonLinkConfig`)
  - Builder pattern for fluent configuration
  - Environment variable support (`NEONLINK_*`)
  - TLS configuration (`TLSConfig`)
  - Retry policy configuration (`RetryPolicy`)
- **Middleware System**
  - `LoggingMiddleware` - Request/response logging
  - `RetryMiddleware` - Exponential backoff retries
  - `TimeoutMiddleware` - Request timeout enforcement
  - `RecoveryMiddleware` - Exception handling
  - `MetricsMiddleware` - Performance metrics collection
- **Message Building** (`MessageBuilder`)
  - Fluent builder pattern for message construction
  - Automatic UUID generation for message IDs
  - JSON payload support
  - Idempotency key support (explicit and field-based generation)
- **Helper Functions**
  - `get_identity_context()` - Extract identity headers
  - `get_webhook_ingress_context()` - Extract webhook headers
  - `get_active_job_type_name()` - Get job type from headers
  - `get_job_type_message()` - Get job type message from headers
- **Error Handling**
  - `NeonLinkError` - Base exception class
  - `ConnectionError` - Connection failures
  - `TimeoutError` - Request timeouts
  - `PublishError` - Publish failures
  - `SubscribeError` - Subscription failures
  - `AckError` - Acknowledgment failures
  - `ConfigurationError` - Invalid configuration
- **gRPC Operations**
  - `publish()` - Send messages to streams
  - `subscribe()` - Stream messages with async iterator
  - `ack()` - Acknowledge processed messages
  - `nack()` - Negative acknowledge failed messages
  - `get_stream_health()` - Check stream health metrics
  - `health_check()` - Connection health verification

### Feature Parity
- Full feature parity with Go SDK v1.0.8
- All core operations supported
- Middleware chain compatible with Go SDK patterns
- Idempotency key generation matches Go SDK algorithm

### Documentation
- Comprehensive README with quick start guide
- Five example scripts demonstrating usage patterns
- Type hints throughout for IDE support

[Unreleased]: https://github.com/LetA-Tech/mcfo-neonlink/compare/py3-v1.0.0...HEAD
[1.0.0]: https://github.com/LetA-Tech/mcfo-neonlink/releases/tag/py3-v1.0.0
