"""Tests for WorkflowTracer."""

import time
from unittest.mock import MagicMock, patch

import pytest


class TestStepMetrics:
    """Tests for StepMetrics dataclass."""

    def test_init(self) -> None:
        """Test StepMetrics initialization."""
        from autonomize_observer.tracing.workflow_tracer import StepMetrics

        metrics = StepMetrics(name="test-step")

        assert metrics.name == "test-step"
        assert metrics.start_time > 0
        assert metrics.end_time is None
        assert metrics.duration_ms is None
        assert metrics.attributes == {}
        assert metrics.error is None

    def test_complete(self) -> None:
        """Test completing a step."""
        from autonomize_observer.tracing.workflow_tracer import StepMetrics

        metrics = StepMetrics(name="test-step")
        time.sleep(0.01)  # Small delay
        metrics.complete()

        assert metrics.end_time is not None
        assert metrics.duration_ms is not None
        assert metrics.duration_ms >= 10  # At least 10ms
        assert metrics.error is None

    def test_complete_with_error(self) -> None:
        """Test completing a step with error."""
        from autonomize_observer.tracing.workflow_tracer import StepMetrics

        metrics = StepMetrics(name="test-step")
        metrics.complete(error="Something failed")

        assert metrics.error == "Something failed"


class TestStep:
    """Tests for Step context."""

    def test_set_attribute(self) -> None:
        """Test setting attributes."""
        from autonomize_observer.tracing.workflow_tracer import Step, WorkflowTracer

        tracer = WorkflowTracer("test")
        step = Step("test-step", tracer)

        result = step.set("key", "value")

        assert result is step  # Returns self for chaining
        assert step._attributes["key"] == "value"
        assert step._metrics.attributes["key"] == "value"

    def test_set_multiple_attributes(self) -> None:
        """Test chaining attribute setting."""
        from autonomize_observer.tracing.workflow_tracer import Step, WorkflowTracer

        tracer = WorkflowTracer("test")
        step = Step("test-step", tracer)

        step.set("a", 1).set("b", 2).set("c", 3)

        assert step._attributes == {"a": 1, "b": 2, "c": 3}

    @patch("autonomize_observer.tracing.workflow_tracer.LOGFIRE_AVAILABLE", True)
    @patch("autonomize_observer.tracing.workflow_tracer.logfire")
    def test_log(self, mock_logfire: MagicMock) -> None:
        """Test logging within step."""
        from autonomize_observer.tracing.workflow_tracer import Step, WorkflowTracer

        tracer = WorkflowTracer("test")
        step = Step("test-step", tracer)

        result = step.log("Test message", extra="data")

        assert result is step
        mock_logfire.info.assert_called_once()

    @patch("autonomize_observer.tracing.workflow_tracer.LOGFIRE_AVAILABLE", True)
    @patch("autonomize_observer.tracing.workflow_tracer.logfire")
    def test_log_exception(self, mock_logfire: MagicMock) -> None:
        """Test logging handles exceptions gracefully."""
        from autonomize_observer.tracing.workflow_tracer import Step, WorkflowTracer

        mock_logfire.info.side_effect = Exception("Log failed")

        tracer = WorkflowTracer("test")
        step = Step("test-step", tracer)

        # Should not raise
        result = step.log("Test message")

        assert result is step

    def test_set_with_otel_span_exception(self) -> None:
        """Test set handles OTEL span exceptions gracefully."""
        from autonomize_observer.tracing.workflow_tracer import Step, WorkflowTracer

        tracer = WorkflowTracer("test")
        mock_span = MagicMock()
        mock_span.set_attribute.side_effect = Exception("Span failed")
        step = Step("test-step", tracer, otel_span=mock_span)

        # Should not raise
        result = step.set("key", "value")

        assert result is step
        assert step._attributes["key"] == "value"

    def test_duration_ms_property(self) -> None:
        """Test step duration_ms property."""
        from autonomize_observer.tracing.workflow_tracer import Step, WorkflowTracer

        tracer = WorkflowTracer("test")
        step = Step("test-step", tracer)

        # Before completion
        assert step.duration_ms is None

        # After completion
        step._metrics.complete()
        assert step.duration_ms is not None
        assert step.duration_ms >= 0


