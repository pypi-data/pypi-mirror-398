"""Tracer factory for creating configured tracer instances.

This module provides a factory pattern for creating tracers,
centralizing configuration and ensuring consistent setup.

Usage:
    from autonomize_observer.tracing.factory import TracerFactory
    from autonomize_observer.core.config import ObserverConfig

    config = ObserverConfig.from_env()
    factory = TracerFactory(config)

    # Create tracers with consistent configuration
    with factory.create_workflow_tracer("my-workflow") as tracer:
        with tracer.step("step1"):
            do_work()
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from autonomize_observer.core.config import KafkaConfig, ObserverConfig
    from autonomize_observer.tracing.agent_tracer import AgentTracer
    from autonomize_observer.tracing.otel_utils import OTELManager
    from autonomize_observer.tracing.workflow_tracer import WorkflowTracer


class TracerFactory:
    """Factory for creating tracer instances.

    Provides a centralized way to create tracers with consistent
    configuration from ObserverConfig or KafkaConfig.

    Example:
        ```python
        config = ObserverConfig.from_env()
        factory = TracerFactory(config)

        # Create a workflow tracer
        with factory.create_workflow_tracer("process-order") as tracer:
            with tracer.step("validate"):
                validate()
            with tracer.step("process"):
                process()

        # Create an agent tracer (for AI Studio)
        agent = factory.create_agent_tracer(
            trace_id=uuid4(),
            flow_id="my-flow",
            trace_name="Customer Support Agent",
        )
        ```
    """

    def __init__(
        self,
        config: ObserverConfig | None = None,
        kafka_config: KafkaConfig | None = None,
        otel_manager: OTELManager | None = None,
    ) -> None:
        """Initialize factory with configuration.

        Args:
            config: Full ObserverConfig (preferred)
            kafka_config: Standalone Kafka config (alternative)
            otel_manager: Shared OTEL manager instance
        """
        self._config = config
        self._kafka_config = kafka_config or (config.kafka if config else None)
        self._otel_manager = otel_manager

        # Extract settings from config
        self._service_name = config.service_name if config else "autonomize-service"
        self._send_to_logfire = config.send_to_logfire if config else False
        self._kafka_enabled = (
            config.kafka_enabled if config else (kafka_config is not None)
        )

    @classmethod
    def from_config(cls, config: ObserverConfig) -> TracerFactory:
        """Create factory from ObserverConfig.

        Args:
            config: ObserverConfig instance

        Returns:
            Configured TracerFactory
        """
        return cls(config=config)

    @classmethod
    def from_kafka_config(cls, kafka_config: KafkaConfig) -> TracerFactory:
        """Create factory from KafkaConfig only.

        Args:
            kafka_config: KafkaConfig instance

        Returns:
            Configured TracerFactory
        """
        return cls(kafka_config=kafka_config)

    def create_workflow_tracer(
        self,
        name: str,
        service_name: str | None = None,
        send_to_logfire: bool | None = None,
        kafka_topic: str | None = None,
        **attributes: Any,
    ) -> WorkflowTracer:
        """Create a WorkflowTracer instance.

        Args:
            name: Workflow name
            service_name: Override service name
            send_to_logfire: Override Logfire setting
            kafka_topic: Override Kafka topic
            **attributes: Initial workflow attributes

        Returns:
            Configured WorkflowTracer
        """
        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        # Resolve settings
        resolved_service_name = service_name or self._service_name
        resolved_send_to_logfire = (
            send_to_logfire if send_to_logfire is not None else self._send_to_logfire
        )
        resolved_topic = (
            kafka_topic
            or (self._kafka_config.workflow_topic if self._kafka_config else None)
            or "workflow-traces"
        )

        # Build Kafka kwargs if enabled
        kafka_kwargs: dict[str, Any] = {}
        if self._kafka_enabled and self._kafka_config:
            kafka_kwargs = {
                "kafka_bootstrap_servers": self._kafka_config.bootstrap_servers,
                "kafka_topic": resolved_topic,
                "kafka_username": self._kafka_config.sasl_username,
                "kafka_password": self._kafka_config.sasl_password,
                "kafka_security_protocol": self._kafka_config.security_protocol
                or "PLAINTEXT",
            }

        return WorkflowTracer(
            name=name,
            service_name=resolved_service_name,
            send_to_logfire=resolved_send_to_logfire,
            **kafka_kwargs,
            **attributes,
        )

    def create_agent_tracer(
        self,
        trace_id: UUID | None = None,
        flow_id: str = "",
        trace_name: str = "",
        project_name: str = "GenesisStudio",
        user_id: str | None = None,
        session_id: str | None = None,
        kafka_topic: str | None = None,
        enable_otel: bool = False,
        **kwargs: Any,
    ) -> AgentTracer:
        """Create an AgentTracer instance.

        Args:
            trace_id: Trace UUID (generated if not provided)
            flow_id: Flow identifier
            trace_name: Trace/flow name
            project_name: Project name
            user_id: Optional user ID
            session_id: Optional session ID
            kafka_topic: Override Kafka topic
            enable_otel: Enable OTEL tracing
            **kwargs: Additional tracer arguments

        Returns:
            Configured AgentTracer
        """
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        # Generate trace_id if not provided
        resolved_trace_id = trace_id or uuid4()

        # Resolve topic
        resolved_topic = (
            kafka_topic
            or (self._kafka_config.trace_topic if self._kafka_config else None)
            or "genesis-traces-streaming"
        )

        # Build Kafka kwargs if enabled
        kafka_kwargs: dict[str, Any] = {}
        if self._kafka_enabled and self._kafka_config:
            kafka_kwargs = {
                "kafka_bootstrap_servers": self._kafka_config.bootstrap_servers,
                "kafka_topic": resolved_topic,
                "kafka_username": self._kafka_config.sasl_username,
                "kafka_password": self._kafka_config.sasl_password,
                "security_protocol": self._kafka_config.security_protocol or "SASL_SSL",
                "sasl_mechanism": self._kafka_config.sasl_mechanism or "PLAIN",
            }

        return AgentTracer(
            trace_name=trace_name,
            trace_id=resolved_trace_id,
            flow_id=flow_id,
            project_name=project_name,
            user_id=user_id,
            session_id=session_id,
            enable_otel=enable_otel,
            otel_service_name=self._service_name,
            send_to_logfire=self._send_to_logfire,
            **kafka_kwargs,
            **kwargs,
        )


__all__ = ["TracerFactory"]
