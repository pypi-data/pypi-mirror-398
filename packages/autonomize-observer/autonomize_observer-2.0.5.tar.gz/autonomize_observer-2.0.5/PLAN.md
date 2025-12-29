# Autonomize Observer SDK v2.1 - Comprehensive Architecture Plan

## Executive Summary

Redesign the SDK to support **three distinct tracing/logging paradigms**:

1. **Legacy Streaming** (Current AI Studio) - Custom format to `genesis-traces-streaming`
2. **OTEL Tracing** (New) - Standard OTEL spans to `genesis-otel` via Logfire
3. **Audit Logging** (Current) - Compliance events to `genesis-audits`

The monitoring service will have 3 consumers to handle all formats during migration.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        AUTONOMIZE-OBSERVER SDK v2.1                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────────────┐   │
│  │  AI Studio Tracer │  │  OTEL Tracing     │  │  Audit Logging            │   │
│  │  (Legacy Format)  │  │  (Logfire/OTEL)   │  │  (Compliance)             │   │
│  ├───────────────────┤  ├───────────────────┤  ├───────────────────────────┤   │
│  │ • AIStudioTracer  │  │ • Logfire spans   │  │ • audit.log_create()      │   │
│  │ • BaseTracer iface│  │ • SpanProcessor   │  │ • audit.log_read()        │   │
│  │ • trace_start     │  │ • GenAI attrs     │  │ • audit.log_llm_*()       │   │
│  │ • span_start/end  │  │ • W3C trace IDs   │  │ • ActorContext            │   │
│  │ • trace_end       │  │                   │  │                           │   │
│  └─────────┬─────────┘  └─────────┬─────────┘  └─────────────┬─────────────┘   │
│            │                      │                          │                 │
│            ▼                      ▼                          ▼                 │
│  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────────────┐   │
│  │ KafkaTraceProducer│  │ KafkaSpanExporter │  │ KafkaExporter             │   │
│  │ (Streaming Events)│  │ (OTEL JSON)       │  │ (Audit Events)            │   │
│  └─────────┬─────────┘  └─────────┬─────────┘  └─────────────┬─────────────┘   │
│            │                      │                          │                 │
│            ▼                      ▼                          ▼                 │
│  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────────────┐   │
│  │ genesis-traces-   │  │ genesis-otel      │  │ genesis-audits            │   │
│  │ streaming         │  │                   │  │                           │   │
│  └───────────────────┘  └───────────────────┘  └───────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│              GENESIS-SERVICE-MONITORING-AND-OBSERVABILITY                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────────────┐   │
│  │ Legacy Consumer   │  │ OTEL Consumer     │  │ Audit Consumer            │   │
│  │ (Current)         │  │ (New)             │  │ (New)                     │   │
│  ├───────────────────┤  ├───────────────────┤  ├───────────────────────────┤   │
│  │ • trace_start     │  │ • OTLP JSON parse │  │ • Audit event parse       │   │
│  │ • span_start/end  │  │ • GenAI attrs     │  │ • Compliance tracking     │   │
│  │ • trace_end       │  │ • W3C correlation │  │ • Actor context           │   │
│  │ • llm_call_*      │  │ • Cost from attrs │  │ • Immutable append        │   │
│  └─────────┬─────────┘  └─────────┬─────────┘  └─────────────┬─────────────┘   │
│            │                      │                          │                 │
│            └──────────────────────┼──────────────────────────┘                 │
│                                   ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         MongoDB Collections                              │   │
│  ├───────────────────┬───────────────────┬───────────────────┬─────────────┤   │
│  │ traces            │ observations      │ audits            │ metrics     │   │
│  │ (unified)         │ (spans)           │ (compliance)      │ (agg)       │   │
│  └───────────────────┴───────────────────┴───────────────────┴─────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Module Structure