class TestWorkflowTracer:
    """Tests for WorkflowTracer."""

    def test_basic_workflow(self) -> None:
        """Test basic workflow tracing."""
        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        with WorkflowTracer("test-workflow", task_id="123") as tracer:
            with tracer.step("step1") as step:
                step.set("result", "ok")
                time.sleep(0.01)

            with tracer.step("step2"):
                time.sleep(0.01)

        assert tracer.duration_ms is not None
        assert tracer.duration_ms >= 20
        assert len(tracer.steps) == 2
        assert tracer.steps[0].name == "step1"
        assert tracer.steps[1].name == "step2"

    def test_step_attributes(self) -> None:
        """Test step attributes."""
        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        with WorkflowTracer("test") as tracer:
            with tracer.step("step1", initial="value") as step:
                step.set("added", "later")

        assert tracer.steps[0].attributes["initial"] == "value"
        assert tracer.steps[0].attributes["added"] == "later"

    def test_workflow_attributes(self) -> None:
        """Test workflow-level attributes."""
        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        with WorkflowTracer("test", initial="attr") as tracer:
            tracer.set("added", "later")

        assert tracer._attributes["initial"] == "attr"
        assert tracer._attributes["added"] == "later"

    def test_step_exception(self) -> None:
        """Test step with exception."""
        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        with pytest.raises(ValueError):
            with WorkflowTracer("test") as tracer:
                with tracer.step("failing-step"):
                    raise ValueError("Test error")

        assert len(tracer.steps) == 1
        assert tracer.steps[0].error == "Test error"

    def test_workflow_exception(self) -> None:
        """Test workflow with exception."""
        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        with pytest.raises(ValueError):
            with WorkflowTracer("test") as tracer:
                with tracer.step("step1"):
                    pass
                raise ValueError("Workflow error")

        assert len(tracer.steps) == 1
        assert tracer.steps[0].error is None  # Step succeeded

    def test_get_summary(self) -> None:
        """Test getting workflow summary."""
        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        with WorkflowTracer("test-workflow", order_id="123") as tracer:
            with tracer.step("validate") as step:
                step.set("valid", True)
            with tracer.step("process") as step:
                step.set("items", 5)

        summary = tracer.get_summary()

        assert summary["name"] == "test-workflow"
        assert summary["duration_ms"] is not None
        assert summary["step_count"] == 2
        assert len(summary["steps"]) == 2
        assert summary["steps"][0]["name"] == "validate"
        assert summary["steps"][0]["attributes"]["valid"] is True
        assert summary["steps"][1]["name"] == "process"
        assert summary["steps"][1]["attributes"]["items"] == 5
        assert summary["attributes"]["order_id"] == "123"

    def test_steps_property_returns_copy(self) -> None:
        """Test that steps property returns a copy."""
        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        with WorkflowTracer("test") as tracer:
            with tracer.step("step1"):
                pass

        steps = tracer.steps
        steps.clear()

        assert len(tracer.steps) == 1  # Original not modified

    @patch("autonomize_observer.tracing.workflow_tracer.LOGFIRE_AVAILABLE", True)
    @patch("autonomize_observer.tracing.workflow_tracer.logfire")
    def test_log(self, mock_logfire: MagicMock) -> None:
        """Test logging within workflow."""
        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        with WorkflowTracer("test") as tracer:
            result = tracer.log("Test message", extra="data")
            assert result is tracer

        mock_logfire.info.assert_called()

    @patch("autonomize_observer.tracing.workflow_tracer.LOGFIRE_AVAILABLE", True)
    @patch("autonomize_observer.tracing.workflow_tracer.logfire")
    def test_log_exception(self, mock_logfire: MagicMock) -> None:
        """Test logging handles exceptions gracefully."""
        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        mock_logfire.info.side_effect = Exception("Log failed")

        with WorkflowTracer("test") as tracer:
            # Should not raise
            result = tracer.log("Test message")
            assert result is tracer

    @patch("autonomize_observer.tracing.workflow_tracer.LOGFIRE_AVAILABLE", True)
    @patch("autonomize_observer.tracing.workflow_tracer.logfire")
    def test_set_with_otel_span_exception(self, mock_logfire: MagicMock) -> None:
        """Test set handles OTEL span exceptions gracefully."""
        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=False)
        mock_span.set_attribute.side_effect = Exception("Span failed")
        mock_logfire.span.return_value = mock_span

        with WorkflowTracer("test") as tracer:
            # Should not raise
            result = tracer.set("key", "value")
            assert result is tracer
            assert tracer._attributes["key"] == "value"


