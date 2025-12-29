"""Tests for TracerFactory."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestTracerFactory:
    """Tests for TracerFactory."""

    def test_create_workflow_tracer_without_kafka(self) -> None:
        """Test creating WorkflowTracer without Kafka."""
        from autonomize_observer.tracing.factory import TracerFactory

        factory = TracerFactory()
        tracer = factory.create_workflow_tracer("test-workflow")

        assert tracer.name == "test-workflow"
        assert not tracer._kafka_enabled

    def test_create_workflow_tracer_with_kafka_config(self) -> None:
        """Test creating WorkflowTracer with KafkaConfig."""
        from autonomize_observer.core.config import KafkaConfig
        from autonomize_observer.tracing.factory import TracerFactory

        kafka_config = KafkaConfig(
            bootstrap_servers="kafka:9092",
            workflow_topic="my-workflow-topic",
            sasl_username="user",
            sasl_password="pass",
            security_protocol="SASL_SSL",
        )
        factory = TracerFactory(kafka_config=kafka_config)

        with patch(
            "autonomize_observer.tracing.workflow_tracer.CONFLUENT_KAFKA_AVAILABLE",
            True,
        ):
            with patch(
                "autonomize_observer.tracing.workflow_tracer.ConfluentProducer"
            ) as mock_producer:
                mock_producer.return_value = MagicMock()
                tracer = factory.create_workflow_tracer("test-workflow")

                assert tracer.name == "test-workflow"
                assert tracer._kafka_topic == "my-workflow-topic"

    def test_create_workflow_tracer_with_observer_config(self) -> None:
        """Test creating WorkflowTracer with ObserverConfig."""
        from autonomize_observer.core.config import KafkaConfig, ObserverConfig
        from autonomize_observer.tracing.factory import TracerFactory

        config = ObserverConfig(
            service_name="my-service",
            send_to_logfire=False,
            kafka=KafkaConfig(
                bootstrap_servers="kafka:9092",
                workflow_topic="test-workflows",
            ),
            kafka_enabled=True,
        )
        factory = TracerFactory.from_config(config)

        with patch(
            "autonomize_observer.tracing.workflow_tracer.CONFLUENT_KAFKA_AVAILABLE",
            True,
        ):
            with patch(
                "autonomize_observer.tracing.workflow_tracer.ConfluentProducer"
            ) as mock_producer:
                mock_producer.return_value = MagicMock()
                tracer = factory.create_workflow_tracer("my-workflow", order_id="123")

                assert tracer.name == "my-workflow"
                assert tracer._service_name == "my-service"

    def test_create_workflow_tracer_override_settings(self) -> None:
        """Test overriding settings when creating WorkflowTracer."""
        from autonomize_observer.tracing.factory import TracerFactory

        factory = TracerFactory()
        tracer = factory.create_workflow_tracer(
            name="test",
            service_name="custom-service",
            custom_attr="value",
        )

        assert tracer._service_name == "custom-service"
        assert tracer._attributes.get("custom_attr") == "value"

    def test_create_agent_tracer_without_kafka(self) -> None:
        """Test creating AgentTracer without Kafka."""
        from uuid import uuid4

        from autonomize_observer.tracing.factory import TracerFactory

        factory = TracerFactory()
        trace_id = uuid4()
        tracer = factory.create_agent_tracer(
            trace_id=trace_id,
            flow_id="flow-123",
            trace_name="Test Agent",
        )

        assert tracer.trace_id == trace_id
        assert tracer.flow_id == "flow-123"
        assert tracer.trace_name == "Test Agent"
        assert not tracer._ready  # No Kafka configured

    def test_create_agent_tracer_auto_generate_trace_id(self) -> None:
        """Test AgentTracer trace_id is auto-generated if not provided."""
        from autonomize_observer.tracing.factory import TracerFactory

        factory = TracerFactory()
        tracer = factory.create_agent_tracer(
            flow_id="flow-123",
            trace_name="Test Agent",
        )

        assert tracer.trace_id is not None

    def test_create_agent_tracer_with_kafka_config(self) -> None:
        """Test creating AgentTracer with KafkaConfig."""
        from uuid import uuid4

        from autonomize_observer.core.config import KafkaConfig
        from autonomize_observer.tracing.factory import TracerFactory

        kafka_config = KafkaConfig(
            bootstrap_servers="kafka:9092",
            trace_topic="my-traces",
            security_protocol="SASL_SSL",
            sasl_mechanism="PLAIN",
        )
        factory = TracerFactory(kafka_config=kafka_config)

        with patch(
            "autonomize_observer.tracing.kafka_trace_producer.KAFKA_AVAILABLE",
            True,
        ):
            with patch(
                "autonomize_observer.tracing.kafka_trace_producer.Producer"
            ) as mock_producer:
                mock_producer.return_value = MagicMock()
                tracer = factory.create_agent_tracer(
                    trace_id=uuid4(),
                    flow_id="flow-456",
                    trace_name="Kafka Agent",
                )

                assert tracer._kafka_topic == "my-traces"

    def test_from_kafka_config(self) -> None:
        """Test creating factory from KafkaConfig."""
        from autonomize_observer.core.config import KafkaConfig
        from autonomize_observer.tracing.factory import TracerFactory

        kafka_config = KafkaConfig(bootstrap_servers="kafka:9092")
        factory = TracerFactory.from_kafka_config(kafka_config)

        assert factory._kafka_config is kafka_config
        assert factory._kafka_enabled is True


class TestTracerFactoryIntegration:
    """Integration tests for TracerFactory."""

    def test_workflow_tracer_with_steps(self) -> None:
        """Test WorkflowTracer created by factory works correctly."""
        from autonomize_observer.tracing.factory import TracerFactory

        factory = TracerFactory()

        with factory.create_workflow_tracer("integration-test") as tracer:
            with tracer.step("step1") as step:
                step.set("value", 1)
            with tracer.step("step2") as step:
                step.set("value", 2)

        assert len(tracer.steps) == 2
        assert tracer.steps[0].name == "step1"
        assert tracer.steps[1].name == "step2"