```
autonomize_observer/
├── __init__.py                    # Main exports, init()
├── core/
│   ├── config.py                  # KafkaConfig, ObserverConfig
│   └── exceptions.py              # Exception hierarchy
│
├── audit/                         # ✅ EXISTS - Keep as-is
│   ├── context.py                 # ActorContext, JWT parsing
│   └── logger.py                  # AuditLogger, log_* methods
│
├── tracing/
│   ├── __init__.py                # Exports
│   ├── logfire_integration.py     # ✅ EXISTS - Extend
│   ├── kafka_span_processor.py    # 🆕 NEW - OTEL SpanProcessor → Kafka
│   ├── ai_studio_tracer.py        # 🆕 NEW - Langflow BaseTracer impl
│   ├── kafka_trace_producer.py    # 🆕 NEW - Streaming event producer
│   └── trace_context.py           # 🆕 NEW - StreamingTraceContext
│
├── schemas/
│   ├── base.py                    # ✅ EXISTS - BaseEvent
│   ├── audit.py                   # ✅ EXISTS - AuditEvent
│   ├── enums.py                   # ✅ EXISTS - All enums
│   ├── otel.py                    # 🆕 NEW - OTELSpan schema
│   ├── streaming.py               # 🆕 NEW - TraceEvent, SpanEvent schemas
│   └── genai.py                   # 🆕 NEW - GenAI attribute builders
│
├── exporters/
│   ├── base.py                    # ✅ EXISTS - BaseExporter
│   ├── kafka.py                   # ✅ EXISTS - Audit event exporter
│   └── kafka_otel.py              # 🆕 NEW - OTEL span exporter
│
├── integrations/
│   ├── __init__.py                # ✅ EXISTS
│   ├── fastapi.py                 # ✅ EXISTS - JWT middleware
│   └── langflow.py                # ✅ EXISTS - Logfire decorators
│
└── cost/
    └── pricing.py                 # ✅ EXISTS - genai-prices wrapper
```

---

## Phase 1: AI Studio Tracer (Legacy Format)

**Goal**: Restore `AgentTracer` functionality for AI Studio compatibility

### 1.1 Streaming Event Schemas (`schemas/streaming.py`)

```python
from enum import Enum
from pydantic import BaseModel

class StreamingEventType(str, Enum):
    TRACE_START = "trace_start"
    TRACE_END = "trace_end"
    SPAN_START = "span_start"
    SPAN_END = "span_end"
    LLM_CALL_START = "llm_call_start"
    LLM_CALL_END = "llm_call_end"
    CUSTOM = "custom"

class TraceEvent(BaseModel):
    """Streaming trace event for Kafka."""
    event_type: StreamingEventType
    trace_id: str
    timestamp: str
    flow_id: str | None = None
    span_id: str | None = None
    parent_span_id: str | None = None
    component_name: str | None = None
    component_type: str | None = None
    duration_ms: float | None = None
    input_data: dict | None = None
    output_data: dict | None = None
    error: str | None = None
    metadata: dict = {}

    # User context
    user_id: str | None = None
    session_id: str | None = None
    project_name: str = "GenesisStudio"

    @classmethod
    def create_trace_start(cls, trace_id, flow_id, flow_name, **kwargs):
        ...

    @classmethod
    def create_span_start(cls, trace_id, span_id, component_name, **kwargs):
        ...
```

### 1.2 Kafka Trace Producer (`tracing/kafka_trace_producer.py`)

```python
class KafkaTraceProducer:
    """Sends streaming trace events to Kafka."""

    def __init__(
        self,
        bootstrap_servers: str,
        topic: str = "genesis-traces-streaming",
        security_protocol: str = "SASL_SSL",
        sasl_mechanism: str = "PLAIN",
        sasl_username: str | None = None,
        sasl_password: str | None = None,
    ):
        ...

    def send_trace_start(self, trace_id, flow_id, flow_name, **kwargs) -> bool:
        ...

    def send_span_start(self, trace_id, span_id, component_name, **kwargs) -> bool:
        ...

    def send_span_end(self, trace_id, span_id, duration_ms, **kwargs) -> bool:
        ...

    def send_trace_end(self, trace_id, duration_ms, **kwargs) -> bool:
        ...

    def flush(self, timeout: float = 5.0) -> int:
        ...
```