class TestWorkflowTracerOTEL:
    """Tests for WorkflowTracer OTEL integration."""

    @patch("autonomize_observer.tracing.workflow_tracer.LOGFIRE_AVAILABLE", False)
    def test_works_without_logfire(self) -> None:
        """Test workflow works when logfire not installed."""
        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        with WorkflowTracer("test") as tracer:
            with tracer.step("step1") as step:
                step.set("key", "value")

        assert len(tracer.steps) == 1

    @patch("autonomize_observer.tracing.workflow_tracer.LOGFIRE_AVAILABLE", True)
    @patch("autonomize_observer.tracing.workflow_tracer.logfire")
    def test_otel_workflow_span(self, mock_logfire: MagicMock) -> None:
        """Test OTEL workflow span creation."""
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=False)
        mock_span.set_attribute = MagicMock()
        mock_logfire.span.return_value = mock_span

        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        with WorkflowTracer("test-workflow", task_id="123") as tracer:
            tracer.set("status", "ok")

        # Workflow span should be created
        mock_logfire.span.assert_called()
        mock_span.set_attribute.assert_called()

    @patch("autonomize_observer.tracing.workflow_tracer.LOGFIRE_AVAILABLE", True)
    @patch("autonomize_observer.tracing.workflow_tracer.logfire")
    def test_otel_step_span(self, mock_logfire: MagicMock) -> None:
        """Test OTEL step span creation."""
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=False)
        mock_span.set_attribute = MagicMock()
        mock_logfire.span.return_value = mock_span

        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        with WorkflowTracer("test") as tracer:
            with tracer.step("step1") as step:
                step.set("key", "value")

        # Should have created spans for workflow and step
        assert mock_logfire.span.call_count >= 2

    @patch("autonomize_observer.tracing.workflow_tracer.LOGFIRE_AVAILABLE", True)
    @patch("autonomize_observer.tracing.workflow_tracer.logfire")
    def test_otel_span_exception(self, mock_logfire: MagicMock) -> None:
        """Test OTEL span with exception."""
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=False)
        mock_span.set_attribute = MagicMock()
        mock_logfire.span.return_value = mock_span

        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        with pytest.raises(ValueError):
            with WorkflowTracer("test") as tracer:
                with tracer.step("failing") as step:
                    raise ValueError("Test error")

        # Should have set error attribute
        mock_span.set_attribute.assert_any_call("error", "Test error")

    @patch("autonomize_observer.tracing.workflow_tracer.LOGFIRE_AVAILABLE", True)
    @patch("autonomize_observer.tracing.workflow_tracer.logfire")
    def test_otel_configure_exception(self, mock_logfire: MagicMock) -> None:
        """Test handling of configure exception."""
        mock_logfire.configure.side_effect = Exception("Config failed")

        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        # Should not raise
        with WorkflowTracer("test") as tracer:
            with tracer.step("step1"):
                pass

        assert len(tracer.steps) == 1

    @patch("autonomize_observer.tracing.workflow_tracer.LOGFIRE_AVAILABLE", True)
    @patch("autonomize_observer.tracing.workflow_tracer.logfire")
    def test_otel_span_creation_exception(self, mock_logfire: MagicMock) -> None:
        """Test handling of span creation exception."""
        mock_logfire.span.side_effect = Exception("Span failed")

        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        # Should not raise
        with WorkflowTracer("test") as tracer:
            with tracer.step("step1"):
                pass

        assert len(tracer.steps) == 1

    @patch("autonomize_observer.tracing.workflow_tracer.LOGFIRE_AVAILABLE", True)
    @patch("autonomize_observer.tracing.workflow_tracer.logfire")
    def test_otel_step_span_exit_exception(self, mock_logfire: MagicMock) -> None:
        """Test handling of step span __exit__ exception."""
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(side_effect=Exception("Exit failed"))
        mock_span.set_attribute = MagicMock()
        mock_logfire.span.return_value = mock_span

        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        # Should not raise
        with WorkflowTracer("test") as tracer:
            with tracer.step("step1"):
                pass

        assert len(tracer.steps) == 1

    @patch("autonomize_observer.tracing.workflow_tracer.LOGFIRE_AVAILABLE", True)
    @patch("autonomize_observer.tracing.workflow_tracer.logfire")
    def test_otel_workflow_span_exit_exception(self, mock_logfire: MagicMock) -> None:
        """Test handling of workflow span __exit__ exception."""
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(side_effect=Exception("Exit failed"))
        mock_span.set_attribute = MagicMock()
        mock_logfire.span.return_value = mock_span

        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        # Should not raise
        with WorkflowTracer("test") as tracer:
            pass

        assert tracer.duration_ms is not None


