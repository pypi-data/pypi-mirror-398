"""AgentTracer for AI Studio (Langflow) integration.

This tracer implements streaming/incremental span sending:
1. Start trace context
2. Send individual spans as they start/end
3. No massive memory accumulation
4. Real-time monitoring capabilities

Supports dual export:
- Legacy streaming format to Kafka (for AI Studio)
- OTEL format via Logfire (for modern observability)

IMPORTANT: This class maintains API compatibility with AI Studio.
Do not change the constructor signature or method signatures!
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any, Sequence
from uuid import UUID

from autonomize_observer.core.config import KafkaConfig
from autonomize_observer.cost.pricing import calculate_cost
from autonomize_observer.tracing.kafka_trace_producer import (
    KAFKA_AVAILABLE,
    KafkaTraceProducer,
)
from autonomize_observer.tracing.otel_utils import OTELManager
from autonomize_observer.tracing.utils.model_utils import (
    clean_model_name,
    guess_provider_from_model,
    infer_component_type,
)
from autonomize_observer.tracing.utils.serialization import safe_serialize
from autonomize_observer.tracing.utils.token_extractors import TokenExtractorChain

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class StreamingTraceContext:
    """Context for managing streaming trace state."""

    def __init__(
        self,
        trace_id: str,
        flow_id: str,
        trace_name: str,
        project_name: str = "GenesisStudio",
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> None:
        self.trace_id = trace_id
        self.flow_id = flow_id
        self.trace_name = trace_name
        self.project_name = project_name
        self.user_id = user_id
        self.session_id = session_id
        self.start_time = time.time()

        # Active spans
        self._active_spans: dict[str, dict[str, Any]] = {}
        self._completed_spans: list[str] = []

        # Trace-level metrics
        self.tags: dict[str, str] = {}
        self.params: dict[str, Any] = {}
        self.metrics: dict[str, float] = {}

        # Token/cost aggregation
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0

    def add_span(self, span_id: str, span_info: dict[str, Any]) -> None:
        """Add an active span."""
        self._active_spans[span_id] = span_info

    def complete_span(self, span_id: str) -> dict[str, Any] | None:
        """Mark a span as completed and return its info."""
        span_info = self._active_spans.pop(span_id, None)
        if span_info:
            self._completed_spans.append(span_id)
        return span_info

    def get_span_count(self) -> int:
        """Get total number of spans (active + completed)."""
        return len(self._active_spans) + len(self._completed_spans)

    def update_tags(self, tags: dict[str, str]) -> None:
        """Update trace tags."""
        self.tags.update(tags)

    def set_param(self, key: str, value: Any) -> None:
        """Set a trace parameter."""
        self.params[key] = value

    def set_metric(self, key: str, value: float) -> None:
        """Set a trace metric."""
        self.metrics[key] = value

    def add_token_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        cost: float,
    ) -> None:
        """Add token usage to trace totals."""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost += cost


class AgentTracer:
    """Streaming Agent tracer that sends spans incrementally.

    Workflow:
    1. start_trace() - Initialize trace context, send trace_start event
    2. add_trace() - Start component span, send span_start event
    3. end_trace() - End component span, send span_end event
    4. end() - Finalize trace, send trace_end event

    IMPORTANT: Do not change the constructor signature!
    AI Studio depends on this exact interface.
    """

    def __init__(
        self,
        trace_name: str,
        trace_id: UUID,
        flow_id: str,
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
        # OTEL/Logfire config (new in v2.0)
        enable_otel: bool = False,
        otel_service_name: str | None = None,
        send_to_logfire: bool = False,
        # New config objects (v2.0) - alternative to individual params
        kafka_config: KafkaConfig | None = None,
        otel_manager: OTELManager | None = None,
        **kwargs: Any,  # Accept extra kwargs for forward compatibility
    ) -> None:
        """Initialize streaming tracer.

        Args:
            trace_name: Name of the trace/flow
            trace_id: UUID for the trace
            flow_id: Flow identifier
            project_name: Project name
            user_id: Optional user ID
            session_id: Optional session ID
            kafka_bootstrap_servers: Kafka broker addresses (legacy, prefer kafka_config)
            kafka_topic: Kafka topic for trace events (legacy, prefer kafka_config)
            kafka_username: SASL username (legacy, prefer kafka_config)
            kafka_password: SASL password (legacy, prefer kafka_config)
            security_protocol: Security protocol (legacy, prefer kafka_config)
            sasl_mechanism: SASL mechanism (legacy, prefer kafka_config)
            enable_otel: Enable OTEL tracing via Logfire (default: False)
            otel_service_name: Service name for OTEL spans
            send_to_logfire: Send traces to Logfire cloud (default: False)
            kafka_config: KafkaConfig object (v2.0 - preferred over individual params)
            otel_manager: Shared OTELManager instance (v2.0 - for DI)
            **kwargs: Additional arguments (ignored for forward compatibility)
        """
        self.trace_name = self._clean_trace_name(trace_name)
        self.trace_id = trace_id
        self.flow_id = flow_id
        self.project_name = project_name
        self.user_id = user_id
        self.session_id = session_id

        # Kafka configuration - prefer KafkaConfig, fallback to individual params
        if kafka_config:
            self._kafka_bootstrap_servers = kafka_config.bootstrap_servers
            self._kafka_topic = kafka_config.trace_topic
            self._kafka_username = kafka_config.sasl_username
            self._kafka_password = kafka_config.sasl_password
            self._security_protocol = kafka_config.security_protocol
            self._sasl_mechanism = kafka_config.sasl_mechanism
        else:
            self._kafka_bootstrap_servers = kafka_bootstrap_servers
            self._kafka_topic = kafka_topic
            self._kafka_username = kafka_username
            self._kafka_password = kafka_password
            self._security_protocol = security_protocol
            self._sasl_mechanism = sasl_mechanism

        # OTEL configuration - use injected OTELManager or create one
        self._otel_manager = otel_manager
        self._enable_otel = enable_otel or (otel_manager is not None)
        self._otel_service_name = otel_service_name or project_name
        self._send_to_logfire = send_to_logfire

        # Token extraction chain (Strategy pattern)
        self._token_extractor = TokenExtractorChain()

        # Initialize Kafka producer
        self._kafka_producer: KafkaTraceProducer | None = None
        self._ready = False

        # Trace context
        self._trace_context: StreamingTraceContext | None = None

        # Active OTEL spans (for correlation)
        self._otel_trace_span: Any = None
        self._otel_spans: dict[str, Any] = {}

        # Setup Kafka producer
        self._setup_kafka_producer()

        # Setup OTEL if enabled and no manager was injected
        if self._enable_otel and not self._otel_manager:
            self._setup_otel()

        logger.info(f"AgentTracer initialized for flow: {flow_id}")

    def _clean_trace_name(self, trace_name: str) -> str:
        """Clean up trace name by removing UUIDs and timestamps."""
        if not trace_name:
            return "unknown"

        # Split by " - " and take the meaningful part
        parts = trace_name.split(" - ")
        if len(parts) >= 2:
            # Usually format is "Flow Name - UUID"
            return parts[0].strip()
        return trace_name.strip()

    @property
    def ready(self) -> bool:
        """Check if tracer is ready - AI Studio checks this."""
        return self._ready

    def _setup_kafka_producer(self) -> None:
        """Setup Kafka producer with authentication."""
        if not KAFKA_AVAILABLE:
            logger.warning("Kafka not available - confluent-kafka not installed")
            self._ready = False
            return

        if not self._kafka_bootstrap_servers:
            logger.warning("Kafka bootstrap servers not configured")
            self._ready = False
            return

        try:
            self._kafka_producer = KafkaTraceProducer(
                bootstrap_servers=self._kafka_bootstrap_servers,
                topic=self._kafka_topic,
                kafka_username=self._kafka_username,
                kafka_password=self._kafka_password,
                security_protocol=self._security_protocol,
                sasl_mechanism=self._sasl_mechanism,
            )
            self._ready = True
            logger.debug("Kafka producer initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Kafka producer: {e}")
            self._ready = False

    def _setup_otel(self) -> None:
        """Setup OTEL tracing via OTELManager."""
        try:
            self._otel_manager = OTELManager(
                service_name=self._otel_service_name,
                send_to_logfire=self._send_to_logfire,
            )
            logger.debug("OTELManager initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize OTELManager: {e}")
            self._otel_manager = None
            self._enable_otel = False

    @property
    def _otel_available(self) -> bool:
        """Check if OTEL is available and configured."""
        return (
            self._enable_otel
            and self._otel_manager is not None
            and self._otel_manager.is_available
        )

    def start_trace(self) -> None:
        """Start the trace context and send trace_start event.

        AI Studio calls this after construction.
        """
        # Initialize trace context regardless of Kafka status
        self._trace_context = StreamingTraceContext(
            trace_id=str(self.trace_id),
            flow_id=self.flow_id,
            trace_name=self.trace_name,
            project_name=self.project_name,
            user_id=self.user_id,
            session_id=self.session_id,
        )

        # Start OTEL parent span if enabled
        if self._otel_available and self._otel_manager:
            try:
                # Create a parent span for the entire trace
                self._otel_trace_span = self._otel_manager.start_span(
                    f"trace:{self.trace_name}",
                    tags=["flow", "trace"],
                    flow_id=self.flow_id,
                    flow_name=self.trace_name,
                    trace_id=str(self.trace_id),
                    user_id=self.user_id,
                    session_id=self.session_id,
                    project_name=self.project_name,
                )
                logger.debug("Started OTEL trace span")
            except Exception as e:
                logger.warning(f"Failed to start OTEL trace span: {e}")

        # Send Kafka trace_start event
        if self._ready and self._kafka_producer:
            try:
                success = self._kafka_producer.send_trace_start(
                    trace_id=self._trace_context.trace_id,
                    flow_id=self._trace_context.flow_id,
                    flow_name=self._trace_context.trace_name,
                    user_id=self._trace_context.user_id,
                    session_id=self._trace_context.session_id,
                    project_name=self._trace_context.project_name,
                    metadata={
                        "environment": "production",
                    },
                )
                if success:
                    logger.info(
                        f"Started streaming trace: {self._trace_context.trace_id}"
                    )
                else:
                    logger.warning("Failed to send trace_start event")
            except Exception as e:
                logger.error(f"Error starting streaming trace: {e}")

    def add_trace(
        self,
        trace_id: str,  # This is span_id/component_id
        trace_name: str,  # Component name
        trace_type: str,  # Component type
        inputs: dict[str, Any],
        metadata: dict[str, Any] | None = None,
        vertex: Any = None,  # Langflow Vertex object
    ) -> None:
        """Start a component span and send span_start event.

        Args:
            trace_id: Component/span ID
            trace_name: Component name
            trace_type: Component type
            inputs: Input data
            metadata: Optional metadata
            vertex: Optional Langflow Vertex object
        """
        if not self._trace_context:
            return

        try:
            span_start_time = time.time()
            safe_inputs = safe_serialize(inputs) if inputs else {}
            safe_metadata = safe_serialize(metadata) if metadata else {}

            # Infer component type
            component_type = infer_component_type(trace_name)

            # Store active span
            span_info = {
                "span_id": trace_id,
                "component_name": trace_name,
                "trace_type": trace_type,
                "component_type": component_type,
                "start_time": span_start_time,
                "inputs": safe_inputs,
                "metadata": safe_metadata,
            }
            self._trace_context.add_span(trace_id, span_info)

            # Start OTEL child span if enabled
            if self._otel_available and self._otel_manager:
                try:
                    otel_span = self._otel_manager.start_span(
                        f"component:{trace_name}",
                        tags=["component", component_type],
                        span_id=trace_id,
                        component_name=trace_name,
                        component_type=component_type,
                        trace_type=trace_type,
                    )
                    self._otel_spans[trace_id] = otel_span
                    logger.debug(f"Started OTEL span: {trace_id}")
                except Exception as e:
                    logger.warning(f"Failed to start OTEL span {trace_id}: {e}")

            # Send Kafka span_start event
            if self._ready and self._kafka_producer:
                success = self._kafka_producer.send_span_start(
                    trace_id=self._trace_context.trace_id,
                    span_id=trace_id,
                    component_name=trace_name,
                    component_type=component_type,
                    input_data=safe_inputs,
                    metadata=safe_metadata,
                )
                if success:
                    logger.debug(f"Started span: {trace_id} ({trace_name})")
                else:
                    logger.warning(f"Failed to send span_start for {trace_id}")

        except Exception as e:
            logger.error(f"Error starting span {trace_id}: {e}")

    def end_trace(
        self,
        trace_id: str,  # span_id
        trace_name: str,
        outputs: dict[str, Any] | None = None,
        error: Exception | None = None,
        logs: Sequence[Any] = (),
    ) -> None:
        """End a component span and send span_end event.

        Args:
            trace_id: Component/span ID
            trace_name: Component name
            outputs: Output data
            error: Optional exception
            logs: Optional logs
        """
        if not self._trace_context:
            return

        try:
            span_end_time = time.time()
            safe_outputs = safe_serialize(outputs) if outputs else {}

            # Get span info and mark as completed
            span_info = self._trace_context.complete_span(trace_id)

            if not span_info:
                logger.warning(f"Trying to end unknown span: {trace_id}")
                return

            # Calculate duration
            duration_ms = (span_end_time - span_info["start_time"]) * 1000

            # Extract token usage and calculate cost if this is an LLM span
            input_tokens = None
            output_tokens = None
            cost = None
            model_name = None
            provider = None

            if safe_outputs:
                # Try to extract token usage from outputs using Strategy pattern
                usage = self._token_extractor.extract(safe_outputs)
                if usage:
                    input_tokens = usage.get("input_tokens")
                    output_tokens = usage.get("output_tokens")
                    model_name = usage.get("model")

                    if model_name:
                        model_name = clean_model_name(model_name)
                        provider = guess_provider_from_model(model_name)

                        # Calculate cost using genai-prices
                        if input_tokens is not None and output_tokens is not None:
                            cost_result = calculate_cost(
                                provider=provider,
                                model=model_name,
                                input_tokens=input_tokens,
                                output_tokens=output_tokens,
                            )
                            cost = cost_result.total_cost

                            # Update trace totals
                            self._trace_context.add_token_usage(
                                input_tokens, output_tokens, cost or 0.0
                            )

            # Build metadata
            enhanced_metadata = {
                "component_name": trace_name,
                "status": "error" if error else "success",
                "component_type": infer_component_type(trace_name, model_name),
            }
            if model_name:
                enhanced_metadata["model"] = model_name
            if provider:
                enhanced_metadata["provider"] = provider
            if input_tokens is not None:
                enhanced_metadata["input_tokens"] = input_tokens
            if output_tokens is not None:
                enhanced_metadata["output_tokens"] = output_tokens
            if cost is not None:
                enhanced_metadata["cost"] = cost

            # End OTEL span if enabled
            if trace_id in self._otel_spans and self._otel_manager:
                try:
                    otel_span = self._otel_spans.pop(trace_id)
                    # Add attributes to span before closing
                    self._otel_manager.set_span_attribute(
                        otel_span, "duration_ms", duration_ms
                    )
                    if model_name:
                        self._otel_manager.set_span_attribute(
                            otel_span, "model", model_name
                        )
                    if provider:
                        self._otel_manager.set_span_attribute(
                            otel_span, "provider", provider
                        )
                    if input_tokens is not None:
                        self._otel_manager.set_span_attribute(
                            otel_span, "input_tokens", input_tokens
                        )
                    if output_tokens is not None:
                        self._otel_manager.set_span_attribute(
                            otel_span, "output_tokens", output_tokens
                        )
                    if cost is not None:
                        self._otel_manager.set_span_attribute(otel_span, "cost", cost)
                    if error:
                        self._otel_manager.set_span_attribute(
                            otel_span, "error", str(error)
                        )
                    # End span with error if present
                    self._otel_manager.end_span(otel_span, error=error)
                    logger.debug(f"Ended OTEL span: {trace_id}")
                except Exception as e:
                    logger.warning(f"Failed to end OTEL span {trace_id}: {e}")

            # Send Kafka span_end event
            if self._ready and self._kafka_producer:
                success = self._kafka_producer.send_span_end(
                    trace_id=self._trace_context.trace_id,
                    span_id=trace_id,
                    duration_ms=duration_ms,
                    component_name=trace_name,
                    output_data=safe_outputs,
                    error=str(error) if error else None,
                    metadata=enhanced_metadata,
                )
                if success:
                    logger.debug(
                        f"Ended span: {trace_id} (duration: {duration_ms:.2f}ms)"
                    )
                else:
                    logger.warning(f"Failed to send span_end for {trace_id}")

        except Exception as e:
            logger.error(f"Error ending span {trace_id}: {e}")

    def end(
        self,
        inputs: dict[str, Any],
        outputs: dict[str, Any],
        error: Exception | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """End the entire trace and send trace_end event.

        Args:
            inputs: All inputs to the flow
            outputs: All outputs from the flow
            error: Optional exception
            metadata: Optional metadata
        """
        if not self._trace_context:
            return

        try:
            trace_end_time = time.time()
            duration_ms = (trace_end_time - self._trace_context.start_time) * 1000

            # Build trace metadata
            trace_metadata = {
                "flow_id": self._trace_context.flow_id,
                "flow_name": self._trace_context.trace_name,
                "total_spans": self._trace_context.get_span_count(),
                "status": "error" if error else "success",
                "project_name": self._trace_context.project_name,
                # Token/cost totals
                "total_input_tokens": self._trace_context.total_input_tokens,
                "total_output_tokens": self._trace_context.total_output_tokens,
                "total_cost": self._trace_context.total_cost,
                # Additional context
                **self._trace_context.tags,
                **self._trace_context.params,
                **self._trace_context.metrics,
                **(metadata or {}),
            }

            # End OTEL parent span if enabled
            if self._otel_trace_span and self._otel_manager:
                try:
                    # Add final attributes
                    self._otel_manager.set_span_attribute(
                        self._otel_trace_span, "duration_ms", duration_ms
                    )
                    self._otel_manager.set_span_attribute(
                        self._otel_trace_span,
                        "total_spans",
                        self._trace_context.get_span_count(),
                    )
                    self._otel_manager.set_span_attribute(
                        self._otel_trace_span,
                        "total_input_tokens",
                        self._trace_context.total_input_tokens,
                    )
                    self._otel_manager.set_span_attribute(
                        self._otel_trace_span,
                        "total_output_tokens",
                        self._trace_context.total_output_tokens,
                    )
                    self._otel_manager.set_span_attribute(
                        self._otel_trace_span,
                        "total_cost",
                        self._trace_context.total_cost,
                    )
                    if error:
                        self._otel_manager.set_span_attribute(
                            self._otel_trace_span, "error", str(error)
                        )
                    # End the trace span
                    self._otel_manager.end_span(self._otel_trace_span, error=error)
                    self._otel_trace_span = None
                    logger.debug("Ended OTEL trace span")
                except Exception as e:
                    logger.warning(f"Failed to end OTEL trace span: {e}")

            # Send Kafka trace_end event
            if self._ready and self._kafka_producer:
                success = self._kafka_producer.send_trace_end(
                    trace_id=self._trace_context.trace_id,
                    duration_ms=duration_ms,
                    metadata=trace_metadata,
                    error=str(error) if error else None,
                )
                if success:
                    logger.info(
                        f"Completed streaming trace: {self._trace_context.trace_id} "
                        f"(duration: {duration_ms:.2f}ms, "
                        f"spans: {self._trace_context.get_span_count()}, "
                        f"cost: ${self._trace_context.total_cost:.4f})"
                    )
                else:
                    logger.warning("Failed to send trace_end event")

                # Flush pending messages
                self._flush_producer()

        except Exception as e:
            logger.error(f"Error ending streaming trace: {e}")

    def add_tags(self, tags: dict[str, str]) -> None:
        """Add tags to trace context."""
        if self._trace_context:
            self._trace_context.update_tags(tags)

    def log_param(self, key: str, value: Any) -> None:
        """Log parameter to trace context."""
        if self._trace_context:
            self._trace_context.set_param(key, value)

    def log_metric(self, key: str, value: float) -> None:
        """Log metric to trace context."""
        if self._trace_context:
            self._trace_context.set_metric(key, value)

    def get_langchain_callback(self) -> Any:
        """Get LangChain callback handler if needed.

        Returns:
            LangChain callback handler or None
        """
        # TODO: Implement LangChain callback if needed
        return None

    def _flush_producer(self) -> None:
        """Flush Kafka producer."""
        try:
            if self._kafka_producer:
                pending = self._kafka_producer.flush(timeout=5.0)
                if pending > 0:
                    logger.warning(f"{pending} messages still pending after flush")
        except Exception as e:
            logger.error(f"Error flushing producer: {e}")

    def close(self) -> None:
        """Close the tracer."""
        try:
            # Close any remaining OTEL spans using OTELManager
            if self._otel_manager:
                for span_id, span in list(self._otel_spans.items()):
                    try:
                        self._otel_manager.end_span(span)
                    except Exception:
                        pass
                self._otel_spans.clear()

                # Close OTEL trace span if still open
                if self._otel_trace_span:
                    try:
                        self._otel_manager.end_span(self._otel_trace_span)
                    except Exception:
                        pass
                    self._otel_trace_span = None
            else:
                self._otel_spans.clear()
                self._otel_trace_span = None

            # Flush and close Kafka producer
            self._flush_producer()
            if self._kafka_producer:
                self._kafka_producer.close()
                self._kafka_producer = None
            self._ready = False
            logger.debug("AgentTracer closed")
        except Exception as e:
            logger.error(f"Error closing tracer: {e}")

    def __enter__(self) -> AgentTracer:
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: type | None,
        exc_val: Exception | None,
        exc_tb: Any,
    ) -> bool:
        """Context manager exit."""
        self.close()
        return False

    def __del__(self) -> None:
        """Destructor to ensure cleanup."""
        try:
            self.close()
        except Exception:
            pass