### 1.3 AgentTracer (`tracing/agent_tracer.py`)

**CRITICAL**: This class must maintain EXACT API compatibility with AI Studio.
AI Studio imports: `from autonomize_observer.tracing import AgentTracer`
NO CHANGES to AI Studio required!

```python
class AgentTracer:
    """
    Streaming tracer for AI Studio (Langflow) integration.

    Sends streaming events to genesis-traces-streaming Kafka topic.

    IMPORTANT: Do not change the constructor signature or method signatures!
    AI Studio depends on this exact interface.

    AI Studio calls this with:
        tracer = AgentTracer(
            trace_name=trace_context.run_name,
            trace_id=trace_context.run_id,           # UUID object
            flow_id=str(trace_context.run_id),
            project_name=trace_context.project_name,
            user_id=trace_context.user_id,
            session_id=trace_context.session_id,
            **self._tracing_config,  # Kafka config from env vars
        )
        tracer.start_trace()
    """

    def __init__(
        self,
        trace_name: str,                                    # Required
        trace_id: UUID,                                     # Required (UUID object)
        flow_id: str,                                       # Required
        project_name: str = "GenesisStudio",
        user_id: str | None = None,
        session_id: str | None = None,
        # Kafka config - passed from AI Studio's _tracing_config
        kafka_bootstrap_servers: str | None = None,
        kafka_topic: str = "genesis-traces-streaming",
        kafka_username: str | None = None,
        kafka_password: str | None = None,
        security_protocol: str = "SASL_SSL",
        sasl_mechanism: str = "PLAIN",
        **kwargs,  # Accept extra kwargs for forward compatibility
    ):
        self.trace_name = trace_name
        self.trace_id = trace_id
        self.flow_id = flow_id
        self.project_name = project_name
        self.user_id = user_id
        self.session_id = session_id

        # Initialize Kafka producer
        self._producer = KafkaTraceProducer(
            bootstrap_servers=kafka_bootstrap_servers,
            topic=kafka_topic,
            kafka_username=kafka_username,
            kafka_password=kafka_password,
            security_protocol=security_protocol,
            sasl_mechanism=sasl_mechanism,
        )

        # Track spans
        self._spans: dict[str, dict] = {}
        self._start_time = time.time()
        self._ready = kafka_bootstrap_servers is not None

    @property
    def ready(self) -> bool:
        """Check if tracer is ready - AI Studio checks this."""
        return self._ready

    def start_trace(self) -> None:
        """Send trace_start event - AI Studio calls this after construction."""
        if not self._ready:
            return
        self._producer.send_trace_start(
            trace_id=str(self.trace_id),
            flow_id=self.flow_id,
            flow_name=self.trace_name,
            user_id=self.user_id,
            session_id=self.session_id,
            metadata={"project_name": self.project_name},
        )

    def add_trace(
        self,
        trace_id: str,          # This is span_id/component_id
        trace_name: str,        # Component name
        trace_type: str,        # Component type
        inputs: dict[str, Any],
        metadata: dict[str, Any] | None = None,
        vertex: Any = None,     # Langflow Vertex object
    ) -> None:
        """Send span_start event for a component."""
        if not self._ready:
            return

        span_info = {
            "span_id": trace_id,
            "name": trace_name,
            "type": trace_type,
            "start_time": time.time(),
        }
        self._spans[trace_id] = span_info

        self._producer.send_span_start(
            trace_id=str(self.trace_id),
            span_id=trace_id,
            component_name=trace_name,
            component_type=trace_type,
            input_data=inputs,
            metadata=metadata,
        )

    def end_trace(
        self,
        trace_id: str,          # span_id
        trace_name: str,
        outputs: dict[str, Any] | None = None,
        error: Exception | None = None,
        logs: Sequence = (),
    ) -> None:
        """Send span_end event for a component."""
        if not self._ready:
            return

        span_info = self._spans.pop(trace_id, None)
        duration_ms = 0.0
        if span_info:
            duration_ms = (time.time() - span_info["start_time"]) * 1000

        self._producer.send_span_end(
            trace_id=str(self.trace_id),
            span_id=trace_id,
            duration_ms=duration_ms,
            output_data=outputs,
            error=str(error) if error else None,
            metadata={"component_name": trace_name},
        )

    def end(
        self,
        inputs: dict[str, Any],
        outputs: dict[str, Any],
        error: Exception | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Send trace_end event - called when flow completes."""
        if not self._ready:
            return

        duration_ms = (time.time() - self._start_time) * 1000

        self._producer.send_trace_end(
            trace_id=str(self.trace_id),
            duration_ms=duration_ms,
            metadata={
                "flow_id": self.flow_id,
                "flow_name": self.trace_name,
                "project_name": self.project_name,
                "status": "error" if error else "success",
                **(metadata or {}),
            },
            error=str(error) if error else None,
        )

        # Flush pending messages
        self._producer.flush()

    def get_langchain_callback(self) -> Any:
        """Return LangChain callback handler if needed."""
        return None
```

