"""WorkflowTracer for general step-based tracing.

A simple, modern tracer for any workflow - not just LLM operations.
Supports dual export: OTEL via Logfire and direct Kafka streaming.

Example:
    ```python
    from autonomize_observer.tracing import WorkflowTracer

    with WorkflowTracer("process-order", order_id="123") as tracer:
        with tracer.step("validate") as step:
            validate_order()
            step.set("items_count", 5)

        with tracer.step("payment") as step:
            result = process_payment()
            step.set("amount", result.amount)
            step.set("provider", "stripe")

        with tracer.step("fulfillment"):
            send_to_warehouse()

        tracer.set("status", "completed")
    ```

With Kafka export:
    ```python
    with WorkflowTracer(
        "process-order",
        kafka_bootstrap_servers="kafka:9092",
        kafka_topic="workflow-traces",
        order_id="123",
    ) as tracer:
        with tracer.step("validate"):
            validate_order()
    ```
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Generator

from autonomize_observer.core.imports import (
    CONFLUENT_KAFKA_AVAILABLE,
    LOGFIRE_AVAILABLE,
    ConfluentProducer,
    logfire,
)
from autonomize_observer.core.kafka_utils import build_producer_config

logger = logging.getLogger(__name__)


@dataclass
class StepMetrics:
    """Metrics for a single step."""

    name: str
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    duration_ms: float | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def complete(self, error: str | None = None) -> None:
        """Mark step as complete."""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.error = error


class Step:
    """Context for a single step within a workflow."""

    def __init__(
        self,
        name: str,
        tracer: WorkflowTracer,
        otel_span: Any = None,
    ) -> None:
        self.name = name
        self._tracer = tracer
        self._otel_span = otel_span
        self._metrics = StepMetrics(name=name)
        self._attributes: dict[str, Any] = {}

    def set(self, key: str, value: Any) -> Step:
        """Set an attribute on this step.

        Args:
            key: Attribute name
            value: Attribute value

        Returns:
            Self for chaining
        """
        self._attributes[key] = value
        self._metrics.attributes[key] = value

        # Set on OTEL span if available
        if self._otel_span and hasattr(self._otel_span, "set_attribute"):
            try:
                self._otel_span.set_attribute(key, value)
            except Exception:
                pass

        return self

    def log(self, message: str, **kwargs: Any) -> Step:
        """Log a message within this step.

        Args:
            message: Log message
            **kwargs: Additional attributes

        Returns:
            Self for chaining
        """
        if LOGFIRE_AVAILABLE and logfire:
            try:
                logfire.info(message, step=self.name, **kwargs)
            except Exception:
                pass
        return self

    @property
    def duration_ms(self) -> float | None:
        """Get duration in milliseconds (available after step completes)."""
        return self._metrics.duration_ms


class WorkflowTracer:
    """Simple tracer for step-based workflows.

    Provides dual export: OTEL-based tracing and direct Kafka streaming.
    Works with or without LLM operations.

    Example:
        ```python
        with WorkflowTracer("data-pipeline", pipeline_id="p-123") as tracer:
            with tracer.step("extract") as step:
                data = extract_data()
                step.set("rows", len(data))

            with tracer.step("transform") as step:
                result = transform_data(data)
                step.set("transformed_rows", len(result))

            with tracer.step("load"):
                load_to_db(result)
        ```

    With Kafka:
        ```python
        with WorkflowTracer(
            "data-pipeline",
            kafka_bootstrap_servers="kafka:9092",
            kafka_topic="workflow-traces",
        ) as tracer:
            ...
        ```
    """

    def __init__(
        self,
        name: str,
        service_name: str | None = None,
        send_to_logfire: bool = False,
        # Kafka configuration
        kafka_bootstrap_servers: str | None = None,
        kafka_topic: str = "workflow-traces",
        kafka_username: str | None = None,
        kafka_password: str | None = None,
        kafka_security_protocol: str = "PLAINTEXT",
        **attributes: Any,
    ) -> None:
        """Initialize workflow tracer.

        Args:
            name: Workflow name (e.g., "process-order", "data-pipeline")
            service_name: Service name for OTEL (defaults to workflow name)
            send_to_logfire: Send traces to Logfire cloud
            kafka_bootstrap_servers: Kafka bootstrap servers (enables Kafka export)
            kafka_topic: Kafka topic for workflow traces
            kafka_username: Kafka SASL username
            kafka_password: Kafka SASL password
            kafka_security_protocol: Kafka security protocol
            **attributes: Initial attributes for the workflow
        """
        self.name = name
        self._workflow_id = str(uuid.uuid4())
        self._service_name = service_name or name
        self._send_to_logfire = send_to_logfire
        self._attributes = dict(attributes)

        self._start_time: float | None = None
        self._end_time: float | None = None
        self._steps: list[StepMetrics] = []
        self._otel_span: Any = None
        self._configured = False

        # Kafka configuration
        self._kafka_bootstrap_servers = kafka_bootstrap_servers
        self._kafka_topic = kafka_topic
        self._kafka_username = kafka_username
        self._kafka_password = kafka_password
        self._kafka_security_protocol = kafka_security_protocol
        self._kafka_producer: Any = None
        self._kafka_enabled = False

        # Configure OTEL if available
        self._setup_otel()

        # Configure Kafka if servers provided
        if kafka_bootstrap_servers:
            self._setup_kafka()

    def _setup_otel(self) -> None:
        """Setup OTEL tracing."""
        if not LOGFIRE_AVAILABLE or not logfire:
            logger.debug("Logfire not available - tracing will be local only")
            return

        try:
            logfire.configure(
                service_name=self._service_name,
                send_to_logfire=self._send_to_logfire,
            )
            self._configured = True
        except Exception as e:
            logger.warning(f"Failed to configure Logfire: {e}")

    def _setup_kafka(self) -> None:
        """Setup Kafka producer using confluent-kafka."""
        if not CONFLUENT_KAFKA_AVAILABLE or not ConfluentProducer:
            logger.warning("confluent-kafka not installed - Kafka export disabled")
            return

        if not self._kafka_bootstrap_servers:
            return

        try:
            # Use shared config builder
            config = build_producer_config(
                bootstrap_servers=self._kafka_bootstrap_servers,
                client_id="workflow-tracer",
                username=self._kafka_username,
                password=self._kafka_password,
                security_protocol=self._kafka_security_protocol,
                sasl_mechanism="PLAIN",
                # Batch mode for workflow events
                low_latency=False,
            )

            self._kafka_producer = ConfluentProducer(config)
            self._kafka_enabled = True
            logger.debug(f"Kafka producer configured for topic {self._kafka_topic}")
        except Exception as e:
            logger.warning(f"Failed to configure Kafka producer: {e}")
            self._kafka_enabled = False

    def _send_to_kafka(self, event_type: str, data: dict[str, Any]) -> None:
        """Send event to Kafka using confluent-kafka."""
        if not self._kafka_enabled or not self._kafka_producer:
            return

        try:
            event = {
                "event_type": event_type,
                "workflow_id": self._workflow_id,
                "workflow_name": self.name,
                "service_name": self._service_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **data,
            }
            # Serialize and send using confluent-kafka API
            self._kafka_producer.produce(
                topic=self._kafka_topic,
                key=self._workflow_id.encode("utf-8"),
                value=json.dumps(event, default=str).encode("utf-8"),
            )
            # Trigger delivery callbacks (non-blocking)
            self._kafka_producer.poll(0)
        except Exception as e:
            logger.warning(f"Failed to send event to Kafka: {e}")

    def set(self, key: str, value: Any) -> WorkflowTracer:
        """Set an attribute on the workflow.

        Args:
            key: Attribute name
            value: Attribute value

        Returns:
            Self for chaining
        """
        self._attributes[key] = value

        # Set on OTEL span if available
        if self._otel_span and hasattr(self._otel_span, "set_attribute"):
            try:
                self._otel_span.set_attribute(key, value)
            except Exception:
                pass

        return self

    def log(self, message: str, **kwargs: Any) -> WorkflowTracer:
        """Log a message within this workflow.

        Args:
            message: Log message
            **kwargs: Additional attributes

        Returns:
            Self for chaining
        """
        if LOGFIRE_AVAILABLE and logfire:
            try:
                logfire.info(message, workflow=self.name, **kwargs)
            except Exception:
                pass
        return self

    @contextmanager
    def step(
        self,
        name: str,
        **attributes: Any,
    ) -> Generator[Step, None, None]:
        """Create a step within the workflow.

        Args:
            name: Step name
            **attributes: Initial attributes for the step

        Yields:
            Step context for setting attributes
        """
        step_obj: Step
        otel_span = None

        # Create OTEL span if available
        if self._configured and LOGFIRE_AVAILABLE and logfire:
            try:
                otel_span = logfire.span(
                    f"step:{name}",
                    _tags=["step"],
                    **attributes,
                ).__enter__()
            except Exception as e:
                logger.warning(f"Failed to create OTEL span for step {name}: {e}")

        step_obj = Step(name, self, otel_span)

        # Set initial attributes
        for key, value in attributes.items():
            step_obj.set(key, value)

        # Send step start event to Kafka
        self._send_to_kafka(
            "step_start",
            {
                "step_name": name,
                "step_index": len(self._steps),
                "attributes": dict(attributes),
            },
        )

        error: Exception | None = None
        try:
            yield step_obj
        except Exception as e:
            error = e
            step_obj._metrics.error = str(e)
            raise
        finally:
            # Complete the step
            step_obj._metrics.complete(str(error) if error else None)
            self._steps.append(step_obj._metrics)

            # Send step end event to Kafka
            self._send_to_kafka(
                "step_end",
                {
                    "step_name": name,
                    "step_index": len(self._steps) - 1,
                    "duration_ms": step_obj._metrics.duration_ms,
                    "error": str(error) if error else None,
                    "attributes": step_obj._attributes,
                },
            )

            # Close OTEL span
            if otel_span:
                try:
                    if hasattr(otel_span, "set_attribute"):
                        otel_span.set_attribute(
                            "duration_ms", step_obj._metrics.duration_ms
                        )
                        if error:
                            otel_span.set_attribute("error", str(error))
                    otel_span.__exit__(
                        type(error) if error else None,
                        error,
                        error.__traceback__ if error else None,
                    )
                except Exception:
                    pass

    def __enter__(self) -> WorkflowTracer:
        """Start the workflow."""
        self._start_time = time.time()

        # Create OTEL parent span
        if self._configured and LOGFIRE_AVAILABLE and logfire:
            try:
                self._otel_span = logfire.span(
                    f"workflow:{self.name}",
                    _tags=["workflow"],
                    **self._attributes,
                ).__enter__()
            except Exception as e:
                logger.warning(f"Failed to create OTEL workflow span: {e}")

        # Send workflow start event to Kafka
        self._send_to_kafka(
            "workflow_start",
            {
                "attributes": self._attributes,
            },
        )

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> bool:
        """Complete the workflow."""
        self._end_time = time.time()
        duration_ms = (self._end_time - (self._start_time or self._end_time)) * 1000

        # Log summary
        step_count = len(self._steps)
        total_step_time = sum(s.duration_ms or 0 for s in self._steps)
        failed_steps = [s for s in self._steps if s.error]

        logger.info(
            f"Workflow '{self.name}' completed in {duration_ms:.2f}ms "
            f"({step_count} steps, {len(failed_steps)} failed)"
        )

        # Close OTEL span
        if self._otel_span:
            try:
                if hasattr(self._otel_span, "set_attribute"):
                    self._otel_span.set_attribute("duration_ms", duration_ms)
                    self._otel_span.set_attribute("step_count", step_count)
                    self._otel_span.set_attribute("total_step_time_ms", total_step_time)
                    if exc_val:
                        self._otel_span.set_attribute("error", str(exc_val))
                self._otel_span.__exit__(exc_type, exc_val, exc_tb)
            except Exception:
                pass

        # Send workflow end event to Kafka
        self._send_to_kafka(
            "workflow_end",
            {
                "duration_ms": duration_ms,
                "step_count": step_count,
                "total_step_time_ms": total_step_time,
                "failed_step_count": len(failed_steps),
                "error": str(exc_val) if exc_val else None,
                "attributes": self._attributes,
                "steps": [
                    {
                        "name": s.name,
                        "duration_ms": s.duration_ms,
                        "error": s.error,
                        "attributes": s.attributes,
                    }
                    for s in self._steps
                ],
            },
        )

        # Flush and close Kafka producer
        self._close_kafka()

        return False  # Don't suppress exceptions

    def _close_kafka(self) -> None:
        """Close Kafka producer (confluent-kafka)."""
        if self._kafka_producer:
            try:
                # confluent-kafka flush takes timeout in seconds
                remaining = self._kafka_producer.flush(5.0)
                if remaining > 0:
                    logger.warning(f"Kafka flush: {remaining} messages pending")
            except Exception as e:
                logger.warning(f"Error closing Kafka producer: {e}")
            finally:
                self._kafka_producer = None
                self._kafka_enabled = False

    @property
    def duration_ms(self) -> float | None:
        """Get total duration in milliseconds."""
        if self._start_time and self._end_time:
            return (self._end_time - self._start_time) * 1000
        return None

    @property
    def steps(self) -> list[StepMetrics]:
        """Get all step metrics."""
        return self._steps.copy()

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of the workflow execution.

        Returns:
            Dictionary with workflow metrics
        """
        return {
            "name": self.name,
            "duration_ms": self.duration_ms,
            "step_count": len(self._steps),
            "steps": [
                {
                    "name": s.name,
                    "duration_ms": s.duration_ms,
                    "error": s.error,
                    "attributes": s.attributes,
                }
                for s in self._steps
            ],
            "attributes": self._attributes,
        }


# Convenience function for quick tracing
@contextmanager
def trace_workflow(
    name: str,
    **attributes: Any,
) -> Generator[WorkflowTracer, None, None]:
    """Convenience function for tracing a workflow.

    Args:
        name: Workflow name
        **attributes: Initial attributes

    Yields:
        WorkflowTracer instance

    Example:
        ```python
        from autonomize_observer.tracing import trace_workflow

        with trace_workflow("my-task", task_id="123") as tracer:
            with tracer.step("step1"):
                do_step1()
            with tracer.step("step2"):
                do_step2()
        ```
    """
    with WorkflowTracer(name, **attributes) as tracer:
        yield tracer
