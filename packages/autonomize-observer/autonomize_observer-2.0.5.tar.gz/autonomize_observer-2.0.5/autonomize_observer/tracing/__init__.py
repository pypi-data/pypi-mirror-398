"""Tracing module - wraps Logfire for distributed tracing and provides tracers."""

# Import from centralized imports module
from autonomize_observer.core.imports import LOGFIRE_AVAILABLE

# Import AgentTracer and related components
from autonomize_observer.tracing.agent_tracer import AgentTracer, StreamingTraceContext

# Import base tracer protocols
from autonomize_observer.tracing.base import BaseTracer, SpanTracer, TracerMixin

# Import factory
from autonomize_observer.tracing.factory import TracerFactory
from autonomize_observer.tracing.kafka_trace_producer import (
    KAFKA_AVAILABLE,
    KafkaTraceProducer,
)
from autonomize_observer.tracing.logfire_integration import (
    configure_logfire,
    get_logfire,
    instrument_database,
    instrument_llms,
    instrument_web_framework,
)

# Import OTEL utilities
from autonomize_observer.tracing.otel_utils import OTELManager

# Import utilities
from autonomize_observer.tracing.utils import (
    clean_model_name,
    guess_provider_from_model,
    infer_component_type,
    safe_serialize,
)

# Import WorkflowTracer for general step-based tracing
from autonomize_observer.tracing.workflow_tracer import (
    Step,
    StepMetrics,
    WorkflowTracer,
    trace_workflow,
)

__all__ = [
    # Base protocols
    "BaseTracer",
    "SpanTracer",
    "TracerMixin",
    # Factory
    "TracerFactory",
    # Logfire integration
    "configure_logfire",
    "get_logfire",
    "instrument_llms",
    "instrument_web_framework",
    "instrument_database",
    # AgentTracer (for AI Studio and legacy streaming)
    "AgentTracer",
    "StreamingTraceContext",
    # WorkflowTracer (for general step-based tracing)
    "WorkflowTracer",
    "Step",
    "StepMetrics",
    "trace_workflow",
    # OTEL utilities
    "OTELManager",
    # Kafka producer
    "KafkaTraceProducer",
    "KAFKA_AVAILABLE",
    # OTEL/Logfire availability
    "LOGFIRE_AVAILABLE",
    # Utilities
    "clean_model_name",
    "guess_provider_from_model",
    "infer_component_type",
    "safe_serialize",
]