### 1.4 Update Exports (`tracing/__init__.py`)

```python
from autonomize_observer.tracing.logfire_integration import (
    configure_logfire,
    get_logfire,
    instrument_llms,
    instrument_web_framework,
    instrument_database,
)
from autonomize_observer.tracing.ai_studio_tracer import AIStudioTracer
from autonomize_observer.tracing.kafka_trace_producer import KafkaTraceProducer

# Backwards compatibility alias
AgentTracer = AIStudioTracer

__all__ = [
    "configure_logfire",
    "get_logfire",
    "instrument_llms",
    "instrument_web_framework",
    "instrument_database",
    "AIStudioTracer",
    "AgentTracer",  # Alias for backwards compatibility
    "KafkaTraceProducer",
]
```

---

## Phase 2: OTEL Tracing (Logfire + Kafka)

**Goal**: Add OTEL-native span export to Kafka alongside Logfire

### 2.1 OTEL Span Schema (`schemas/otel.py`)

```python
from dataclasses import dataclass
from enum import IntEnum

class SpanKind(IntEnum):
    INTERNAL = 0
    SERVER = 1
    CLIENT = 2
    PRODUCER = 3
    CONSUMER = 4

class SpanStatusCode(IntEnum):
    UNSET = 0
    OK = 1
    ERROR = 2

@dataclass
class OTELSpan:
    """W3C/OTEL compliant span structure."""
    trace_id: str           # 32 hex chars
    span_id: str            # 16 hex chars
    parent_span_id: str | None
    name: str
    kind: SpanKind
    start_time_unix_nano: int
    end_time_unix_nano: int
    status_code: SpanStatusCode
    status_message: str | None
    attributes: dict[str, Any]
    events: list[dict] = field(default_factory=list)
    links: list[dict] = field(default_factory=list)

    # Resource attributes
    service_name: str
    service_version: str | None = None

    def to_otlp_json(self) -> dict:
        """Convert to OTLP JSON format."""
        return {
            "traceId": self.trace_id,
            "spanId": self.span_id,
            "parentSpanId": self.parent_span_id,
            "name": self.name,
            "kind": self.kind,
            "startTimeUnixNano": str(self.start_time_unix_nano),
            "endTimeUnixNano": str(self.end_time_unix_nano),
            "status": {
                "code": self.status_code,
                "message": self.status_message,
            },
            "attributes": [
                {"key": k, "value": self._encode_value(v)}
                for k, v in self.attributes.items()
            ],
            "events": self.events,
            "links": self.links,
        }
```

