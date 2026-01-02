# Python SDK Development Debt & Production Readiness Fixes

> **Generated:** December 7, 2025  
> **Status:** Pre-Production Review  
> **Priority:** Critical fixes required before production deployment

---

## Table of Contents

1. [Critical Issues](#1-critical-issues)
   - [1.1 Missing Circuit Breaker](#11-missing-circuit-breaker)
   - [1.2 MessageBuilder Proto Structure Mismatch](#12-messagebuilder-proto-structure-mismatch)
   - [1.3 Missing IdentityContext Support](#13-missing-identitycontext-support)
2. [Medium Priority Issues](#2-medium-priority-issues)
   - [2.1 Missing JWT Authentication](#21-missing-jwt-authentication)
   - [2.2 Missing SubscriptionBuilder](#22-missing-subscriptionbuilder)
   - [2.3 Missing Keepalive Configuration](#23-missing-keepalive-configuration)
   - [2.4 Missing Handler Concurrency Config](#24-missing-handler-concurrency-config)
3. [Test Fixes](#3-test-fixes)
   - [3.1 Incorrect Mock Patch Paths](#31-incorrect-mock-patch-paths)
   - [3.2 Auto-reconnect Task Cleanup](#32-auto-reconnect-task-cleanup)
4. [Package Configuration](#4-package-configuration)
   - [4.1 Direct Git Reference Issue](#41-direct-git-reference-issue)
5. [Implementation Files](#5-implementation-files)

---

## 1. Critical Issues

### 1.1 Missing Circuit Breaker

**Issue:** The Python SDK lacks circuit breaker pattern implementation that exists in Go SDK.

**Impact:** Without circuit breaker, a failing NeonLink server can cause cascade failures in microservices. Requests will pile up, exhaust resources, and crash services.

**Go SDK Reference:**
```go
// pkg/neonlink/client.go
type CircuitBreaker struct {
    maxFailures      int
    halfOpenMax      int
    resetTimeout     time.Duration
    failures         int
    lastFailTime     time.Time
    state            CircuitState
    halfOpenInFlight int
    mutex            sync.Mutex
}

type CircuitState int

const (
    CircuitClosed CircuitState = iota  // Normal operation
    CircuitOpen                         // Rejecting requests
    CircuitHalfOpen                     // Testing recovery
)
```

**Resolution:** Add `circuit_breaker.py` module with full implementation.

**File to create:** `neonlink/circuit_breaker.py`

```python
"""Circuit breaker implementation for resilience."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Awaitable, Callable, TypeVar

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Rejecting requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    max_failures: int = 5
    half_open_max: int = 1
    reset_timeout: float = 30.0  # seconds


@dataclass
class CircuitBreaker:
    """
    Circuit breaker for protecting against cascade failures.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Failure threshold exceeded, requests rejected immediately
    - HALF_OPEN: Testing if service recovered, limited requests allowed
    """
    config: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    _failures: int = field(default=0, init=False)
    _last_failure_time: float = field(default=0.0, init=False)
    _half_open_in_flight: int = field(default=0, init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state

    @property
    def failures(self) -> int:
        """Get current failure count."""
        return self._failures

    async def call(self, func: Callable[[], Awaitable[T]]) -> T:
        """
        Execute function through circuit breaker.
        
        Args:
            func: Async function to execute
            
        Returns:
            Result from function
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        async with self._lock:
            if not await self._allow_request():
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is {self._state.value}, "
                    f"failures={self._failures}"
                )
            
            if self._state == CircuitState.HALF_OPEN:
                self._half_open_in_flight += 1

        try:
            result = await func()
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise

    async def _allow_request(self) -> bool:
        """Check if request should be allowed."""
        if self._state == CircuitState.CLOSED:
            return True
        
        if self._state == CircuitState.OPEN:
            # Check if reset timeout has elapsed
            if time.time() - self._last_failure_time >= self.config.reset_timeout:
                self._state = CircuitState.HALF_OPEN
                self._half_open_in_flight = 0
                return True
            return False
        
        # HALF_OPEN: Allow limited requests
        if self._state == CircuitState.HALF_OPEN:
            return self._half_open_in_flight < self.config.half_open_max
        
        return False

    async def _on_success(self) -> None:
        """Handle successful request."""
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._half_open_in_flight -= 1
            
            # Reset on success
            self._failures = 0
            self._state = CircuitState.CLOSED

    async def _on_failure(self) -> None:
        """Handle failed request."""
        async with self._lock:
            self._failures += 1
            self._last_failure_time = time.time()
            
            if self._state == CircuitState.HALF_OPEN:
                self._half_open_in_flight -= 1
                # Immediately open on half-open failure
                self._state = CircuitState.OPEN
            elif self._failures >= self.config.max_failures:
                self._state = CircuitState.OPEN

    def reset(self) -> None:
        """Manually reset circuit breaker."""
        self._state = CircuitState.CLOSED
        self._failures = 0
        self._half_open_in_flight = 0


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass
```

**Integration in client.py:**

```python
# In NeonLinkClient.__init__
from neonlink.circuit_breaker import CircuitBreaker, CircuitBreakerConfig

self._circuit_breaker = CircuitBreaker(
    CircuitBreakerConfig(
        max_failures=config.cb_max_failures,
        half_open_max=config.cb_half_open_max,
        reset_timeout=config.cb_reset_timeout,
    )
)

# In publish method
async def publish(self, request, timeout=None):
    if not self._stub:
        raise ConnectionError("Not connected to NeonLink")
    
    async def _do_publish():
        return await self._stub.Publish(
            request,
            timeout=timeout or self.config.timeout,
            metadata=self._get_metadata(),
        )
    
    # Wrap with circuit breaker
    return await self._circuit_breaker.call(
        lambda: self._middleware_chain.execute(_do_publish)
    )
```

---

### 1.2 MessageBuilder Proto Structure Mismatch

**Issue:** Python MessageBuilder creates flat string-based messages, but the server expects structured protobuf messages with `MessageHeader` and enums.

**Current Python (Wrong):**
```python
# helpers.py - Creates flat structure with strings
return messaging_pb2.PublishRequest(
    stream=self._stream,
    message_type=self._message_type,  # String "OrderCreated"
    message_id=self._message_id,
    headers=self._headers,  # Dict[str, str]
    payload=self._payload,
)
```

**Go SDK (Correct):**
```go
// Uses structured MessageHeader with enums
return &neoncontract.PublishRequest{
    Header: &neoncontract.MessageHeader{
        MessageId:     mb.header.MessageId,
        MessageType:   neoncontract.MessageType_ORDER_CREATED,  // Enum
        SourceService: neoncontract.SourceService_ORDER_SERVICE,
        TargetService: neoncontract.TargetService_INVENTORY_SERVICE,
        Identity:      &neoncontract.IdentityContext{...},
    },
    Payload: &neoncontract.PublishRequest_JobDispatch{...},
}
```

**Resolution:** Rewrite MessageBuilder to match neoncontract protobuf structure.

**Updated `neonlink/helpers.py`:**

```python
"""Helper functions and utilities for NeonLink client."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

if TYPE_CHECKING:
    from neoncontract.messaging.v1 import messaging_pb2


# Type alias for identity option function
IdentityOption = Callable[["messaging_pb2.IdentityContext"], None]


class MessageBuilder:
    """
    Builder for constructing NeonLink publish requests.

    Matches Go SDK's MessageBuilder with proper protobuf structure:
    - MessageHeader with enums for MessageType, SourceService, TargetService
    - IdentityContext for idempotency
    - JobDispatch payload wrapper
    """

    def __init__(self) -> None:
        # Will be lazily imported when build() is called
        self._message_id: Optional[str] = None  # Auto-generated if not set
        self._correlation_id: Optional[str] = None  # Auto-generated if not set
        self._timestamp: Optional[int] = None  # Auto-generated if not set
        
        # Header fields (using int for enum values for flexibility)
        self._message_type: Optional[int] = None
        self._source_service: Optional[int] = None
        self._target_service: Optional[int] = None
        self._priority: Optional[int] = None
        self._ttl_seconds: int = 0
        self._version: str = ""
        
        # Identity context for idempotency
        self._identity_options: List[IdentityOption] = []
        
        # Legacy string-based headers (for backward compatibility)
        self._headers: Dict[str, str] = {}
        
        # Payload
        self._job_dispatch: Optional[Any] = None
        self._raw_payload: Optional[bytes] = None

    # =========================================================================
    # Header Configuration (Matching Go SDK)
    # =========================================================================

    def with_message_id(self, message_id: str) -> MessageBuilder:
        """Set custom message ID (auto-generated UUID if not set)."""
        self._message_id = message_id
        return self

    def with_correlation_id(self, correlation_id: str) -> MessageBuilder:
        """Set correlation ID for distributed tracing."""
        self._correlation_id = correlation_id
        return self

    def with_timestamp(self, timestamp: int) -> MessageBuilder:
        """Set timestamp (Unix epoch seconds, auto-generated if not set)."""
        self._timestamp = timestamp
        return self

    def with_message_type(self, message_type: int) -> MessageBuilder:
        """
        Set message type enum value.
        
        Use neoncontract.messaging.v1.messaging_pb2.MessageType enum values.
        Example: messaging_pb2.MessageType.ORDER_CREATED
        """
        self._message_type = message_type
        return self

    def with_source_service(self, source_service: int) -> MessageBuilder:
        """
        Set source service enum value.
        
        Use neoncontract.messaging.v1.messaging_pb2.SourceService enum values.
        """
        self._source_service = source_service
        return self

    def with_target_service(self, target_service: int) -> MessageBuilder:
        """
        Set target service enum value.
        
        Use neoncontract.messaging.v1.messaging_pb2.TargetService enum values.
        """
        self._target_service = target_service
        return self

    def with_priority(self, priority: int) -> MessageBuilder:
        """Set message priority enum value."""
        self._priority = priority
        return self

    def with_ttl(self, ttl_seconds: int) -> MessageBuilder:
        """Set message TTL in seconds."""
        self._ttl_seconds = ttl_seconds
        return self

    def with_version(self, version: str) -> MessageBuilder:
        """Set message version."""
        self._version = version
        return self

    # =========================================================================
    # Identity Context (Idempotency Support - Matching Go SDK)
    # =========================================================================

    def with_identity(self, identity: "messaging_pb2.IdentityContext") -> MessageBuilder:
        """Set the full IdentityContext directly."""
        def set_identity(ic: "messaging_pb2.IdentityContext") -> None:
            ic.CopyFrom(identity)
        self._identity_options.append(set_identity)
        return self

    def with_idempotency_fields(self, *opts: IdentityOption) -> MessageBuilder:
        """
        Set idempotency fields using functional options.
        
        Example:
            builder.with_idempotency_fields(
                with_entity_id("entity-123"),
                with_user_id("user-456"),
                with_data_type(DataType.DATA_TYPE_TRANSACTIONS),
            )
        """
        self._identity_options.extend(opts)
        return self

    # =========================================================================
    # Payload Configuration
    # =========================================================================

    def with_job_dispatch(self, job_dispatch: Any) -> MessageBuilder:
        """Set JobDispatch payload (the main payload wrapper)."""
        self._job_dispatch = job_dispatch
        return self

    def with_etl_job_context(
        self,
        etl_context: Any,
        metadata: Optional[Any] = None,
    ) -> MessageBuilder:
        """Set ETL job context payload."""
        from neoncontract.messaging.v1 import messaging_pb2
        
        self._job_dispatch = messaging_pb2.JobDispatch(
            etl_job_context=etl_context,
            metadata=metadata,
        )
        return self

    def with_goal_event_context(
        self,
        goal_context: Any,
        metadata: Optional[Any] = None,
    ) -> MessageBuilder:
        """Set goal event context payload."""
        from neoncontract.messaging.v1 import messaging_pb2
        
        self._job_dispatch = messaging_pb2.JobDispatch(
            goal_event_context=goal_context,
            metadata=metadata,
        )
        return self

    def with_webhook_ingress_context(
        self,
        webhook_context: Any,
        metadata: Optional[Any] = None,
    ) -> MessageBuilder:
        """Set webhook ingress context payload."""
        from neoncontract.messaging.v1 import messaging_pb2
        
        self._job_dispatch = messaging_pb2.JobDispatch(
            webhook_ingress_context=webhook_context,
            metadata=metadata,
        )
        return self

    # =========================================================================
    # Legacy Support (Backward Compatibility)
    # =========================================================================

    def with_header(self, key: str, value: str) -> MessageBuilder:
        """Add a legacy string header (for backward compatibility)."""
        self._headers[key] = value
        return self

    def with_headers(self, headers: Dict[str, str]) -> MessageBuilder:
        """Add multiple legacy string headers."""
        self._headers.update(headers)
        return self

    def with_payload(self, payload: bytes) -> MessageBuilder:
        """Set raw bytes payload (legacy, prefer with_job_dispatch)."""
        self._raw_payload = payload
        return self

    def with_json_payload(self, data: Any) -> MessageBuilder:
        """Set JSON payload (legacy, prefer with_job_dispatch)."""
        self._raw_payload = json.dumps(data).encode("utf-8")
        return self

    def with_idempotency_key(self, key: str) -> MessageBuilder:
        """Set idempotency key directly in IdentityContext."""
        def set_key(ic: "messaging_pb2.IdentityContext") -> None:
            ic.idempotency_key = key
        self._identity_options.append(set_key)
        return self

    def with_idempotency_hash(
        self,
        *fields: str,
        prefix: Optional[str] = None,
    ) -> MessageBuilder:
        """
        Generate idempotency key from hash of fields (legacy compatibility).
        
        Creates a SHA256 hash truncated to 32 chars.
        """
        combined = ":".join(fields)
        if prefix:
            combined = f"{prefix}:{combined}"
        
        key = hashlib.sha256(combined.encode()).hexdigest()[:32]
        return self.with_idempotency_key(key)

    # =========================================================================
    # Build Methods
    # =========================================================================

    def build(self) -> "messaging_pb2.PublishRequest":
        """
        Build the PublishRequest with proper protobuf structure.
        
        Auto-generates:
        - message_id (UUID) if not set
        - correlation_id (UUID) if not set  
        - timestamp (Unix epoch) if not set
        
        Raises:
            ValueError: If required fields are missing
        """
        from neoncontract.messaging.v1 import messaging_pb2

        # Validate required fields
        if self._message_type is None:
            raise ValueError("message_type is required (use with_message_type)")
        if self._job_dispatch is None and self._raw_payload is None:
            raise ValueError("payload is required (use with_job_dispatch or with_payload)")

        # Build MessageHeader
        header = messaging_pb2.MessageHeader(
            message_id=self._message_id or str(uuid.uuid4()),
            correlation_id=self._correlation_id or str(uuid.uuid4()),
            timestamp=self._timestamp or int(datetime.now(timezone.utc).timestamp()),
            message_type=self._message_type,
            ttl_seconds=self._ttl_seconds,
            version=self._version,
        )

        # Set optional enum fields
        if self._source_service is not None:
            header.source_service = self._source_service
        if self._target_service is not None:
            header.target_service = self._target_service
        if self._priority is not None:
            header.priority = self._priority

        # Build IdentityContext if options provided
        if self._identity_options:
            identity = messaging_pb2.IdentityContext()
            for opt in self._identity_options:
                opt(identity)
            header.identity.CopyFrom(identity)

        # Build PublishRequest
        request = messaging_pb2.PublishRequest(header=header)
        
        # Set payload
        if self._job_dispatch is not None:
            request.job_dispatch.CopyFrom(self._job_dispatch)
        
        return request

    def build_dict(self) -> Dict[str, Any]:
        """
        Build as dictionary (for testing/debugging without proto).
        
        Note: This is for backward compatibility and testing only.
        Production code should use build() for proper protobuf messages.
        """
        return {
            "header": {
                "message_id": self._message_id or str(uuid.uuid4()),
                "correlation_id": self._correlation_id or str(uuid.uuid4()),
                "timestamp": self._timestamp or int(datetime.now(timezone.utc).timestamp()),
                "message_type": self._message_type,
                "source_service": self._source_service,
                "target_service": self._target_service,
                "priority": self._priority,
                "ttl_seconds": self._ttl_seconds,
                "version": self._version,
            },
            "legacy_headers": self._headers,
            "has_job_dispatch": self._job_dispatch is not None,
            "has_raw_payload": self._raw_payload is not None,
        }


# =========================================================================
# Identity Option Functions (Matching Go SDK functional options)
# =========================================================================

def with_entity_id(entity_id: str) -> IdentityOption:
    """Set entity ID in IdentityContext."""
    def apply(ic: "messaging_pb2.IdentityContext") -> None:
        ic.entity_id = entity_id
    return apply


def with_user_id(user_id: str) -> IdentityOption:
    """Set user ID in IdentityContext."""
    def apply(ic: "messaging_pb2.IdentityContext") -> None:
        ic.user_id = user_id
    return apply


def with_item_id(item_id: str) -> IdentityOption:
    """Set item ID in IdentityContext."""
    def apply(ic: "messaging_pb2.IdentityContext") -> None:
        ic.item_id = item_id
    return apply


def with_batch_id(batch_id: str) -> IdentityOption:
    """Set batch ID in IdentityContext."""
    def apply(ic: "messaging_pb2.IdentityContext") -> None:
        ic.batch_id = batch_id
    return apply


def with_job_id(job_id: str) -> IdentityOption:
    """Set job ID in IdentityContext."""
    def apply(ic: "messaging_pb2.IdentityContext") -> None:
        ic.job_id = job_id
    return apply


def with_request_id(request_id: str) -> IdentityOption:
    """Set request ID in IdentityContext."""
    def apply(ic: "messaging_pb2.IdentityContext") -> None:
        ic.request_id = request_id
    return apply


def with_event_id(event_id: str) -> IdentityOption:
    """Set event ID in IdentityContext."""
    def apply(ic: "messaging_pb2.IdentityContext") -> None:
        ic.event_id = event_id
    return apply


def with_connection_id(connection_id: str) -> IdentityOption:
    """Set connection ID in IdentityContext."""
    def apply(ic: "messaging_pb2.IdentityContext") -> None:
        ic.connection_id = connection_id
    return apply


def with_provider(provider: str) -> IdentityOption:
    """Set provider in IdentityContext."""
    def apply(ic: "messaging_pb2.IdentityContext") -> None:
        ic.provider = provider
    return apply


def with_trigger_source(source: str) -> IdentityOption:
    """Set trigger source in IdentityContext."""
    def apply(ic: "messaging_pb2.IdentityContext") -> None:
        ic.trigger_source = source
    return apply


def with_data_type(data_type: int) -> IdentityOption:
    """Set data type enum in IdentityContext."""
    def apply(ic: "messaging_pb2.IdentityContext") -> None:
        ic.data_type = data_type
    return apply


def with_source_system(source: int) -> IdentityOption:
    """Set source system enum in IdentityContext."""
    def apply(ic: "messaging_pb2.IdentityContext") -> None:
        ic.source = source
    return apply


def with_idempotency_key_option(key: str) -> IdentityOption:
    """Set pre-computed idempotency key in IdentityContext."""
    def apply(ic: "messaging_pb2.IdentityContext") -> None:
        ic.idempotency_key = key
    return apply


# =========================================================================
# Message Extraction Helpers (Matching Go SDK)
# =========================================================================

def get_job_dispatch(
    message: "messaging_pb2.StreamMessage",
) -> tuple[Optional[Any], bool]:
    """Extract JobDispatch from StreamMessage."""
    if message is None:
        return None, False
    jd = message.job_dispatch if message.HasField("job_dispatch") else None
    return jd, jd is not None


def get_etl_job_context(
    message: "messaging_pb2.StreamMessage",
) -> tuple[Optional[Any], bool]:
    """Extract ETLJobContext from StreamMessage if present."""
    jd, ok = get_job_dispatch(message)
    if not ok or jd is None:
        return None, False
    if jd.HasField("etl_job_context"):
        return jd.etl_job_context, True
    return None, False


def get_webhook_ingress_context(
    message: "messaging_pb2.StreamMessage",
) -> tuple[Optional[Any], bool]:
    """Extract WebhookIngressContext from StreamMessage if present."""
    jd, ok = get_job_dispatch(message)
    if not ok or jd is None:
        return None, False
    if jd.HasField("webhook_ingress_context"):
        return jd.webhook_ingress_context, True
    return None, False


def get_goal_event_context(
    message: "messaging_pb2.StreamMessage",
) -> tuple[Optional[Any], bool]:
    """Extract GoalEventContext from StreamMessage if present."""
    jd, ok = get_job_dispatch(message)
    if not ok or jd is None:
        return None, False
    if jd.HasField("goal_event_context"):
        return jd.goal_event_context, True
    return None, False


def get_identity_context(
    message: "messaging_pb2.StreamMessage",
) -> Optional["messaging_pb2.IdentityContext"]:
    """Extract IdentityContext from message header."""
    if message is None or not message.HasField("header"):
        return None
    if message.header.HasField("identity"):
        return message.header.identity
    return None
```

---

### 1.3 Missing IdentityContext Support

**Issue:** The current implementation uses simple string hashing for idempotency instead of structured IdentityContext.

**Impact:** Server cannot properly perform reflection-based idempotency key generation. Idempotency may not work correctly.

**Resolution:** Already addressed in section 1.2 above with the full `helpers.py` rewrite including:
- `IdentityOption` functional options pattern (matching Go SDK)
- All identity field setters (`with_entity_id`, `with_user_id`, etc.)
- Proper `IdentityContext` integration in `MessageBuilder.build()`

---

## 2. Medium Priority Issues

### 2.1 Missing JWT Authentication

**Issue:** Python SDK doesn't support JWT token authentication in gRPC metadata.

**Go SDK Reference:**
```go
// pkg/neonlink/client.go
if config.JWTToken != "" {
    dialOpts = append(dialOpts,
        grpc.WithPerRPCCredentials(&jwtCredentials{
            token:      config.JWTToken,
            requireTLS: requireTLS,
        }),
    )
}
```

**Resolution:** Add JWT token to config and metadata.

**Update `neonlink/config.py`:**

```python
@dataclass
class NeonLinkConfig:
    """Configuration for NeonLink client."""

    service_name: str
    address: str
    tls: Optional[TLSConfig] = None
    timeout: float = 30.0  # seconds
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    metadata: Dict[str, str] = field(default_factory=dict)
    
    # JWT Authentication
    jwt_token: Optional[str] = None
    
    # Circuit Breaker settings
    cb_max_failures: int = 5
    cb_half_open_max: int = 1
    cb_reset_timeout: float = 30.0  # seconds
    
    # Connection settings
    keepalive_time: float = 30.0  # seconds
    keepalive_timeout: float = 5.0  # seconds
    max_recv_msg_size: int = 4 * 1024 * 1024  # 4MB
    max_send_msg_size: int = 4 * 1024 * 1024  # 4MB
```

**Update `neonlink/client.py` `_get_metadata()`:**

```python
def _get_metadata(self) -> List[tuple[str, str]]:
    """Get metadata for gRPC calls including JWT if configured."""
    metadata: List[tuple[str, str]] = [
        ("x-service-name", self.config.service_name),
    ]
    
    # Add JWT token if configured
    if self.config.jwt_token:
        metadata.append(("authorization", f"Bearer {self.config.jwt_token}"))
    
    # Add custom metadata
    for key, value in self.config.metadata.items():
        metadata.append((key, value))
    
    return metadata
```

**Update `ConfigBuilder`:**

```python
def with_jwt_token(self, token: str) -> ConfigBuilder:
    """Set JWT token for authentication."""
    self._jwt_token = token
    return self

def with_circuit_breaker(
    self,
    max_failures: int = 5,
    half_open_max: int = 1,
    reset_timeout: float = 30.0,
) -> ConfigBuilder:
    """Configure circuit breaker settings."""
    self._cb_max_failures = max_failures
    self._cb_half_open_max = half_open_max
    self._cb_reset_timeout = reset_timeout
    return self
```

---

### 2.2 Missing SubscriptionBuilder

**Issue:** No builder helper for creating SubscribeRequest.

**Go SDK Reference:**
```go
// pkg/neonlink/helpers.go
type SubscriptionBuilder struct {
    streamName     string
    consumerGroup  string
    consumerName   string
    batchSize      int32
    timeoutSeconds int32
    autoAck        bool
    messageTypes   []neoncontract.MessageType
}
```

**Resolution:** Add `SubscriptionBuilder` class.

**Add to `neonlink/helpers.py`:**

```python
class SubscriptionBuilder:
    """
    Builder for constructing SubscribeRequest.
    
    Matches Go SDK's SubscriptionBuilder.
    """

    def __init__(self) -> None:
        self._stream_name: Optional[str] = None
        self._consumer_group: Optional[str] = None
        self._consumer_name: Optional[str] = None
        self._batch_size: int = 10
        self._timeout_seconds: int = 30
        self._auto_ack: bool = False  # Default False for safety
        self._message_types: List[int] = []

    def with_stream_name(self, stream_name: str) -> SubscriptionBuilder:
        """Set the stream name to subscribe to."""
        self._stream_name = stream_name
        return self

    def with_consumer_group(self, consumer_group: str) -> SubscriptionBuilder:
        """Set the consumer group name."""
        self._consumer_group = consumer_group
        return self

    def with_consumer_name(self, consumer_name: str) -> SubscriptionBuilder:
        """Set the consumer name (auto-generated if not set)."""
        self._consumer_name = consumer_name
        return self

    def with_batch_size(self, batch_size: int) -> SubscriptionBuilder:
        """Set the batch size for consuming messages."""
        self._batch_size = batch_size
        return self

    def with_timeout(self, timeout_seconds: int) -> SubscriptionBuilder:
        """Set the timeout in seconds."""
        self._timeout_seconds = timeout_seconds
        return self

    def with_auto_ack(self, auto_ack: bool = True) -> SubscriptionBuilder:
        """
        Enable/disable automatic acknowledgment.
        
        WARNING: auto_ack=True can cause message loss if handler crashes.
        Only use for idempotent operations.
        """
        self._auto_ack = auto_ack
        return self

    def with_message_types(self, message_types: List[int]) -> SubscriptionBuilder:
        """
        Filter subscription to specific message types.
        
        When set, enables server-side stream inference if stream_name is empty.
        """
        self._message_types = message_types
        return self

    def build(self) -> "messaging_pb2.SubscribeRequest":
        """Build the SubscribeRequest."""
        from neoncontract.messaging.v1 import messaging_pb2

        if not self._stream_name and not self._message_types:
            raise ValueError(
                "Either stream_name or message_types is required"
            )

        return messaging_pb2.SubscribeRequest(
            stream_name=self._stream_name or "",
            consumer_group=self._consumer_group or "",
            consumer_name=self._consumer_name or "",
            batch_size=self._batch_size,
            timeout_seconds=self._timeout_seconds,
            auto_ack=self._auto_ack,
            message_types=self._message_types,
        )
```

---

### 2.3 Missing Keepalive Configuration

**Issue:** gRPC keepalive settings not configurable in Python SDK.

**Go SDK Reference:**
```go
grpc.WithKeepaliveParams(keepalive.ClientParameters{
    Time:                config.KeepAlive,
    Timeout:             config.KeepAliveTimeout,
    PermitWithoutStream: true,
}),
```

**Resolution:** Add keepalive options to channel creation.

**Update `neonlink/client.py` `connect()`:**

```python
async def connect(self) -> None:
    """Establish connection to NeonLink server."""
    try:
        # Build channel options
        options = [
            ("grpc.keepalive_time_ms", int(self.config.keepalive_time * 1000)),
            ("grpc.keepalive_timeout_ms", int(self.config.keepalive_timeout * 1000)),
            ("grpc.keepalive_permit_without_calls", True),
            ("grpc.max_receive_message_length", self.config.max_recv_msg_size),
            ("grpc.max_send_message_length", self.config.max_send_msg_size),
        ]

        if self.config.tls and not self.config.tls.insecure:
            credentials = self._create_credentials()
            self._channel = grpc_aio.secure_channel(
                self.config.address,
                credentials,
                options=options,
            )
        else:
            self._channel = grpc_aio.insecure_channel(
                self.config.address,
                options=options,
            )

        from neoncontract.messaging.v1 import messaging_pb2_grpc
        self._stub = messaging_pb2_grpc.MessageBrokerStub(self._channel)
        self._connected = True
        logger.info(f"Connected to NeonLink at {self.config.address}")
    except Exception as e:
        raise ConnectionError(f"Failed to connect: {e}") from e
```

---

### 2.4 ~~Missing Handler Concurrency Config~~ RESOLVED

**Status:** ✅ RESOLVED - HandlerConcurrency has been intentionally removed from both Go and Python SDKs.

**Rationale:** NeonLink follows the "Dumb Pipe" architecture where scaling is achieved via horizontal scaling (Kubernetes replicas + consumer groups), not vertical scaling (internal worker pools). The HandlerConcurrency config was technical debt that implied functionality not implemented in the runtime. The SDK processes messages sequentially, which is correct for this architecture.

---

## 3. Test Fixes

### 3.1 Incorrect Mock Patch Paths

**Issue:** Tests patch `neonlink.client.messaging_pb2_grpc` but the client imports from `neoncontract.messaging.v1`.

**Current (Wrong):**
```python
with patch("neonlink.client.messaging_pb2_grpc") as mock_grpc:
```

**Correct:**
```python
with patch("neoncontract.messaging.v1.messaging_pb2_grpc") as mock_grpc:
```

**Files to fix:** `tests/test_client.py`

**Affected tests:**
- `test_connect_insecure`
- `test_get_stream_health_success`
- `test_connect_with_tls`
- `test_connect_with_insecure_tls`

**Fix for `test_connect_insecure`:**
```python
@pytest.mark.asyncio
async def test_connect_insecure(self, config):
    with patch("grpc.aio.insecure_channel") as mock_channel:
        mock_channel.return_value = MagicMock()

        with patch("neoncontract.messaging.v1.messaging_pb2_grpc") as mock_grpc:
            mock_grpc.MessageBrokerStub.return_value = MagicMock()

            client = NeonLinkClient(config)
            await client.connect()

            assert client._connected is True
            mock_channel.assert_called_once()
```

**Fix for `test_get_stream_health_success`:**
```python
@pytest.mark.asyncio
async def test_get_stream_health_success(self, mock_client):
    """Test get_stream_health returns health response."""
    mock_response = MagicMock()
    mock_response.stream_name = "test-stream"
    mock_response.length = 100
    mock_response.healthy = True

    mock_client._stub.GetStreamHealth = AsyncMock(return_value=mock_response)

    with patch("neoncontract.messaging.v1.messaging_pb2") as mock_pb2:
        mock_pb2.StreamHealthRequest.return_value = MagicMock()
        response = await mock_client.get_stream_health("test-stream")

    assert response.stream_name == "test-stream"
    assert response.length == 100
    assert response.healthy is True
```

---

### 3.2 Auto-reconnect Task Cleanup

**Issue:** `test_close_cancels_reconnect_task` expects `_reconnect_task` to be `None` after close, but `close()` doesn't set it to `None`.

**Current `close()` method:**
```python
async def close(self) -> None:
    if self._reconnect_task:
        self._reconnect_task.cancel()
        try:
            await self._reconnect_task
        except asyncio.CancelledError:
            pass
    # Missing: self._reconnect_task = None
```

**Fix:**
```python
async def close(self) -> None:
    """Close the connection."""
    if self._reconnect_task:
        self._reconnect_task.cancel()
        try:
            await self._reconnect_task
        except asyncio.CancelledError:
            pass
        self._reconnect_task = None  # Add this line
    if self._channel:
        await self._channel.close()
    self._connected = False
    logger.info("Disconnected from NeonLink")
```

---

## 4. Package Configuration

### 4.1 Direct Git Reference Issue

**Issue:** `pyproject.toml` uses direct git reference for `neoncontract` which hatchling doesn't allow by default.

**Current:**
```toml
dependencies = [
    "grpcio>=1.60.0",
    "grpcio-tools>=1.60.0",
    "protobuf>=4.25.0",
    "neoncontract @ git+https://github.com/LetA-Tech/mcfo-neoncontract.git@gen/python/v1.3.2#subdirectory=gen/python",
]
```

**Error:**
```
ValueError: Dependency #4 of field `project.dependencies` cannot be a direct reference 
unless field `tool.hatch.metadata.allow-direct-references` is set to `true`
```

**Resolution:** Add hatch configuration to allow direct references.

**Add to `pyproject.toml`:**
```toml
[tool.hatch.metadata]
allow-direct-references = true
```

**Alternative (Better for PyPI publishing):** Remove direct reference and document installation separately:

```toml
dependencies = [
    "grpcio>=1.60.0",
    "grpcio-tools>=1.60.0",
    "protobuf>=4.25.0",
]

[project.optional-dependencies]
neoncontract = [
    "neoncontract @ git+https://github.com/LetA-Tech/mcfo-neoncontract.git@gen/python/v1.3.2#subdirectory=gen/python",
]
```

---

## 5. Implementation Files

### Summary of Files to Create/Modify

| File | Action | Priority |
|------|--------|----------|
| `neonlink/circuit_breaker.py` | **CREATE** | Critical |
| `neonlink/helpers.py` | **REPLACE** | Critical |
| `neonlink/config.py` | **MODIFY** | High |
| `neonlink/client.py` | **MODIFY** | High |
| `neonlink/errors.py` | **MODIFY** | Medium |
| `neonlink/__init__.py` | **MODIFY** | Medium |
| `tests/test_client.py` | **MODIFY** | High |
| `pyproject.toml` | **MODIFY** | High |

### New Exports to Add to `__init__.py`

```python
# Circuit Breaker
from neonlink.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitState,
)

# Identity Options (from helpers.py)
from neonlink.helpers import (
    # Existing
    MessageBuilder,
    get_identity_context,
    get_webhook_ingress_context,
    get_active_job_type_name,
    get_job_type_message,
    # New
    SubscriptionBuilder,
    get_job_dispatch,
    get_etl_job_context,
    get_goal_event_context,
    with_entity_id,
    with_user_id,
    with_item_id,
    with_batch_id,
    with_job_id,
    with_request_id,
    with_event_id,
    with_connection_id,
    with_provider,
    with_trigger_source,
    with_data_type,
    with_source_system,
    with_idempotency_key_option,
)

__all__ = [
    # ... existing exports ...
    
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitBreakerConfig", 
    "CircuitBreakerOpenError",
    "CircuitState",
    
    # Subscription Builder
    "SubscriptionBuilder",
    
    # Job Dispatch helpers
    "get_job_dispatch",
    "get_etl_job_context",
    "get_goal_event_context",
    
    # Identity Options
    "with_entity_id",
    "with_user_id",
    "with_item_id",
    "with_batch_id",
    "with_job_id",
    "with_request_id",
    "with_event_id",
    "with_connection_id",
    "with_provider",
    "with_trigger_source",
    "with_data_type",
    "with_source_system",
    "with_idempotency_key_option",
]
```

### Add to `errors.py`

```python
class CircuitBreakerOpenError(NeonLinkError):
    """Raised when circuit breaker is open and rejecting requests."""
    pass
```

---

## Implementation Order

1. **Phase 1 - Critical (Do First)**
   - Create `circuit_breaker.py`
   - Update `helpers.py` with new MessageBuilder
   - Update `config.py` with new fields
   - Update `client.py` with circuit breaker integration

2. **Phase 2 - High Priority**
   - Fix test mock paths in `test_client.py`
   - Fix `pyproject.toml` direct reference
   - Update `__init__.py` exports

3. **Phase 3 - Medium Priority**
   - Add comprehensive tests for new features
   - Update documentation/examples

---

## Verification Checklist

After implementation, verify:

- [ ] All 85+ tests pass
- [ ] Circuit breaker opens after configured failures
- [ ] Circuit breaker recovers in half-open state
- [ ] MessageBuilder creates proper protobuf structure
- [ ] IdentityContext fields are properly set
- [ ] JWT token appears in metadata when configured
- [ ] Keepalive settings are applied to channel
- [ ] Package installs without errors
- [ ] Examples work against real NeonLink server