class TestTraceWorkflow:
    """Tests for trace_workflow convenience function."""

    def test_trace_workflow(self) -> None:
        """Test trace_workflow function."""
        from autonomize_observer.tracing.workflow_tracer import trace_workflow

        with trace_workflow("test-task", task_id="123") as tracer:
            with tracer.step("step1"):
                pass
            with tracer.step("step2"):
                pass

        assert len(tracer.steps) == 2
        assert tracer._attributes["task_id"] == "123"

    def test_trace_workflow_exception(self) -> None:
        """Test trace_workflow with exception."""
        from autonomize_observer.tracing.workflow_tracer import trace_workflow

        with pytest.raises(RuntimeError):
            with trace_workflow("failing") as tracer:
                with tracer.step("step1"):
                    pass
                raise RuntimeError("Failed")


class TestWorkflowTracerKafka:
    """Tests for WorkflowTracer Kafka integration (confluent-kafka)."""

    @patch(
        "autonomize_observer.tracing.workflow_tracer.CONFLUENT_KAFKA_AVAILABLE", False
    )
    def test_kafka_not_available(self) -> None:
        """Test graceful handling when confluent-kafka not installed."""
        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        with WorkflowTracer(
            "test",
            kafka_bootstrap_servers="localhost:9092",
        ) as tracer:
            with tracer.step("step1"):
                pass

        assert not tracer._kafka_enabled

    @patch(
        "autonomize_observer.tracing.workflow_tracer.CONFLUENT_KAFKA_AVAILABLE", True
    )
    @patch("autonomize_observer.tracing.workflow_tracer.ConfluentProducer")
    def test_kafka_setup(self, mock_producer_class: MagicMock) -> None:
        """Test Kafka producer setup."""
        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        mock_producer = MagicMock()
        mock_producer_class.return_value = mock_producer

        tracer = WorkflowTracer(
            "test",
            kafka_bootstrap_servers="localhost:9092",
            kafka_topic="test-topic",
        )

        assert tracer._kafka_enabled
        mock_producer_class.assert_called_once()

    @patch(
        "autonomize_observer.tracing.workflow_tracer.CONFLUENT_KAFKA_AVAILABLE", True
    )
    @patch("autonomize_observer.tracing.workflow_tracer.ConfluentProducer")
    def test_kafka_setup_with_auth(self, mock_producer_class: MagicMock) -> None:
        """Test Kafka producer setup with SASL authentication."""
        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        mock_producer = MagicMock()
        mock_producer_class.return_value = mock_producer

        tracer = WorkflowTracer(
            "test",
            kafka_bootstrap_servers="localhost:9092",
            kafka_username="user",
            kafka_password="pass",
            kafka_security_protocol="SASL_SSL",
        )

        assert tracer._kafka_enabled
        # confluent-kafka receives config as positional dict argument
        call_args = mock_producer_class.call_args[0][0]
        assert call_args["security.protocol"] == "SASL_SSL"
        assert call_args["sasl.mechanism"] == "PLAIN"
        assert call_args["sasl.username"] == "user"
        assert call_args["sasl.password"] == "pass"

    @patch(
        "autonomize_observer.tracing.workflow_tracer.CONFLUENT_KAFKA_AVAILABLE", True
    )
    @patch("autonomize_observer.tracing.workflow_tracer.ConfluentProducer")
    def test_kafka_sends_events(self, mock_producer_class: MagicMock) -> None:
        """Test Kafka events are sent during workflow execution."""
        import json

        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        mock_producer = MagicMock()
        mock_producer.flush.return_value = 0
        mock_producer_class.return_value = mock_producer

        with WorkflowTracer(
            "test-workflow",
            kafka_bootstrap_servers="localhost:9092",
            kafka_topic="test-topic",
            order_id="123",
        ) as tracer:
            with tracer.step("step1") as step:
                step.set("key", "value")
            with tracer.step("step2"):
                pass

        # Check events sent via produce(): workflow_start, step_start, step_end (x2), workflow_end
        calls = mock_producer.produce.call_args_list
        assert len(calls) >= 5

        # Parse events from the calls (value is bytes)
        events = [json.loads(c[1]["value"].decode("utf-8")) for c in calls]

        # Check workflow_start
        assert events[0]["event_type"] == "workflow_start"

        # Check step events
        step_events = [e for e in events if "step" in e["event_type"]]
        assert len(step_events) == 4  # 2 starts, 2 ends

        # Check workflow_end
        assert events[-1]["event_type"] == "workflow_end"

        # Check flush was called (confluent-kafka has no close method)
        mock_producer.flush.assert_called()

    @patch(
        "autonomize_observer.tracing.workflow_tracer.CONFLUENT_KAFKA_AVAILABLE", True
    )
    @patch("autonomize_observer.tracing.workflow_tracer.ConfluentProducer")
    def test_kafka_setup_failure(self, mock_producer_class: MagicMock) -> None:
        """Test graceful handling of Kafka setup failure."""
        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        mock_producer_class.side_effect = Exception("Connection failed")

        tracer = WorkflowTracer(
            "test",
            kafka_bootstrap_servers="localhost:9092",
        )

        assert not tracer._kafka_enabled

    @patch(
        "autonomize_observer.tracing.workflow_tracer.CONFLUENT_KAFKA_AVAILABLE", True
    )
    @patch("autonomize_observer.tracing.workflow_tracer.ConfluentProducer")
    def test_kafka_send_failure(self, mock_producer_class: MagicMock) -> None:
        """Test graceful handling of Kafka produce failure."""
        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        mock_producer = MagicMock()
        mock_producer.produce.side_effect = Exception("Produce failed")
        mock_producer.flush.return_value = 0
        mock_producer_class.return_value = mock_producer

        # Should not raise
        with WorkflowTracer(
            "test",
            kafka_bootstrap_servers="localhost:9092",
        ) as tracer:
            with tracer.step("step1"):
                pass

    @patch(
        "autonomize_observer.tracing.workflow_tracer.CONFLUENT_KAFKA_AVAILABLE", True
    )
    @patch("autonomize_observer.tracing.workflow_tracer.ConfluentProducer")
    def test_kafka_flush_failure(self, mock_producer_class: MagicMock) -> None:
        """Test graceful handling of Kafka flush failure."""
        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        mock_producer = MagicMock()
        mock_producer.flush.side_effect = Exception("Flush failed")
        mock_producer_class.return_value = mock_producer

        # Should not raise
        with WorkflowTracer(
            "test",
            kafka_bootstrap_servers="localhost:9092",
        ) as tracer:
            pass

        assert tracer._kafka_producer is None

    @patch(
        "autonomize_observer.tracing.workflow_tracer.CONFLUENT_KAFKA_AVAILABLE", True
    )
    @patch("autonomize_observer.tracing.workflow_tracer.ConfluentProducer")
    def test_workflow_id_in_events(self, mock_producer_class: MagicMock) -> None:
        """Test workflow ID is included in all events."""
        import json

        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        mock_producer = MagicMock()
        mock_producer.flush.return_value = 0
        mock_producer_class.return_value = mock_producer

        with WorkflowTracer(
            "test",
            kafka_bootstrap_servers="localhost:9092",
        ) as tracer:
            workflow_id = tracer._workflow_id
            with tracer.step("step1"):
                pass

        # All events should have the same workflow_id
        for call in mock_producer.produce.call_args_list:
            value = json.loads(call[1]["value"].decode("utf-8"))
            assert value["workflow_id"] == workflow_id
            assert call[1]["key"].decode("utf-8") == workflow_id

    @patch(
        "autonomize_observer.tracing.workflow_tracer.CONFLUENT_KAFKA_AVAILABLE", True
    )
    @patch("autonomize_observer.tracing.workflow_tracer.ConfluentProducer")
    def test_kafka_with_plaintext_protocol(
        self, mock_producer_class: MagicMock
    ) -> None:
        """Test Kafka setup with PLAINTEXT protocol (no SASL auth)."""
        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        mock_producer = MagicMock()
        mock_producer_class.return_value = mock_producer

        tracer = WorkflowTracer(
            "test",
            kafka_bootstrap_servers="localhost:9092",
            kafka_security_protocol="PLAINTEXT",
        )

        assert tracer._kafka_enabled
        # Check config doesn't include SASL credentials when not provided
        call_args = mock_producer_class.call_args[0][0]
        assert "sasl.username" not in call_args
        assert "sasl.password" not in call_args