### 2.2 GenAI Attributes (`schemas/genai.py`)

```python
class GenAIAttributes:
    """Builder for gen_ai.* semantic convention attributes."""

    @staticmethod
    def for_llm_call(
        provider: str,
        model: str,
        operation: str = "chat",
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        cost: float | None = None,
    ) -> dict[str, Any]:
        attrs = {
            "gen_ai.operation.name": operation,
            "gen_ai.system": provider,  # openai, anthropic, etc.
            "gen_ai.request.model": model,
        }
        if input_tokens is not None:
            attrs["gen_ai.usage.input_tokens"] = input_tokens
        if output_tokens is not None:
            attrs["gen_ai.usage.output_tokens"] = output_tokens
        if temperature is not None:
            attrs["gen_ai.request.temperature"] = temperature
        if max_tokens is not None:
            attrs["gen_ai.request.max_tokens"] = max_tokens
        if cost is not None:
            attrs["gen_ai.usage.cost"] = cost
        return attrs

    @staticmethod
    def for_flow(
        flow_id: str,
        flow_name: str,
        session_id: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        attrs = {
            "langflow.flow.id": flow_id,
            "langflow.flow.name": flow_name,
        }
        if session_id:
            attrs["langflow.session.id"] = session_id
        if user_id:
            attrs["langflow.user.id"] = user_id
        return attrs

    @staticmethod
    def for_component(
        component_type: str,
        component_name: str | None = None,
        component_index: int | None = None,
    ) -> dict[str, Any]:
        attrs = {
            "langflow.component.type": component_type,
        }
        if component_name:
            attrs["langflow.component.name"] = component_name
        if component_index is not None:
            attrs["langflow.component.index"] = component_index
        return attrs
```

### 2.3 Kafka Span Exporter (`exporters/kafka_otel.py`)

```python
class KafkaSpanExporter:
    """Exports OTEL spans to Kafka in OTLP JSON format."""

    def __init__(
        self,
        config: KafkaConfig,
        topic: str = "genesis-otel",
    ):
        self.topic = topic
        self._producer = None
        self._config = config

    def initialize(self) -> None:
        from confluent_kafka import Producer
        self._producer = Producer({
            "bootstrap.servers": self._config.bootstrap_servers,
            ...
        })

    def export_span(self, span: OTELSpan) -> ExportResult:
        """Export single span to Kafka."""
        message = {
            "resourceSpans": [{
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": span.service_name}},
                    ]
                },
                "scopeSpans": [{
                    "scope": {"name": "autonomize-observer"},
                    "spans": [span.to_otlp_json()]
                }]
            }]
        }
        self._producer.produce(
            topic=self.topic,
            key=span.trace_id,
            value=json.dumps(message),
        )
        return ExportResult.ok(events_exported=1)
```

### 2.4 Kafka Span Processor (`tracing/kafka_span_processor.py`)

```python
from opentelemetry.sdk.trace import SpanProcessor, ReadableSpan

class KafkaSpanProcessor(SpanProcessor):
    """OTEL SpanProcessor that exports completed spans to Kafka."""

    def __init__(
        self,
        exporter: KafkaSpanExporter,
        batch_size: int = 100,
        flush_interval_ms: int = 5000,
    ):
        self.exporter = exporter
        self.batch_size = batch_size
        self._pending: list[OTELSpan] = []
        self._lock = threading.Lock()

    def on_start(self, span: ReadableSpan, parent_context) -> None:
        """Called when span starts - no-op for batch export."""
        pass

    def on_end(self, span: ReadableSpan) -> None:
        """Called when span ends - queue for export."""
        otel_span = self._convert_span(span)
        with self._lock:
            self._pending.append(otel_span)
            if len(self._pending) >= self.batch_size:
                self._flush()

    def _convert_span(self, span: ReadableSpan) -> OTELSpan:
        """Convert OTEL SDK span to our OTELSpan."""
        return OTELSpan(
            trace_id=format(span.context.trace_id, '032x'),
            span_id=format(span.context.span_id, '016x'),
            parent_span_id=format(span.parent.span_id, '016x') if span.parent else None,
            name=span.name,
            kind=SpanKind(span.kind.value),
            start_time_unix_nano=span.start_time,
            end_time_unix_nano=span.end_time,
            status_code=SpanStatusCode(span.status.status_code.value),
            status_message=span.status.description,
            attributes=dict(span.attributes or {}),
            events=[...],
            links=[...],
            service_name=span.resource.attributes.get("service.name", "unknown"),
        )

    def _flush(self) -> None:
        """Flush pending spans to Kafka."""
        with self._lock:
            for span in self._pending:
                self.exporter.export_span(span)
            self._pending.clear()

    def shutdown(self) -> None:
        self._flush()
        self.exporter.shutdown()

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        self._flush()
        return True
```