class TestWorkflowTracerRealWorld:
    """Real-world usage scenarios."""

    def test_order_processing_workflow(self) -> None:
        """Test order processing workflow scenario."""
        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        def validate_order(order_id: str) -> bool:
            time.sleep(0.005)
            return True

        def process_payment(amount: float) -> dict:
            time.sleep(0.005)
            return {"transaction_id": "tx-123", "status": "success"}

        def send_confirmation(order_id: str) -> None:
            time.sleep(0.005)

        with WorkflowTracer("process-order", order_id="order-456") as tracer:
            with tracer.step("validate") as step:
                is_valid = validate_order("order-456")
                step.set("is_valid", is_valid)

            with tracer.step("payment") as step:
                result = process_payment(99.99)
                step.set("transaction_id", result["transaction_id"])
                step.set("amount", 99.99)

            with tracer.step("confirmation"):
                send_confirmation("order-456")

            tracer.set("status", "completed")

        summary = tracer.get_summary()
        assert summary["step_count"] == 3
        assert summary["attributes"]["status"] == "completed"
        assert summary["steps"][0]["attributes"]["is_valid"] is True
        assert summary["steps"][1]["attributes"]["transaction_id"] == "tx-123"

    def test_data_pipeline_workflow(self) -> None:
        """Test data pipeline workflow scenario."""
        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        with WorkflowTracer(
            "etl-pipeline", source="postgres", target="warehouse"
        ) as tracer:
            with tracer.step("extract") as step:
                rows = 1000
                step.set("rows_extracted", rows)

            with tracer.step("transform") as step:
                transformed = 950
                step.set("rows_transformed", transformed)
                step.set("rows_filtered", 50)

            with tracer.step("load") as step:
                step.set("rows_loaded", 950)
                step.set("table", "fact_sales")

        assert len(tracer.steps) == 3
        assert tracer.steps[0].attributes["rows_extracted"] == 1000
        assert tracer.steps[2].attributes["table"] == "fact_sales"

    def test_nested_timing(self) -> None:
        """Test that step timing is accurate."""
        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        with WorkflowTracer("timing-test") as tracer:
            with tracer.step("fast"):
                time.sleep(0.01)

            with tracer.step("slow"):
                time.sleep(0.05)

        fast_step = tracer.steps[0]
        slow_step = tracer.steps[1]

        assert fast_step.duration_ms is not None
        assert slow_step.duration_ms is not None
        assert slow_step.duration_ms > fast_step.duration_ms
        assert slow_step.duration_ms >= 50  # At least 50ms