### 2.5 Update Logfire Configuration

```python
def configure_logfire(
    service_name: str = "autonomize-observer",
    service_version: str = "2.0.0",
    environment: str | None = None,
    send_to_logfire: bool = False,
    # NEW: Kafka OTEL export
    kafka_config: KafkaConfig | None = None,
    kafka_otel_enabled: bool = False,
    kafka_otel_topic: str = "genesis-otel",
    **kwargs,
) -> logfire_module.Logfire:
    """Configure Logfire with optional Kafka OTEL export."""

    additional_processors = kwargs.pop("additional_span_processors", []) or []

    # Add Kafka span processor if configured
    if kafka_otel_enabled and kafka_config:
        exporter = KafkaSpanExporter(kafka_config, topic=kafka_otel_topic)
        exporter.initialize()
        processor = KafkaSpanProcessor(exporter)
        additional_processors.append(processor)

    # Configure Logfire
    logfire.configure(
        service_name=service_name,
        service_version=service_version,
        send_to_logfire=send_to_logfire,
        additional_span_processors=additional_processors,
        **kwargs,
    )
```

---

## Phase 3: Update Main SDK Initialization

### 3.1 Update `__init__.py`

```python
def init(
    service_name: str,
    service_version: str = "2.0.0",
    environment: str = "production",

    # Kafka configuration
    kafka_config: KafkaConfig | None = None,

    # Legacy streaming (for AI Studio)
    kafka_streaming_enabled: bool = False,
    kafka_streaming_topic: str = "genesis-traces-streaming",

    # OTEL export
    kafka_otel_enabled: bool = False,
    kafka_otel_topic: str = "genesis-otel",

    # Audit logging
    kafka_audit_enabled: bool = False,
    kafka_audit_topic: str = "genesis-audits",

    # Logfire
    send_to_logfire: bool = False,

    # LLM instrumentation
    instrument_openai: bool = True,
    instrument_anthropic: bool = True,

    # Keycloak
    keycloak_claim_mappings: dict | None = None,
) -> None:
    """Initialize the Autonomize Observer SDK.

    Supports three modes:
    1. Legacy streaming (kafka_streaming_enabled) - For AI Studio
    2. OTEL tracing (kafka_otel_enabled) - Standard OTEL spans
    3. Audit logging (kafka_audit_enabled) - Compliance events
    """
    global _initialized, _kafka_exporter, _audit_logger

    # Configure Logfire with optional OTEL Kafka export
    configure_logfire(
        service_name=service_name,
        service_version=service_version,
        environment=environment,
        send_to_logfire=send_to_logfire,
        kafka_config=kafka_config if kafka_otel_enabled else None,
        kafka_otel_enabled=kafka_otel_enabled,
        kafka_otel_topic=kafka_otel_topic,
    )

    # Instrument LLMs
    if instrument_openai or instrument_anthropic:
        instrument_llms(openai=instrument_openai, anthropic=instrument_anthropic)

    # Setup audit Kafka exporter
    if kafka_audit_enabled and kafka_config:
        _kafka_exporter = KafkaExporter(kafka_config)
        _kafka_exporter.initialize()

    # Setup audit logger
    _audit_logger = AuditLogger(
        service_name=service_name,
        exporter=_kafka_exporter,
    )

    _initialized = True
```