class TestWorkflowTracerMissingCoverage:
    """Tests for missing coverage paths."""

    @patch(
        "autonomize_observer.tracing.workflow_tracer.CONFLUENT_KAFKA_AVAILABLE", True
    )
    @patch("autonomize_observer.tracing.workflow_tracer.ConfluentProducer")
    def test_kafka_no_bootstrap_servers(self, mock_producer_class: MagicMock) -> None:
        """Test Kafka setup is skipped when no bootstrap servers."""
        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        # Pass empty bootstrap servers with Kafka available
        tracer = WorkflowTracer(
            name="test-workflow",
            kafka_bootstrap_servers="",  # Empty string - should early exit
            kafka_topic="test-topic",
        )

        # Should not have Kafka enabled
        assert tracer._kafka_producer is None
        assert not tracer._kafka_enabled
        # Producer should not have been called
        mock_producer_class.assert_not_called()

    @patch(
        "autonomize_observer.tracing.workflow_tracer.CONFLUENT_KAFKA_AVAILABLE", True
    )
    @patch("autonomize_observer.tracing.workflow_tracer.ConfluentProducer")
    def test_kafka_none_bootstrap_servers(self, mock_producer_class: MagicMock) -> None:
        """Test Kafka setup is skipped when bootstrap_servers is None."""
        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        # Pass None bootstrap servers with Kafka available
        tracer = WorkflowTracer(
            name="test-workflow",
            kafka_bootstrap_servers=None,
            kafka_topic="test-topic",
        )

        # Should not have Kafka enabled
        assert tracer._kafka_producer is None
        assert not tracer._kafka_enabled
        # Producer should not have been called
        mock_producer_class.assert_not_called()

    @patch(
        "autonomize_observer.tracing.workflow_tracer.CONFLUENT_KAFKA_AVAILABLE", True
    )
    @patch("autonomize_observer.tracing.workflow_tracer.ConfluentProducer")
    def test_kafka_flush_with_remaining_messages(
        self, mock_producer_class: MagicMock
    ) -> None:
        """Test Kafka flush when messages remain pending."""
        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        mock_producer = MagicMock()
        mock_producer.flush.return_value = 5  # 5 messages remaining
        mock_producer_class.return_value = mock_producer

        tracer = WorkflowTracer(
            name="test-workflow",
            kafka_bootstrap_servers="localhost:9092",
            kafka_topic="test-topic",
        )

        # Start and complete workflow
        with tracer as t:
            with t.step("test-step"):
                pass

        # Flush should have been called with remaining messages logged
        mock_producer.flush.assert_called_once()

    def test_duration_ms_before_end(self) -> None:
        """Test duration_ms returns None when workflow not ended."""
        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        tracer = WorkflowTracer(name="test-workflow")
        tracer._start_time = 100.0
        tracer._end_time = None  # Not ended yet

        # Should return None when not ended
        assert tracer.duration_ms is None

    def test_duration_ms_no_start(self) -> None:
        """Test duration_ms returns None when no start time."""
        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        tracer = WorkflowTracer(name="test-workflow")
        tracer._start_time = None  # Not started

        # Should return None
        assert tracer.duration_ms is None