---

## Phase 4: Testing

### Test Files to Create

1. `tests/test_ai_studio_tracer.py` - AIStudioTracer tests
2. `tests/test_kafka_trace_producer.py` - Streaming producer tests
3. `tests/test_streaming_schemas.py` - TraceEvent schema tests
4. `tests/test_otel_schemas.py` - OTELSpan schema tests
5. `tests/test_genai_attributes.py` - GenAI attribute tests
6. `tests/test_kafka_span_processor.py` - SpanProcessor tests
7. `tests/test_kafka_otel_exporter.py` - OTEL exporter tests

### Coverage Requirements

- Maintain 98%+ test coverage
- Mock Kafka producer for unit tests
- Test all event types and edge cases

---

## File Summary

### New Files (12)

| File | Purpose |
|------|---------|
| `schemas/streaming.py` | TraceEvent, streaming event schemas |
| `schemas/otel.py` | OTELSpan, OTLP JSON serialization |
| `schemas/genai.py` | GenAI semantic convention builders |
| `tracing/ai_studio_tracer.py` | Langflow BaseTracer implementation |
| `tracing/kafka_trace_producer.py` | Streaming event Kafka producer |
| `tracing/trace_context.py` | StreamingTraceContext |
| `tracing/kafka_span_processor.py` | OTEL SpanProcessor for Kafka |
| `exporters/kafka_otel.py` | OTEL span Kafka exporter |
| `tests/test_ai_studio_tracer.py` | AIStudioTracer tests |
| `tests/test_kafka_trace_producer.py` | Producer tests |
| `tests/test_otel_*.py` | OTEL-related tests |
| `tests/test_streaming_*.py` | Streaming-related tests |

### Modified Files (4)

| File | Changes |
|------|---------|
| `tracing/__init__.py` | Export AIStudioTracer, AgentTracer alias |
| `tracing/logfire_integration.py` | Add Kafka span processor support |
| `__init__.py` | Update init() for all modes |
| `core/config.py` | Add topic fields to KafkaConfig |

---

## Migration Path

### For AI Studio

1. Update AI Studio's TracingService to import from new SDK:
```python
from autonomize_observer.tracing import AIStudioTracer as AgentTracer
```

2. Or use the backwards-compatible alias:
```python
from autonomize_observer.tracing import AgentTracer  # Still works
```

### For New OTEL Services

```python
from autonomize_observer import init

init(
    service_name="my-service",
    kafka_config=KafkaConfig(bootstrap_servers="kafka:9092"),
    kafka_otel_enabled=True,
    kafka_otel_topic="genesis-otel",
)
```

---

## Monitoring Service Changes (Future)

The monitoring service will need 3 consumers:

1. **Legacy Consumer** (exists) - `genesis-traces-streaming`
2. **OTEL Consumer** (new) - `genesis-otel` - Parse OTLP JSON
3. **Audit Consumer** (new) - `genesis-audits` - Compliance events

These will write to unified MongoDB collections.

---

## Open Questions

1. **Batch size for OTEL export?** Default 100 spans before flush
2. **Flush interval?** Default 5 seconds
3. **Should LLM content be in OTEL spans?** Make it opt-in for privacy
4. **Cost calculation in OTEL?** Add `gen_ai.usage.cost` attribute

---

## Timeline Estimate

- **Phase 1** (AI Studio Tracer): Core functionality
- **Phase 2** (OTEL Export): Standard OTEL support
- **Phase 3** (Integration): SDK initialization updates
- **Phase 4** (Testing): Comprehensive tests
